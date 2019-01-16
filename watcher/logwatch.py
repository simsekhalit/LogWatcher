#!/usr/bin/env python3
from ast import literal_eval
import asyncio
import ipaddress
import multiprocessing
import re
import sqlite3
import sys
import threading
import websockets
from util import databasePath, createNode, getNode
from syslog_rfc5424_parser.constants import SyslogSeverity, SyslogFacility


class LogWatch(multiprocessing.Process):
    """LogWatch class for watching log sources
    match -> (matchfield, operator, value, negated, caseinsens)
    matchfield -> one of (WHOLE, IP, SEVERITY, FACILITY, FIELD:range:sep, RE:regexp:field)
    """

    def __init__(self, lwID, name, pipe):
        super(LogWatch, self).__init__(daemon=True)
        self.lwID = lwID
        self.name = name
        self.pipe = pipe
        self.rules = createNode()
        self.logCV = threading.Condition()
        self.logs = []

    def run(self):
        self.load()
        threading.Thread(target=self.websocketServer, daemon=True).start()
        while True:
            try:
                data = self.pipe.recv()
                methodsTable = {"setMatch": self.setMatch, "combineMatch": self.combineMatch, "delMatch": self.delMatch}
                if not data:
                    return
                if data[0] == "log":
                    try:
                        print(self.rules, file=sys.stderr)
                        print(data, file=sys.stderr)
                        if self.applyFilters(self.rules, data[1].as_dict()):
                            self.addLog(str(data[1]))
                            self.saveLog(str(data[1]))

                    except BaseException as e:
                        print("Log Watch {} ({}): {} ({})".format(self.lwID, self.name, e, str(data[1])),
                              file=sys.stderr)

                elif data[0] in methodsTable:
                    methodsTable[data[0]](*data[1:])
                    self.saveRules()
                    self.pipe.send("0")
                else:
                    self.pipe.send("2")
                    raise Exception("Invalid LogWatch command")

            except KeyboardInterrupt:
                exit()
            except BaseException as e:
                print("Log Watch {} ({}): {}".format(self.lwID, self.name, e), file=sys.stderr)
                self.pipe.send("1")
                raise e

    def addLog(self, log):
        with self.logCV:
            self.logs.append(log)
            self.logCV.notify_all()

    def websocketServer(self):
        async def handler(websocket, path):
            print(path, file=sys.stderr)
            logIndex = 0

            while True:
                with self.logCV:
                    for i in range(logIndex, len(self.logs)):
                        try:
                            await websocket.send(self.logs[i])
                        except websockets.ConnectionClosed:
                            return
                    logIndex = len(self.logs)
                    self.logCV.wait()

        asyncio.set_event_loop(asyncio.new_event_loop())
        start_server = websockets.serve(handler, "localhost", 10000 + self.lwID)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    def applyFilters(self, rules, payload):
        if rules["value"] == "AND":
            return self.applyFilters(rules["left"], payload) and self.applyFilters(rules["right"], payload)
        elif rules["value"] == "OR":
            return self.applyFilters(rules["left"], payload) or self.applyFilters(rules["right"], payload)
        else:
            return self.applyRule(rules["value"], payload)

    def applyRule(self, rule, payload):
        if not rule:
            return False

        def applyMatch(operand):
            arg1 = operand
            arg2 = value

            if caseinsens and type(operand) == str:
                arg1 = arg1.lower()
                arg2 = arg2.lower()
            if operator == "EQ":
                ret = arg1 == arg2
            elif operator == "LT":
                ret = arg1 < arg2
            elif operator == "LE":
                ret = arg1 <= arg2
            elif operator == "GT":
                ret = arg1 > arg2
            elif operator == "GE":
                ret = arg1 >= arg2
            elif operator == "RE":
                ret = re.match(arg2, arg1) is not None
            else:
                raise Exception("Invalid operator {0} in rule {1}".format(operator, rule))
            if not negated:
                return ret
            else:
                return not ret

        matchfield = rule[0]
        operator = rule[1]
        value = rule[2]
        negated = rule[3]
        caseinsens = rule[4]

        if matchfield == "WHOLE":
            return applyMatch(payload["msg"])

        elif matchfield == "IP":
            if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', value) and \
                    re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', payload["hostname"]):
                value = ipaddress.IPv4Address(value)
                return applyMatch(ipaddress.IPv4Address(payload["hostname"]))
            elif type(value) == str and type(payload["hostname"] == str):
                return applyMatch(payload["hostname"])
            else:
                return False

        # emerg is the highest, debug is the lowest severity
        elif matchfield == "SEVERITY":
            if type(value) == str:
                value = 7 - SyslogSeverity[value.lower()]
            else:
                value = 7 - value
            severity = 7 - SyslogSeverity[payload["severity"]]
            return applyMatch(severity)

        # kern is the highest(0), unknown is the lowest (-1), if unknown is not present local7 is the lowest (23)
        elif matchfield == "FACILITY":
            if type(value) == str:
                value = 23 - SyslogFacility[value.lower()]
            else:
                value = 23 - value
            facility = 23 - SyslogFacility[payload["facility"]]
            if facility == 24:
                facility = -1
            if value == 24:
                value = -1
            return applyMatch(facility)

        elif matchfield.startswith("FIELD:"):
            fieldSplitList = matchfield.split(':')
            fieldStartRange = int(fieldSplitList[1][0])
            delimiter = fieldSplitList[2]
            if len(fieldSplitList[1]) != 1:
                fieldEndRange = int(fieldSplitList[1][2:]) + 1
                return applyMatch(delimiter.join(payload["msg"].split(delimiter)[fieldStartRange:fieldEndRange]))
            else:
                return applyMatch("".join(payload["msg"].split(delimiter)[fieldStartRange]))

        elif matchfield.startswith("RE:"):
            regexSplitList = matchfield.split(':')
            regexp = regexSplitList[1]
            field = regexSplitList[2]
            return applyMatch(re.sub(regexp, '\g<' + field + '>', payload["msg"]))

        else:
            raise Exception("Invalid matchfield {0} in rule {1}".format(matchfield, rule))

    # Set addressed Node to given "match" value.
    def setMatch(self, match, address):
        node = getNode(self.rules, address)
        if node["left"] is not None or node["right"] is not None:
            raise Exception("Cant set rule at LogWatch {} since address {} is not a leaf".format(self.lwID, address))
        node["value"] = match

    # Set the the addressed node to given "connector" value. ("AND" or "OR")
    # Left branch of connector will be the previous node's match value, right branch will be the new match value.
    def combineMatch(self, match, connector, address):
        node = getNode(self.rules, address)
        if node["left"] is not None or node["right"] is not None:
            raise Exception("Cant combine rule at LogWatch {} since address {} is not a leaf".format(self.lwID,
                                                                                                     address))
        node["left"] = createNode(node["value"])
        node["value"] = connector
        node["right"] = createNode(match)

    # Delete the node at given address, the sibling of the node will replace the parent logical operator.
    def delMatch(self, address: tuple):
        node = getNode(self.rules, address)
        if node["left"] is not None or node["right"] is not None:
            raise Exception("Cant delete rule at LogWatch {} since address {} is not a leaf".format(self.lwID,
                                                                                                    address))
        if address == ():
            node["value"] = ()
            node["left"] = None
            node["right"] = None
        else:
            parentNode = getNode(self.rules, address[:-1])
            if address[-1] == 0:
                survivorNode = parentNode["right"]
            else:
                survivorNode = parentNode["left"]

            parentNode["value"] = survivorNode["value"]
            parentNode["left"] = survivorNode["left"]
            parentNode["right"] = survivorNode["right"]

    def saveLog(self, log):
        with sqlite3.connect(databasePath) as conn:
            c = conn.cursor()
            c.execute("""insert into logs(wid, log) values(?, ?)""", (self.lwID, log))

    def saveRules(self):
        with sqlite3.connect(databasePath) as conn:
            c = conn.cursor()
            c.execute("""update rules set rules = ? where wid == ?""", (str(self.rules), self.lwID))

    # Load configuration from databasePath
    def load(self):
        with sqlite3.connect(databasePath) as conn:
            c = conn.cursor()
            self.rules = literal_eval(c.execute("""select rules from rules where wid == ?""",
                                                (self.lwID,)).fetchone()[0])
            self.logs = [log[0] for log in c.execute("""select log from logs where wid == ?""", (self.lwID,)).fetchall()]

#!/usr/bin/env python3
from ast import literal_eval
import ipaddress
import multiprocessing
import re
import selectors
import socket
import threading
import sqlite3
import sys
from util import Node, LogCollector, LogWatchTracker, ClientTracker
from syslog_rfc5424_parser.constants import SyslogSeverity, SyslogFacility


class LogWatchManager:
    def __init__(self):
        self.logWatchTrackers = []
        self.logWatchTrackersLock = threading.Lock()
        self.logSources = {}
        self.logSourcesLock = threading.Lock()
        self.clientTrackers = {}
        self.clientTrackersLock = threading.Lock()
        self.hostAddress = "localhost"
        self.udpPort = 5140
        self.tcpPort = 2470
        self.selector = selectors.DefaultSelector()

    def start(self):
        self.startLogCollector()
        self.startServer()
        self.run()

    def run(self):
        while True:
            events = self.selector.select()
            for key, _ in events:
                # collectorPipe
                if key.data == 0:
                    payload = key.fileobj.recv()
                    print(payload)
                    # with self.logWatchTrackersLock:
                    #     for lw in self.logWatchTrackers:
                    #         lw.pipe.send(("log", payload))
                # serverPipe: New client is connected.
                elif key.data == 1:
                    sock, addr = key.fileobj.accept()
                    thread = threading.Thread(target=self.clientHandler, args=(addr,), daemon=True)
                    with self.clientTrackersLock:
                        self.clientTrackers[addr] = ClientTracker(thread, sock)
                    thread.start()
                    print(addr, "connected.")
                # LogWatch: A message has come from a LogWatch object
                else:
                    log = key.fileobj.recv()
                    key.data.logs.append(log)
                    self.notify(key.data, log)

    def register(self, client, lwId):
        try:
            with self.logWatchTrackersLock:
                if lwId >= len(self.logWatchTrackers) or not self.logWatchTrackers[lwId]:
                    return "LogWatch {} does not exists.".format(lwId)
                lw = self.logWatchTrackers[lwId]
            with lw.lwLock:
                if client not in lw.registeredClients:
                    lw.registeredClients.add(client)
                    return "Registered to LogWatch {}".format(lwId)
                else:
                    return "Already registered to LogWatch {}".format(lwId)
        except Exception as e:
            return str(e)

    def unregister(self, client, lwId):
        try:
            with self.logWatchTrackersLock:
                if lwId >= len(self.logWatchTrackers) or not self.logWatchTrackers[lwId]:
                    return "LogWatch {} does not exists.".format(lwId)
                lw = self.logWatchTrackers[lwId]
            with lw.lwLock:
                if client in lw.registeredClients:
                    lw.registeredClients.remove(client)
                    return "Unregistered from LogWatch {}".format(lwId)
                else:
                    return "Already not registered to LogWatch {}".format(lwId)
        except Exception as e:
            return str(e)

    def notify(self, lw, log):
        with self.logWatchTrackersLock:
            for client in lw.registeredClients:
                with client.clientLock:
                    client.write("log\n" + log)

    def clientHandler(self, addr):
        def managerCreate():
            with self.logWatchTrackersLock:
                lwId = len(self.logWatchTrackers)
                parent_conn, child_conn = multiprocessing.Pipe()
                process = LogWatch(lwId, child_conn)
                lwTracker = LogWatchTracker(process, parent_conn)
                self.logWatchTrackers.append(lwTracker)
                self.selector.register(parent_conn, selectors.EVENT_READ, lwTracker)
            self.register(tracker, lwId)
            process.start()
            print("LogWatch {} created.".format(lwId))
            with tracker.clientLock:
                tracker.write("respond\n" + "LogWatch {} created.".format(lwId))

        def managerList():
            with self.logWatchTrackersLock:
                ret = []
                for i, lw in enumerate(self.logWatchTrackers):
                    r = " + " if (tracker in lw.registeredClients) else "   "
                    ret.append("LogWatch {}".format(i) + r + str(len(lw.logs)))
            with tracker.clientLock:
                if ret:
                    tracker.write("respond\n" + "\n".join(ret))
                else:
                    tracker.write("respond\n" + "-")

        def managerRegister():
            try:
                ret = self.register(tracker, int(data[1]))
            except Exception as e:
                ret = str(e)
            with tracker.clientLock:
                tracker.write("respond\n" + ret)

        def managerUnregister():
            try:
                ret = self.unregister(tracker, int(data[1]))
            except Exception as e:
                ret = str(e)
            with tracker.clientLock:
                tracker.write("respond\n" + ret)

        def lwPrintLogs():
            try:
                lwId = int(data[1])
                with self.logWatchTrackersLock:
                    if lwId >= len(self.logWatchTrackers):
                        tracker.write("respond\n" + "LogWatch {} does not exists.".format(lwId))
                        return
                    logs = self.logWatchTrackers[lwId].logs
                    if logs:
                        ret = "\n".join(self.logWatchTrackers[lwId].logs)
                    else:
                        ret = "-"
            except Exception as e:
                ret = str(e)
            tracker.write("respond\n" + ret)

        def lwPrintRules():
            try:
                lwId = int(data[1])
                with self.logWatchTrackersLock:
                    if lwId >= len(self.logWatchTrackers):
                        tracker.write("respond\n" + "LogWatch {} does not exists.".format(lwId))
                        return
                with sqlite3.connect("LogWatch.db") as conn:
                    c = conn.cursor()
                    dump = c.execute("""select * from LogWatch{};""".format(lwId)).fetchall()
                if dump:
                    ret = "\n".join(map(str, dump))
                else:
                    ret = "-"
            except Exception as e:
                ret = str(e)
            tracker.write("respond\n" + ret)

        def lwSetMatch():
            try:
                lwId = int(data[1])
                match = literal_eval(data[2])
                address = literal_eval(data[3])
                with self.logWatchTrackersLock:
                    if lwId >= len(self.logWatchTrackers) or not self.logWatchTrackers[lwId]:
                        ret = "LogWatch {} does not exists.".format(lwId)
                    else:
                        lw = self.logWatchTrackers[lwId]
                        with lw.lwLock:
                            lw.pipe.send(("setMatch", match, address))
                            ret = "Request is sent."
            except Exception as e:
                ret = str(e)
            tracker.write("respond\n" + ret)

        def lwCombineMatch():
            try:
                lwId = int(data[1])
                match = literal_eval(data[2])
                connector = data[3]
                address = literal_eval(data[4])
                with self.logWatchTrackersLock:
                    if lwId >= len(self.logWatchTrackers) or not self.logWatchTrackers[lwId]:
                        ret = "LogWatch {} does not exists.".format(lwId)
                    else:
                        lw = self.logWatchTrackers[lwId]
                        with lw.lwLock:
                            lw.pipe.send(("combineMatch", match, connector, address))
                            ret = "Request is sent."
            except Exception as e:
                ret = str(e)
            tracker.write("respond\n" + ret)

        def lwDelMatch():
            try:
                lwId = int(data[1])
                address = literal_eval(data[2])
                with self.logWatchTrackersLock:
                    if lwId >= len(self.logWatchTrackers) or not self.logWatchTrackers[lwId]:
                        ret = "LogWatch {} does not exists.".format(lwId)
                    else:
                        lw = self.logWatchTrackers[lwId]
                        with lw.lwLock:
                            lw.pipe.send(("delMatch", address))
                            ret = "Request is sent."
            except Exception as e:
                ret = str(e)
            tracker.write("respond\n" + ret)

        def lwSave():
            try:
                lwId = int(data[1])
                with self.logWatchTrackersLock:
                    if lwId >= len(self.logWatchTrackers) or not self.logWatchTrackers[lwId]:
                        ret = "LogWatch {} does not exists.".format(lwId)
                    else:
                        lw = self.logWatchTrackers[lwId]
                        with lw.lwLock:
                            lw.pipe.send(("save",))
                            ret = "Request is sent."
            except Exception as e:
                ret = str(e)
            tracker.write("respond\n" + ret)

        def lwLoad():
            try:
                lwId = int(data[1])
                with self.logWatchTrackersLock:
                    if lwId >= len(self.logWatchTrackers) or not self.logWatchTrackers[lwId]:
                        ret = "LogWatch {} does not exists.".format(lwId)
                    else:
                        lw = self.logWatchTrackers[lwId]
                        with lw.lwLock:
                            lw.pipe.send(("load",))
                            ret = "Request is sent."
            except Exception as e:
                ret = str(e)
            tracker.write("respond\n" + ret)

        def terminate():
            with self.logWatchTrackersLock:
                for lw in self.logWatchTrackers:
                    if tracker in lw.registeredClients:
                        lw.registeredClients.remove(tracker)
            with self.clientTrackersLock:
                del self.clientTrackers[addr]
            print(addr, "disconnected.")
            exit(0)

        tracker = self.clientTrackers[addr]
        managerMethods = {"create": managerCreate, "list": managerList, "register": managerRegister,
                          "unregister": managerUnregister}
        lwMethods = {"printLogs": lwPrintLogs, "printRules": lwPrintRules, "setMatch": lwSetMatch, "combineMatch": lwCombineMatch, "delMatch": lwDelMatch, "save": lwSave,
                     "loadJSON": lwLoad}
        while True:
            data = tracker.read().split("\n")
            if not data[0]:
                terminate()
            elif data[0] in managerMethods:
                managerMethods[data[0]]()
            elif data[0] in lwMethods:
                lwMethods[data[0]]()
            else:
                tracker.write("respond\n" + "Invalid command")

    def startLogCollector(self):
        collectorPipe, externalPipe = multiprocessing.Pipe()
        collector = LogCollector(self.hostAddress, self.udpPort, externalPipe)
        collector.start()
        self.selector.register(collectorPipe, selectors.EVENT_READ, 0)

    def startServer(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.hostAddress, self.tcpPort))
        sock.listen(10)
        self.selector.register(sock, selectors.EVENT_READ, 1)


class LogWatch(multiprocessing.Process):
    """LogWatch class for watching log sources
    match -> (matchfield, operator, value, negated, caseinsens)
    matchfield -> one of (WHOLE, IP, SEVERITY, FACILITY, FIELD:range:sep, RE:regexp:field)
    """

    def __init__(self, lwId, pipe):
        super(LogWatch, self).__init__()
        self.pipe = pipe
        self.rules = Node()
        self.lwId = lwId
        self.database = "LogWatch.db"

    def run(self):
        data = self.pipe.recv()
        while data:
            if data[0] == "setMatch":
                self.setMatch(data[1], data[2])
            elif data[0] == "combineMatch":
                self.combineMatch(data[1], data[2], data[3])
            elif data[0] == "delMatch":
                self.delMatch(data[1])
            elif data[0] == "save":
                self.save()
            elif data[0] == "load":
                self.load()
            elif data[0] == "log":
                if self.applyFilters(self.rules, data[1].as_dict()):
                    self.pipe.send(str(data[1]))
            else:
                pass
            data = self.pipe.recv()
        self.pipe.close()

    def applyFilters(self, rules, payload):
        if rules.value == "AND":
            return self.applyFilters(rules.left, payload) and self.applyFilters(rules.right, payload)
        elif rules.value == "OR":
            return self.applyFilters(rules.left, payload) or self.applyFilters(rules.right, payload)
        else:
            return self.applyRule(rules.value, payload)

    def applyRule(self, rule, payload):
        class InvalidMatchfield(Exception):
            pass

        class InvalidOperator(Exception):
            pass

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
                raise InvalidOperator("Invalid operator {0} in rule {1}".format(operator, rule))
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
            if re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', value) and re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
                                                                                  payload["hostname"]):
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
            raise InvalidMatchfield("Invalid matchfield {0} in rule {1}".format(matchfield, rule))

    # Set addressed Node to given "match" value.
    def setMatch(self, match, address=()):
        self.rules.getNode(address).value = match

    # Set the the addressed node to given "connector" value. ("AND" or "OR")
    # Left branch of connector will be the previous node's match value, right branch will be the new match value.
    def combineMatch(self, match, connector, address=()):
        node = self.rules.getNode(address)
        temp = node.value
        node.value = connector
        node.left = Node(temp)
        node.right = Node(match)

    # Delete the node at given address, the sibling of the node will replace the parent logical operator.
    def delMatch(self, address=()):
        # Deleting the rules
        if address == ():
            if self.rules.left is None and self.rules.right is None:
                self.rules.value = None
                self.rules.left = None
                self.rules.right = None
        else:
            parentNode = self.rules.getNode(address[:-1])
            if address[-1] == 0:
                survivorNode = parentNode.right
            elif address[-1] == 1:
                survivorNode = parentNode.left
            else:
                print("Invalid address:", address, file=sys.stderr)
                return
            parentNode.value = survivorNode.value
            parentNode.left = survivorNode.left
            parentNode.right = survivorNode.right

    # Save current configuration to database
    def save(self):
        dump = self.rules.dump()
        with sqlite3.connect(self.database) as conn:
            c = conn.cursor()
            try:
                c.execute("""drop table LogWatch{}""".format(0))
            except:
                pass
            try:
                a = c.execute("""create table LogWatch{}(path TEXT, rule TEXT)""".format(self.lwId))
            except:
                pass
            for row in dump:
                c.execute("""insert into LogWatch{} (path, rule) values (\"{}\", \"{}\")""".format(0, row[0], row[1]))

    # Load configuration from database
    def load(self):
        with sqlite3.connect(self.database) as conn:
            c = conn.cursor()
            dump = c.execute("""select * from LogWatch{};""".format(self.lwId)).fetchall()
        self.rules.load(dump)


if __name__ == "__main__":
    lwm = LogWatchManager()
    lwm.start()

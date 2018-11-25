#!/usr/bin/env python3
import ipaddress
import json
import re
import parser
from util import *


def main():

    logFile = "samples/sample.log"
    watcher = LogWatch()


class LogWatch:
    """LogWatch class for watching log sources
    match -> (matchfield, operator, value, negated, caseinsens)
    matchfield -> one of (WHOLE, IP, SEVERITY, FACILITY, FIELD:range:sep, RE:regexp:field)
    """
    def __init__(self, filename=None):
        self.rules = Node()
        self.logFile = filename
        self.logSource = None
        self.filteredLogs = []

    def run(self):
        self.logSource = open(self.logFile, "rb")
        logParser = parser.Parser()
        line = self.logSource.readline()
        while line:
            payload = logParser.parse(line.decode())
            if self.applyFilters(self.rules, payload):
                self.filteredLogs.append(line)
            line = self.logSource.readline()
        self.logSource.close()

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
            arg1 = value
            arg2 = operand

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
                ret = re.match(arg1, arg2) is not None
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
            return applyMatch(payload["message"])
        elif matchfield == "IP":
            if re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', value):
                payload["hostname"] = ipaddress.IPv4Address(payload["hostname"])
                value = ipaddress.IPv4Address(value)
            return applyMatch(payload["hostname"])
        elif matchfield == "SEVERITY":
            # TODO: Apply the match according to severity level
            pass
        elif matchfield == "FACILITY":
            # TODO: Apply the match according to facility type
            pass
        elif matchfield.startswith("FIELD:"):
            # TODO: Appy the match according to field
            pass
        elif matchfield.startswith("RE:"):
            # TODO: Apply the match according to REGEX
            pass
        else:
            raise InvalidMatchfield("Invalid matchfield {0} in rule {1}".format(matchfield, rule))

    # Set addressed Node to given "match" value.
    def setMatch(self, match, address = ()):
        self.rules.getNode(address).value = match

    # Set the the addressed node to given "connector" value. ("AND" or "OR")
    # Left branch of connector will be the previous node's match value, right branch will be the new match value.
    def combineMatch(self, match, connector, address = ()):
        node = self.rules.getNode(address)
        temp = node.value
        node.value = connector
        node.left = Node(temp)
        node.right = Node(match)

    # Delete the node at given address, the sibling of the node will replace the parent logical operator.
    def delMatch(self, address = ()):
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
                raise AddressNotFoundError("Invalid address:", address)
            parentNode.value = survivorNode.value
            parentNode.left = survivorNode.left
            parentNode.right = survivorNode.right

    # Save current configuration as JSON to a file
    # Configuration -> log source path + rule tree
    def save(self, name):
        if not name.endswith(".json"):
            name += ".json"
        data = {"logFile": self.logFile, "rules": self.rules}
        with open(name, "w") as writeFile:
            json.dump(data, writeFile, indent = 4)

    # Load configuration from JSON file
    def load(self, name):
        if not name.endswith(".json"):
            name += ".json"
        with open(name, "r") as readFile:
            data = json.load(readFile)
        self.logFile = data["logFile"]
        self.rules.load(data["rules"])


if __name__ == '__main__':
    main()

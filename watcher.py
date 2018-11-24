#!/usr/bin/env python3

from util import *
import json


def main():

    logFile = "/var/log/syslog"
    watcher = LogWatch()


class LogWatch:
    """LogWatch class for watching log sources
    match -> (matchfield, operator, value, negated, caseinsens)
    matchfield -> one of (WHOLE, IP, SEVERITY, FACILITY, FIELD:range:sep, RE:regexp:field)
    """
    # TODO: Open file which has name of filename.
    def __init__(self, filename=None):
        self.rules = Node()
        self.logFile = filename

    # TODO: Initiate the process.
    def run(self):
        pass

    # TODO: Receive and process log data from source then return.
    def readLog(self):
        pass

    # TODO: Parse given log according to RFC 5424.
    def parseLog(self):
        pass

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
            json.dump(data, writeFile, indent = 2)

    # Load configuration from JSON file
    def load(self, name):
        if not name.endswith(".json"):
            name += ".json"
        with open(name, "r") as readFile:
            data = json.load(readFile)
        self.logFile = data["logFile"]
        self.rules = data["rules"]


if __name__ == '__main__':
    main()

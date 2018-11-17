#!/usr/bin/env python3

from util import Node


def main():
    root = Node(5)
    print(root.value)


class LogWatch:
    """LogWatch class for watching log sources
    match -> (matchfield, operator, value, negated, caseinsens)
    matchfield -> one of (WHOLE, IP, SEVERITY, FACILITY, FIELD:range:sep, RE:regexp:field)
    """
    # TODO: Open file which has name of filename.
    def __init__(self, filename):
        pass

    # TODO: Initiate the process.
    def run(self):
        pass

    # TODO: Receive and process log data from source then return.
    def readLog(self):
        pass

    # TODO: Parse given log according to RFC 5424.
    def parseLog(self):
        pass

    # TODO: Replace addressed Node with the given one.
    def setMatch(self, match, address = ()):
        pass

    # TODO: Replace the the addressed node in the tree with a new node with given logical connector ("AND" or "OR").
    def combineMatch(self, match, connector, address):
        pass

    # TODO: Delete the node in the given address.
    def delMatch(self, address):
        pass

    # TODO: Save the configuration to persistent storage.
    def save(self, name):
        pass

    # TODO: Load the configuration from persistent storage.
    def load(self, name):
        pass


if __name__ == '__main__':
    main()

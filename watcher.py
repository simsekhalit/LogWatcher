#!/usr/bin/env python3

from util import Node
import json
import os


def main():

    log_file = "/var/log/syslog"
    instance = LogWatch(log_file)
    instance.setMatch(8)
    instance.combineMatch(6, "AND", ())
    print("Log source path of the object:", instance.log_source_path)
    print("Rule tree of the object:\n", json.dumps(instance.rule_tree, indent = 2))


class LogWatch:
    """LogWatch class for watching log sources
    match -> (matchfield, operator, value, negated, caseinsens)
    matchfield -> one of (WHOLE, IP, SEVERITY, FACILITY, FIELD:range:sep, RE:regexp:field)
    """
    # TODO: Open file which has name of filename.
    def __init__(self, filename):
        self.rule_tree = None
        self.log_source_path = filename

    # TODO: Initiate the process.
    def run(self):
        pass

    # TODO: Receive and process log data from source then return.
    def readLog(self):
        pass

    # TODO: Parse given log according to RFC 5424.
    def parseLog(self):
        pass

    # Replace addressed Node with the given one.
    def setMatch(self, match, address = ()):
        if address == ():
            self.rule_tree = Node(match)
        else:
            node = self.rule_tree.getNode(address)
            node.value = match

    # Replace the the addressed node in the tree with a new node with given logical connector ("AND" or "OR").
    # Left branch of connector will be the previous node value, right branch will be the new match.
    def combineMatch(self, match, connector, address):
        node = self.rule_tree.getNode(address)
        temp = node.value
        node.value = connector
        node.left = Node(temp)
        node.right = Node(match)

    # Delete the node at given address, the sibling of the node will replace the parent logical operator.
    def delMatch(self, address):
        if address == ():  # deleting the rule_tree
            self.rule_tree = None
        else:
            parent_node = self.rule_tree.getNode(address[:-1])
            if address[-1] == 0:
                parent_node.value = parent_node.right.value
            else:
                parent_node.value = parent_node.left.value
            parent_node.right = None
            parent_node.left = None

    # Save current configuration as JSON to a file
    # Configuration -> log source path + rule tree
    def save(self, name):
        with open(name + ".json", "w") as write_file:
            data = {"log_source_path": self.log_source_path, "rule_tree": self.rule_tree}
            json.dump(data, write_file, indent = 2)

    # Load configuration from persistent storage - JSON file
    def load(self, name):
        with open(name + ".json", "r") as read_file:
            data = json.load(read_file)
            self.log_source_path = data["log_source_path"]
            self.rule_tree.fromJson(data["rule_tree"])


if __name__ == '__main__':
    main()

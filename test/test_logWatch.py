#!/usr/bin/env python3
import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import watcher
from util import Node


class TestLogWatch(unittest.TestCase):
    def test_combineMatch(self):
        # Case 1 - Single element rule tree
        testWatcher = watcher.LogWatch()
        testWatcher.rules.value = "OLD_MATCH"
        testWatcher.combineMatch("NEW_MATCH", "AND")
        self.assertDictEqual({"value": "AND", "left": {"value": "OLD_MATCH", "left": None, "right": None},
                              "right": {"value": "NEW_MATCH", "left": None, "right": None}}, testWatcher.rules)

        # Case 2 - Leaf of rule tree
        testWatcher.rules.value = "AND"
        testWatcher.rules.left = Node("OLD_MATCH")
        testWatcher.rules.right = Node("SOME_MATCH")
        testWatcher.combineMatch("NEW_MATCH", "OR", (0,))
        self.assertDictEqual({"value": "AND",
                              "left": {"value": "OR", "left": {"value": "OLD_MATCH", "left": None, "right": None},
                                       "right": {"value": "NEW_MATCH", "left": None, "right": None}},
                              "right": {"value": "SOME_MATCH", "left": None, "right": None}}, testWatcher.rules)

    def test_delMatch(self):
        # Case 1 - Single element of rule tree
        testWatcher = watcher.LogWatch()
        testWatcher.rules.value = "MATCH"
        testWatcher.delMatch()
        self.assertDictEqual({"value": None, "left": None, "right": None}, testWatcher.rules)

        # Case 2 - Internal element of rule tree
        testWatcher = watcher.LogWatch()
        testWatcher.rules.value = "AND"
        testWatcher.rules.left = Node("LEFT_MATCH")
        testWatcher.rules.right = Node("RIGHT_MATCH")
        testWatcher.delMatch((0,))
        self.assertDictEqual({"value": "RIGHT_MATCH", "left": None, "right": None}, testWatcher.rules)

    def test_setMatch(self):
        # Case 1 - Empty rules
        testWatcher = watcher.LogWatch()
        testWatcher.setMatch("MATCH")
        self.assertDictEqual({"value": "MATCH", "left": None, "right": None}, testWatcher.rules)

        # Case 2 - Single element of rule tree
        testWatcher = watcher.LogWatch()
        testWatcher.rules.value = "OLD_MATCH"
        testWatcher.setMatch("NEW_MATCH")
        self.assertDictEqual({"value": "NEW_MATCH", "left": None, "right": None}, testWatcher.rules)

        # Case 3 - Leaf of rule tree
        testWatcher = watcher.LogWatch()
        testWatcher.rules.value = "AND"
        testWatcher.rules.left = Node("OLD_LEFT_MATCH")
        testWatcher.rules.right = Node("OLD_RIGHT_MATCH")
        testWatcher.setMatch("NEW_LEFT_MATCH", (0,))
        testWatcher.setMatch("NEW_RIGHT_MATCH", (1,))
        self.assertDictEqual({"value": "AND", "left": {"value": "NEW_LEFT_MATCH", "left": None, "right": None},
                              "right": {"value": "NEW_RIGHT_MATCH", "left": None, "right": None}},
                             testWatcher.rules)


def main():
    unittest.main(verbosity=3)


if __name__ == '__main__':
    main()

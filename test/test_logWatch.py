#!/usr/bin/env python3
import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import watcher
from util import Node


class TestLogWatch(unittest.TestCase):
    def test_applyRule(self):
        watcherInstance = watcher.LogWatch()

        # Case 1 - matchfield : WHOLE
        payload = {'timestamp': 1542661800, 'hostname': 'john-pc', 'appname': 'gnome-shell', 'pid': '1758',
                              'msg': 'NOTE: Not using GLX TFP!'}
        self.assertTrue(watcherInstance.applyRule(("WHOLE", "EQ", "NOTE: Not using GLX TFP!", False, False), payload))
        self.assertTrue(watcherInstance.applyRule(("WHOLE", "EQ", "NOTE: Not using GLX TFP!", False, True), payload))
        self.assertTrue(watcherInstance.applyRule(("WHOLE", "EQ", "note: not using glx tfp!", False, True), payload))
        self.assertFalse(watcherInstance.applyRule(("WHOLE", "EQ", "note: not using glx tfp!", False, False), payload))
        self.assertTrue(watcherInstance.applyRule(("WHOLE", "EQ", "note: not using glx tfp!", True, False), payload))
        self.assertTrue(watcherInstance.applyRule(("WHOLE", "EQ", "note: not using glx tfp!", True, False), payload))

        self.assertTrue(watcherInstance.applyRule(("WHOLE", "RE", ".*GLX.*", False, False), payload))
        self.assertTrue(watcherInstance.applyRule(("WHOLE", "RE", ".*GLX.*", False, True), payload))
        self.assertFalse(watcherInstance.applyRule(("WHOLE", "RE", ".*GLX.*", True, False), payload))
        self.assertFalse(watcherInstance.applyRule(("WHOLE", "RE", ".*GLX.*", True, True), payload))
        self.assertTrue(watcherInstance.applyRule(("WHOLE", "RE", ".*tfp!", False, True), payload))
        self.assertFalse(watcherInstance.applyRule(("WHOLE", "RE", ".*tfp!", False, False), payload))

        # Case 2 - matchfield : IP
        self.assertTrue(watcherInstance.applyRule(("IP", "EQ", "john-pc", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "EQ", "John-Pc", False, False), payload))
        self.assertTrue(watcherInstance.applyRule(("IP", "EQ", "John-Pc", False, True), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "EQ", "john-pc", True, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "EQ", "John-Pc", True, True), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "EQ", "176.240.43.210", False, False), payload))

        self.assertTrue(watcherInstance.applyRule(("IP", "RE", ".*john-pc.*", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "RE", ".*John-Pc.*", False, False), payload))
        self.assertTrue(watcherInstance.applyRule(("IP", "RE", ".*John-Pc.*", False, True), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "RE", ".*john-pc.*", True, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "RE", ".*John-Pc.*", True, True), payload))

        payload = {'timestamp': 1542661800, 'hostname': "176.240.43.210", 'appname': 'gnome-shell', 'pid': '1758',
                    'msg': 'NOTE: Not using GLX TFP!'}
        self.assertTrue(watcherInstance.applyRule(("IP", "EQ", "176.240.43.210", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "EQ", "192.168.14.7", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "EQ", "176.240.43.210", True, False), payload))

        self.assertTrue(watcherInstance.applyRule(("IP", "LT", "157.51.14.41", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "LT", "192.168.14.7", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "LT", "157.51.14.41", True, False), payload))

        self.assertTrue(watcherInstance.applyRule(("IP", "GT", "192.168.14.7", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "GT", "157.51.14.41", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "GT", "192.168.14.7", True, False), payload))

        self.assertTrue(watcherInstance.applyRule(("IP", "LE", "176.240.43.210", False, False), payload))
        self.assertTrue(watcherInstance.applyRule(("IP", "LE", "157.51.14.41", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "LE", "192.168.14.7", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "LE", "176.240.43.210", True, False), payload))

        self.assertTrue(watcherInstance.applyRule(("IP", "GE", "176.240.43.210", False, False), payload))
        self.assertTrue(watcherInstance.applyRule(("IP", "GE", "192.168.14.7", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "GE", "157.51.14.41", False, False), payload))
        self.assertFalse(watcherInstance.applyRule(("IP", "GE", "176.240.43.210", True, False), payload))

        # TODO: Add test cases for other matchfield cases

    def test_combineMatch(self):
        # Case 1 - Single element rule tree
        watcherInstance = watcher.LogWatch()
        watcherInstance.rules.value = "OLD_MATCH"
        watcherInstance.combineMatch("NEW_MATCH", "AND")
        self.assertDictEqual({"value": "AND", "left": {"value": "OLD_MATCH", "left": None, "right": None},
                              "right": {"value": "NEW_MATCH", "left": None, "right": None}}, watcherInstance.rules)

        # Case 2 - Leaf of rule tree
        watcherInstance.rules.value = "AND"
        watcherInstance.rules.left = Node("OLD_MATCH")
        watcherInstance.rules.right = Node("SOME_MATCH")
        watcherInstance.combineMatch("NEW_MATCH", "OR", (0,))
        self.assertDictEqual({"value": "AND",
                              "left": {"value": "OR", "left": {"value": "OLD_MATCH", "left": None, "right": None},
                                       "right": {"value": "NEW_MATCH", "left": None, "right": None}},
                              "right": {"value": "SOME_MATCH", "left": None, "right": None}}, watcherInstance.rules)

    def test_delMatch(self):
        # Case 1 - Single element of rule tree
        watcherInstance = watcher.LogWatch()
        watcherInstance.rules.value = "MATCH"
        watcherInstance.delMatch()
        self.assertDictEqual({"value": None, "left": None, "right": None}, watcherInstance.rules)

        # Case 2 - Internal element of rule tree
        watcherInstance = watcher.LogWatch()
        watcherInstance.rules.value = "AND"
        watcherInstance.rules.left = Node("LEFT_MATCH")
        watcherInstance.rules.right = Node("RIGHT_MATCH")
        watcherInstance.delMatch((0,))
        self.assertDictEqual({"value": "RIGHT_MATCH", "left": None, "right": None}, watcherInstance.rules)

    def test_setMatch(self):
        # Case 1 - Empty rules
        watcherInstance = watcher.LogWatch()
        watcherInstance.setMatch("MATCH")
        self.assertDictEqual({"value": "MATCH", "left": None, "right": None}, watcherInstance.rules)

        # Case 2 - Single element of rule tree
        watcherInstance = watcher.LogWatch()
        watcherInstance.rules.value = "OLD_MATCH"
        watcherInstance.setMatch("NEW_MATCH")
        self.assertDictEqual({"value": "NEW_MATCH", "left": None, "right": None}, watcherInstance.rules)

        # Case 3 - Leaf of rule tree
        watcherInstance = watcher.LogWatch()
        watcherInstance.rules.value = "AND"
        watcherInstance.rules.left = Node("OLD_LEFT_MATCH")
        watcherInstance.rules.right = Node("OLD_RIGHT_MATCH")
        watcherInstance.setMatch("NEW_LEFT_MATCH", (0,))
        watcherInstance.setMatch("NEW_RIGHT_MATCH", (1,))
        self.assertDictEqual({"value": "AND", "left": {"value": "NEW_LEFT_MATCH", "left": None, "right": None},
                              "right": {"value": "NEW_RIGHT_MATCH", "left": None, "right": None}},
                             watcherInstance.rules)

    def test_save(self):
        watcherInstance = watcher.LogWatch("TEST_LOG_FILE")
        watcherInstance.rules = Node("()")
        watcherInstance.rules.left = Node("(0)")
        watcherInstance.rules.right = Node("(1)")
        watcherInstance.rules.left.left = Node("(0, 0)")
        watcherInstance.rules.left.right = Node("(0, 1)")
        watcherInstance.rules.right.left = Node("(1, 0)")
        watcherInstance.rules.right.right = Node("(1, 1)")
        watcherInstance.save("test_sample.json")

        with open("samples/test_sample.json") as f:
            expected = f.read()
        with open("test_sample.json") as f:
            actual = f.read()
        self.assertEqual(expected, actual)
        os.remove("test_sample.json")

    def test_load(self):
        watcherInstance = watcher.LogWatch("TEST_LOG_FILE")
        watcherInstance.rules = Node("()")
        watcherInstance.rules.left = Node("(0)")
        watcherInstance.rules.right = Node("(1)")
        watcherInstance.rules.left.left = Node("(0, 0)")
        watcherInstance.rules.left.right = Node("(0, 1)")
        watcherInstance.rules.right.left = Node("(1, 0)")
        watcherInstance.rules.right.right = Node("(1, 1)")

        watcherInstance2 = watcher.LogWatch()
        watcherInstance2.load("samples/test_sample.json")
        self.assertEqual(watcherInstance.rules, watcherInstance2.rules)


def main():
    unittest.main(verbosity=3)


if __name__ == '__main__':
    main()

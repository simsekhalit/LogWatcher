#!/usr/bin/env python3
import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from util import createNode, getNode


class TestNode(unittest.TestCase):

    def test_createNode(self):
        node1 = createNode("val1", {"left"}, {"right"})
        test1 = {'value': 'val1', 'left': {'left'}, 'right': {'right'}}
        self.assertDictEqual(node1, test1)
        node2 = createNode("val2", test1, test1)
        test2 = {'value': 'val2', 'left': {'value': 'val1', 'left': {'left'}, 'right': {'right'}},
                 'right': {'value': 'val1', 'left': {'left'}, 'right': {'right'}}}
        self.assertDictEqual(node2, test2)

    def test_getNode(self):
        rule = {'value': 'val2', 'left': {'value': 'val1', 'left': {'left'}, 'right': {'right'}},
                                'right': {'value': 'val1', 'left': {'left'}, 'right': {'right'}}}
        self.assertEqual(rule, getNode(rule, ()))
        self.assertEqual(rule['left'], getNode(rule, (0,)))
        self.assertEqual(rule['right'], getNode(rule, (1,)))
        self.assertEqual(rule['left']['left'], getNode(rule, (0, 0)))
        self.assertEqual(rule['left']['right'], getNode(rule, (0, 1)))
        self.assertEqual(rule['right']['left'], getNode(rule, (1, 0)))
        self.assertEqual(rule['right']['right'], getNode(rule, (1, 1)))





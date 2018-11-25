#!/usr/bin/env python3
import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from parser import Parser


class TestParser(unittest.TestCase):
    def test_parse(self):
        line = "Nov 20 00:10:00 john-pc gnome-shell[1758]: NOTE: Not using GLX TFP!"
        parserInstance = Parser()
        payload = parserInstance.parse(line)
        self.assertDictEqual({'timestamp': 1542661800, 'hostname': 'john-pc', 'appname': 'gnome-shell', 'pid': '1758',
                              'message': 'NOTE: Not using GLX TFP!'}, payload)


def main():
    unittest.main(verbosity=3)


if __name__ == '__main__':
    main()

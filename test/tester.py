#!/usr/bin/env python3
import os
import sys
import test_logWatch
import unittest
testdir = os.path.dirname(__file__)
srcdir = '../'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))
import watcher


def main():
    # Unit tests
    suite = unittest.TestLoader().loadTestsFromModule(test_logWatch)
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    main()

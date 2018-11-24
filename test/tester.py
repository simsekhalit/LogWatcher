#!/usr/bin/env python3
import json
import os
import sys
import test_logWatch
import test_parser
import unittest
testdir = os.path.dirname(__file__)
srcdir = '../'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))
import watcher
import util


def main():
    # Unit tests
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_logWatch))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_parser))
    unittest.TextTestRunner(verbosity=3).run(suite)

    # Integration Tests
    logFile = "./sample.log"
    watcherInstance = watcher.LogWatch(logFile)
    watcherInstance.setMatch(("WHOLE", "EQ", "NOTE: Not using GLX TFP!", False, True))
    watcherInstance.combineMatch(("WHOLE", "RE", ".*Anacron.*", False, False), "OR")
    watcherInstance.combineMatch(("WHOLE", "RE", ".*anacron.*", False, False), "OR", (1,))
    watcherInstance.combineMatch(("WHOLE", "RE", ".*ERROR.*", False, True), "OR", (0,))
    watcherInstance.combineMatch(("WHOLE", "RE", ".*STREAM.*", False, True), "AND", (0, 1))
    watcherInstance.combineMatch(("WHOLE", "RE", ".*dhcp.*", False, True), "OR", (0, 0))
    watcherInstance.combineMatch(("WHOLE", "RE", ".*address.*", False, True), "AND", (0, 0, 1))
    watcherInstance.combineMatch(("WHOLE", "RE", ".*rfkill.*", False, True), "OR", (0, 0, 0))

    with open("sample-conf.json", "rb") as f:
        sampleRules = util.Node().load(json.load(f)["rules"])
    assert sampleRules == watcherInstance.rules
    watcherInstance.run()
    with open("sample-result") as f:
        result = f.read()
    assert str(watcherInstance.filteredLogs) == result
    print("All tests are completed successfully.")


if __name__ == '__main__':
    main()

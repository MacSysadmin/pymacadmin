#!/usr/bin/python2.5
#
# Use 2.5 so we can import objc & Foundation in tests
#
# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Parent script for unit testing a Mac OS X image candidate.

This script expects to be passed the path to a dmg that is a Mac OS X
image candidate. It mounts the image, imports the modules in the tests dir,
builds up a test suite of their test functions and runs them on the image.

Each test has "self.mountpoint" set that is the mountpoint of the dmg

Unit tests in the test directory must be subclasses of macdmgtest.DMGUnitTest.

Naming formats must be as follows:
  Files:    *_test.py
  Classes:  Test*
  Tests:    test*

Author: Nigel Kersten (nigelk@google.com)
Modified by: Joe Block (jpb@google.com)
"""

import optparse
import os
import re
import subprocess
import sys
import types
import unittest
import plistlib


def AttachDiskImage(path):
  """attaches a dmg, returns mountpoint, assuming only one filesystem."""

  command = ["/usr/bin/hdiutil", "attach", path, "-mountrandom", "/tmp",
             "-readonly", "-nobrowse", "-noautoopen", "-plist",
             "-owners", "on"]
  task = subprocess.Popen(command,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
  (stdout, stderr) = task.communicate()
  if task.returncode:
    print "There was an error attaching dmg: %s" % path
    print stderr
    return False
  else:
    mountpoint = False
    dmg_plist = plistlib.readPlistFromString(stdout)
    entities = dmg_plist["system-entities"]
    for entity in entities:
      if "mount-point" in entity:
        mountpoint = entity["mount-point"]
    return mountpoint


def DetachDiskImage(path):
  """forcibly unmounts a given dmg from the mountpoint path."""

  command = ["/usr/bin/hdiutil", "detach", path]
  returncode = subprocess.call(command)
  if returncode:
    command = ["/usr/bin/hdiutil", "detach", "-force", path]
    returncode = subprocess.call(command)
    if returncode:
      raise StandardError("Unable to unmount dmg mounted at: %s" % path)
  return True


def TestClasses(module):
  """returns test classes in a module."""
  classes = []
  pattern = re.compile("^Test\w+$")  # only classes starting with "Test"
  for name in dir(module):
    obj = getattr(module, name)
    if type(obj) in (types.ClassType, types.TypeType):
      if pattern.match(name):
        classes.append(name)
  return classes


def GetTestSuite(path, mountpoint, options):
  """Given path to module, returns suite of test methods."""
  dirname = os.path.dirname(path)
  filename = os.path.basename(path)

  if not dirname in sys.path:
    sys.path.append(dirname)

  modulename = re.sub("\.py$", "", filename)
  module = __import__(modulename)
  for classname in TestClasses(module):
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromName(classname, module)
    # there must be a better way than this protected member access...
    for test in test_suite._tests:
      test.SetMountpoint(mountpoint)
      test.SetOptions(options)
    return test_suite


def ListTests(path):
  """lists tests in directory "path" ending in _test.py."""

  pattern = re.compile("^\w*_test.py$", re.IGNORECASE)
  tests = []
  for test in os.listdir(path):
    if pattern.match(test):
      tests.append(test)
  tests.sort()
  return tests


def SummarizeResults(result):
  """Print a summary of a test result."""
  print
  print "Results"
  print "==============="

  print "total tests run: %s" % result.testsRun
  print "   errors found: %s" % len(result.errors)
  print " failures found: %s" % len(result.failures)
  print


def ParseCLIArgs():
  """Parse command line arguments and set options accordingly."""
  cli = optparse.OptionParser()
  cli.add_option("-c", "--configdir", dest="configdir", default=".",
                 type="string", help="specify directory for test config files")
  cli.add_option("-d", "--dmg", dest="dmg", type="string",
                 help="specify path to dmg to test.")
  cli.add_option("-p", "--pkgdir", dest="pkgdir", type="string",
                 help="specify directory to look for packages in.")
  cli.add_option("-r", "--root", dest="root", type="string",
                 help="specify path to root of a directory tree to test.")
  cli.add_option("-t", "--testdir", dest="testdir", default="tests",
                 type="string", help="specify directory with tests")
  cli.add_option("-v", "--verbosity", type="int", dest="verbosity",
                 help="specify verbosity level", default=0)
  (options, args) = cli.parse_args()
  return (options, args)


def main():
  """entry point."""
  (options, unused_args) = ParseCLIArgs()
  dmg = options.dmg
  verbosity = options.verbosity
  tests_dir = options.testdir
  config_dir = options.configdir
  root = options.root
  if not dmg and not root:
    print "Use --dmg to specify a dmg file or --root to specify a directory."
    sys.exit(1)
  if dmg:
    print "Mounting disk image... (this may take some time)"
    mountpoint = AttachDiskImage(dmg)
    if not mountpoint:
      print "Unable to mount %s" % dmg
      sys.exit(2)
  elif root:
    if not os.path.isdir(root):
      print "%s not a directory" % root
      sys.exit(2)
    mountpoint = root
    print "Checking %s" % mountpoint
  print

  dirname = os.path.dirname(sys.argv[0])
  os.chdir(dirname)
  tests = ListTests(tests_dir)
  test_results = {}
  combo_suite = unittest.TestSuite()
  for test in tests:
    test_path = os.path.join(tests_dir, test)
    combo_suite.addTests(GetTestSuite(test_path, mountpoint, options))

  test_results = unittest.TextTestRunner(verbosity=verbosity).run(combo_suite)

  if dmg:
    DetachDiskImage(mountpoint)

  if test_results.wasSuccessful():
    sys.exit(0)
  else:
    SummarizeResults(test_results)
    bad = len(test_results.errors) + len(test_results.failures)
    sys.exit(bad)


if __name__ == "__main__":
  main()

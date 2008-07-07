#!/usr/bin/env python
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

Naming formats must be as follows:
  Classes:  Test*
  Tests:    test*

Original Author: Nigel Kersten (nigelk@google.com)
"""

import os
import re
import subprocess
import sys
import types
import unittest
import plistlib


tests_dir = "tests"


def AttachDiskImage(path):
  """attaches a dmg, returns mountpoint, assuming only one filesystem."""
  
  command = ["hdiutil", "attach", path, "-mountrandom", "/tmp",
             "-readonly", "-nobrowse", "-noautoopen", "-plist"]
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
  
  command = ["hdiutil", "detach", path]
  returncode = subprocess.call(command)
  if returncode:
    command = ["hdiutil", "detach", "-force", path]
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


def RunTest(path, mountpoint):
  """run_test from path to module, returns testresult."""
  verbosity = 2
  dirname = os.path.dirname(path)
  filename = os.path.basename(path)
  
  if not dirname in sys.path:
    sys.path.append(dirname)
  
  modulename = re.sub("\.py$", "", filename)
  module = __import__(modulename)
  for classname in TestClasses(module):
    test_loader = unittest.TestLoader()
    test_result = unittest.TestResult()
    test_suite = test_loader.loadTestsFromName(classname, module)
    # there must be a better way than this protected member access...
    for test in test_suite._tests:
      test.mountpoint = mountpoint
    test_result = unittest.TextTestRunner(verbosity=verbosity).run(test_suite)
    return test_result


def ListTests(path):
  """lists tests in directory "path" ending in _test.py."""
  
  pattern = re.compile("^\w*_test.py$", re.IGNORECASE)
  tests = []
  for test in os.listdir(path):
    if pattern.match(test):
      tests.append(test)
  return tests


def main():
  """entry point."""
  
  if not len(sys.argv) == 2:
    print "You must pass the path to a dmg as the only argument"
    sys.exit(2)
  
  dmg = sys.argv[1]
  
  print "Mounting disk image... (this may take some time)"
  mountpoint = AttachDiskImage(dmg)
  
  if not mountpoint:
    print "Unable to mount %s" % dmg
    sys.exit(2)
  
  dirname = os.path.dirname(sys.argv[0])
  os.chdir(dirname)
  tests = ListTests(tests_dir)
  test_results = {}
  for test in tests:
    test_path = os.path.join(tests_dir, test)
    test_results[test] = RunTest(test_path, mountpoint)
  
  # not doing anything with the test results yet.
  # not sure if it's worth it given the nice existing output...?
  
  DetachDiskImage(mountpoint)


if __name__ == "__main__":
  main()

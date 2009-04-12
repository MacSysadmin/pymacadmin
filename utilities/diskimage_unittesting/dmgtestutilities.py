#!/usr/bin/python2.5
#
# Use 2.5 so we can import objc & Foundation in tests
#
# Copyright 2008 Google Inc. All Rights Reserved.
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
#
# This has to run under Apple's python2.5 so it can import Cocoa classes.

"""Helper functions for DMG unit tests."""
__author__ = 'jpb@google.com (Joe Block)'

import subprocess
import Foundation


def RemoveEmpties(a_list):
  """Returns a list with no empty lines."""
  cleaned = []
  for a in a_list:
    if a:
      cleaned.append(a)
  return cleaned


def ProcessCommand(command, strip_empty_lines=True):
  """Return a dict containing command's stdout, stderr & error code.

  Args:
    command: list containing the command line we want run
    strip_empty_lines: Boolean to tell us to strip empty lines or not.

  Returns:
    dict with stdout, stderr and error code from the command run.
  """
  cmd = subprocess.Popen(command, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
  (stdout, stderr) = cmd.communicate()
  info = {}
  info['errorcode'] = cmd.returncode
  if not strip_empty_lines:
    info['stdout'] = stdout.split('\n')
    info['stderr'] = stderr.split('\n')
  else:
    info['stdout'] = RemoveEmpties(stdout.split('\n'))
    info['stderr'] = RemoveEmpties(stderr.split('\n'))
  return info


def LintPlist(path):
  """plutil -lint path.

  Args:
    path: file to lint

  Returns:
    errorcode of plutil -lint
  """
  cmd = ProcessCommand(['/usr/bin/plutil', '-lint', path])
  return cmd['errorcode']


def ReadPlist(plistfile):
  """Read a plist, return a dict.

  Args:
    plistfile: Path to plist file to read

  Returns:
    dict of plist contents.
  """
  return Foundation.NSDictionary.dictionaryWithContentsOfFile_(plistfile)


if __name__ == '__main__':
  print 'This is not a standalone script. It contains only helper functions.'

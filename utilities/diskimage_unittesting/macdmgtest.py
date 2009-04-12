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

"""Base class for dmg unit tests."""
__author__ = 'jpb@google.com (Joe Block)'

import os
import unittest


def main():
  """Print usage warning."""
  print 'This is not a standalone test suite. Run with run_image_tests.py.'


class DMGUnitTest(unittest.TestCase):
  """Helper functions for DMG unit tests."""

  def SetMountpoint(self, mountpoint):
    """Set mountpoint."""
    self.mountpoint = mountpoint

  def SetOptions(self, options):
    """Set options parsed from command line.

    Args:
      options: command line options passed in by image testing driver script.
    """
    self.options = options

  def Mountpoint(self):
    """Return mountpoint of dmg being tested."""
    return self.mountpoint

  def ConfigPath(self, configfile):
    """Returns path to a config file with configdir prepended.
    Args:
      path: relative path of config file
    Returns:
      Actual path to that file, based on configdir"""
    return os.path.join(self.options.configdir, configfile)

  def PathOnDMG(self, path):
    """Returns path with dmg mount path prepended.

    Args:
      path: path to a file on the dmg
    """
    # deal with leading /es in path var.
    while path[:1] == '/':
      path = path[1:]
    return os.path.join(self.mountpoint, path)

  def CheckForExistence(self, filename):
    """Make sure filename doesn't exist on the tested image.

    Args:
      filename: file to look for on the dmg
    """
    if filename:
      path = self.PathOnDMG(filename)
      return os.path.exists(path)
    else:
      return False


if __name__ == '__main__':
  Main()

#!/usr/bin/python2.4
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

"""Make sure blacklisted files or directories are not present on the image."""

__author__ = 'jpb@google.com (Joe Block)'

import macdmgtest
import dmgtestutilities


def ReadBlackList(path):
  """Read a blacklist of forbidden directories and files.

  Ignore lines starting with a # so we can comment the datafile.

  Args:
    path: file to load the blacklist from.
  Returns:
    dictionary of path:True mappings
  """
  blacklist_file = open(path, 'r')
  catalog = []
  for entry in blacklist_file:
    if not entry or entry[:1] == '#':
      pass   # ignore comment and empty lines in blacklist file
    else:
      catalog.append(entry.strip())
  return catalog


class TestBlacklists(macdmgtest.DMGUnitTest):

  def setUp(self):
    blacklist_path = self.ConfigPath('file_and_directory.blacklist')
    self.blacklist = ReadBlackList(blacklist_path)

  def ProcessList(self, the_list):
    """files/directories from the_list should be absent from the image.

    Args:
      the_list: A list of paths to file or directories that should be absent
          from the image.
    Returns:
      list of directories/files that are present that shouldn't be.
    """
    bad = []
    for d in the_list:
      if self.CheckForExistence(d) == True:
        bad.append(d)
    return bad

  def testBlacklistedDirectories(self):
    """Ensure directories from blacklist are absent from the image."""
    badfound = self.ProcessList(self.blacklist)
    if badfound:
      print 'These files and directories should not exist:'
      print '%s' % badfound
    self.assertEqual(len(badfound), 0)


if __name__ == '__main__':
  macdmgtest.main()

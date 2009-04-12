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
#
# Tests are done in alphabetical order by file name, so since this
# traverses the entire dmg, using zz to push it to the end with the
# other slow unit tests.

"""Confirm all world-writable files and dirs on the dmg are in our whitelist."""
__author__ = 'jpb@google.com (Joe Block)'


import logging
import dmgtestutilities
import macdmgtest


def CatalogWritables(path):
  """Finds all the files and directories that are world-writeable.

  Args:
    path: root of directory tree to examine.
  Returns:
    dictionary of paths to world-writeable files & directories under root,
    with the base path to the root peeled off.
  """

  dir_cmd = ['/usr/bin/find', path, '-type', 'd', '-perm', '+o=w', '-exec',
             'ls', '-ld', '{}', ';']
  file_cmd = ['/usr/bin/find', path, '-type', 'f', '-perm', '+o=w', '-exec',
              'ls', '-l', '{}', ';']
  logging.debug('Searching dmg for world writable files')
  files = dmgtestutilities.ProcessCommand(file_cmd)
  logging.debug('Searching dmg for world writable directories')
  dirs = dmgtestutilities.ProcessCommand(dir_cmd)
  state_of_sin = dirs['stdout'] + files['stdout']

  writeables = []
  prefix_length = len(path)
  for s in state_of_sin:
    if s:
      snip = s.find('/')
      if snip:
        snip_index = snip + prefix_length
        rawpath = s[snip_index:]
        writeables.append(rawpath)
      else:
        logging.warn('snip: %s' % snip)
        logging.warn(s)
  return writeables


def ReadWhiteList(path):
  """Read a whitelist of world writable files and directories into a dict.

  Ignore lines starting with a # so we can comment the whitelist.

  Args:
    path: file to load the whitelist from.
  Returns:
    dictionary of path:True mappings
  """
  white_file = open(path, 'r')
  catalog = {}
  for entry in white_file:
    if not entry or entry[:1] == '#':
      pass   # ignore comment and empty lines
    else:
      catalog[entry.strip()] = True
  return catalog


class TestWritableDirectoriesAndFiles(macdmgtest.DMGUnitTest):

  def setUp(self):
    whitelist_path = self.ConfigPath('writables.whitelist')
    self.whitelisted_writables = ReadWhiteList(whitelist_path)

  def testForWorldWritableFilesOrDirectories(self):
    """SLOW: Search for non-whitelisted world-writable files and directories."""
    scrutinize = CatalogWritables(self.Mountpoint())
    sinners = []
    for s in scrutinize:
      if s not in self.whitelisted_writables:
        sinners.append(s)
    if sinners:
      print '\n\n# world-writable files & dirs for pasting into whitelist.'
      print '\n'.join(sinners)
      print '# end paste\n\n'
    self.assertEqual(0, len(sinners))


if __name__ == '__main__':
  macdmgtest.main()

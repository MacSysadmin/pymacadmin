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
# tests are done in alphabetical order by file name, so since this
# traverses the entire dmg, using zz to push it to the end with the
# other slow unit tests.

"""Check that all setuid & setgid files on the dmg are in our whitelist."""
__author__ = 'jpb@google.com (Joe Block)'


import logging
import dmgtestutilities
import macdmgtest


def ListSuidSgid(path):
  """Finds all the suid/sgid files under path.

  Args:
    path: root of directory tree to examine.
  Returns:
    dictionary of Suid/Sgid files.
  """

  cmd = ['/usr/bin/find', path, '-type', 'f', '(', '-perm', '-004000', '-o',
         '-perm', '-002000', ')', '-exec', 'ls', '-l', '{}', ';']
  res = dmgtestutilities.ProcessCommand(cmd)
  catalog = []
  prefix_length = len(path)
  for f in res['stdout']:
    if f:
      snip = f.find('/')
      if snip:
        snip_index = snip + prefix_length
        rawpath = f[snip_index:]
        catalog.append(rawpath)
      else:
        logging.warn('snip: %s' % snip)
        logging.warn(f)
  return catalog


def ReadWhiteList(path):
  """Read a whitelist of setuid/setgid files.

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
      pass   # ignore comment and empty lines in whitelist file
    else:
      catalog[entry.strip()] = True
  return catalog


class TestSUIDGUIDFiles(macdmgtest.DMGUnitTest):

  def setUp(self):
    whitelist_path = self.ConfigPath('suidguid.whitelist')
    self.whitelisted_suids = ReadWhiteList(whitelist_path)

  def testForUnknownSUIDsAndGUIDs(self):
    """SLOW: Search for non-whitelisted suid/guid files on dmg."""
    scrutinize = ListSuidSgid(self.Mountpoint())
    illegal_suids = []
    for s in scrutinize:
      if s not in self.whitelisted_suids:
        illegal_suids.append(s)
    if illegal_suids:
      # make it easier to update the whitelist when a new Apple update adds
      # a suid/sgid file
      print '\n\n# suid/sgid files suitable for pasting into whitelist.'
      '\n'.join(illegal_suids)
      print '# end paste\n\n'
    self.assertEqual(0, len(illegal_suids))


if __name__ == '__main__':
  macdmgtest.main()

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

"""Check that all symlinks in /Library don't have brain damaged targets."""
__author__ = 'jpb@google.com (Joe Block)'


import dmgtestutilities
import macdmgtest


class TestSymlinks(macdmgtest.DMGUnitTest):
  """Test dmg to ensure no symlinks point to other drives."""

  def testForSymlinksToOtherVolumes(self):
    """SLOW:Search for symbolic links pointing to other drives."""
    cmd = ['/usr/bin/find', self.Mountpoint(), '-type', 'l', '-exec',
           'readlink', '{}', ';']
    res = dmgtestutilities.ProcessCommand(cmd)
    hall_of_shame = []
    for f in res['stdout']:
      # we can't check just the beginning of the filename because of Apple's
      # penchant for destinations that are ../../../../Volumes/Foo/something
      if f.count('/Volumes/'):
        hall_of_shame.append(f)
    if hall_of_shame:
      print 'Bad symlinks found:'
      for h in hall_of_shame:
        print h
    self.assertEqual(0, len(hall_of_shame))


if __name__ == '__main__':
  macdmgtest.main()

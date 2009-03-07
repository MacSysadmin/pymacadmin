#!/usr/bin/python2.4
#
# Copyright 2008-2009 Google Inc.
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

"""Check that all .plist files on the dmg pass plutil lint."""
__author__ = 'jpb@google.com (Joe Block)'


import os
import dmgtestutilities
import macdmgtest


class TestLintPlistsOnDMG(macdmgtest.DMGUnitTest):
  """Checks all plist files on the dmg with plutil -lint.

  This is by far the slowest test we run, so force it to run last by starting
  the filename with zz. This way we don't have to wait for it to finish when
  we're testing other unit tests.
  """

  def setUp(self):
    """Setup Error statistics."""
    self.lint_output = []
    self.bad_plists = []

  def _CheckPlistFiles(self, unused_a, path, namelist):
    """Run plutil -lint on all the plist files in namelist."""
    for name in namelist:
      if os.path.splitext(name)[1] == '.plist':
        plistfile = os.path.join(path, name)
        cmd = dmgtestutilities.ProcessCommand(['/usr/bin/plutil', '-lint',
                                               plistfile])
        if cmd['errorcode']:
          self.bad_plists.append(plistfile)
          self.lint_output.append('Error found in %s' % plistfile)
          for x in cmd['stdout']:
            self.lint_output.append(x)

  def testPlistsOnDMG(self):
    """SLOW: Check all plists on dmg with plutil -lint. Can take 5 minutes."""
    dirname = self.PathOnDMG('')
    os.path.walk(dirname, self._CheckPlistFiles, None)
    # Print out the bad list. Normally it would be better practice to just
    # let the assert fail, but we want to know exactly what plists are bad on
    # the image so we can fix them.
    if self.bad_plists:
      print
      print 'Found %s bad plist files.' % len(self.bad_plists)
      print '\n\t'.join(self.bad_plists)
      print '\nErrors detected:'
      print '\n'.join(self.lint_output)
    self.assertEqual(len(self.lint_output), 0)
    self.assertEqual(len(self.bad_plists), 0)

if __name__ == '__main__':
  macdmgtest.main()

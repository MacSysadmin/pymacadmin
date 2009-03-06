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

"""Check size of dmg for sanity.

When I was starting to use InstaDMG/InstaUp2Date, bad configurations tended
to generate ridiculously sized dmg files, so confirm the dmg is in the window
we expected.

Yes, this will need updating if we add a significant amount of new items
to the dmg, but it catches the cases when the Instadmg run failed
spectacularly and creates an absurd output dmg.
"""
__author__ = "jpb@google.com (Joe Block)"

import os
import macdmgtest


TOO_BIG = 6000000000
TOO_SMALL = 5000000000


class TestDMGSize(macdmgtest.DMGUnitTest):

  def setUp(self):
    self.dmgpath = self.options.dmg

  def testDMGTooSmall(self):
    """Sanity check on dmg size: the dmg should be at least 5G."""
    if not self.dmgpath:
      print "..skipping DMGTooSmall check - not testing a dmg"
    else:
      dmg_size = os.path.getsize(self.dmgpath)
      self.failUnless(dmg_size > TOO_SMALL)

  def testDMGTooBig(self):
    """Sanity check on dmg size: the dmg should be no more than 6G."""
    if not self.dmgpath:
      print "..skipping DMGTooBig check - not testing a dmg"
    else:
      dmg_size = os.path.getsize(self.dmgpath)
      self.failUnless(dmg_size < TOO_BIG)


if __name__ == "__main__":
  macdmgtest.main()

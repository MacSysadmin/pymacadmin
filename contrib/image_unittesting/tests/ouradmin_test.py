#!/usr/bin/python2.5
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
#
# Change ouradmin to whatever local admin account you're adding to your image.
#
# We also sanity check that the group plists pass lint to ensure our localadmin
# creation package didn't somehow break them.

"""Make sure there's an ouradmin local account on the machine."""
__author__ = 'jpb@google.com (Joe Block)'

import os
import stat
import dmgtestutilities
import macdmgtest


class TestCheckForouradmin(macdmgtest.DMGUnitTest):
  """Make sure there's an ouradmin local account on the machine."""

  def setUp(self):
    """Setup paths."""
    self.localnode = 'var/db/dslocal/nodes/Default'
    self.admin_plist = self.PathOnDMG('%s/groups/admin.plist' % self.localnode)
    self.ouradmin_plist = self.PathOnDMG('%s/users/ouradmin.plist' %
                                         self.localnode)
    self.ouradmin_stat = os.stat(self.ouradmin_plist)
    self.lpadmin_plist = self.PathOnDMG('%s/groups/_lpadmin.plist' %
                                        self.localnode)
    self.appserveradm_plist = self.PathOnDMG('%s/groups/_appserveradm.plist' %
                                             self.localnode)

  def testOuradminIsMemberOfLPadminGroup(self):
    """Check that ouradmin user is in _lpadmin group."""
    pf = dmgtestutilities.ReadPlist(self.lpadmin_plist)
    self.assertEqual('ouradmin' in pf['users'], True)

  def testOuradminIsMemberOfAppserverAdminGroup(self):
    """Check that ouradmin user is in _appserveradm group."""
    pf = dmgtestutilities.ReadPlist(self.appserveradm_plist)
    self.assertEqual('ouradmin' in pf['users'], True)

  def testOuradminIsMemberOfAdminGroup(self):
    """Check that ouradmin user is in admin group."""
    pf = dmgtestutilities.ReadPlist(self.admin_plist)
    self.assertEqual('ouradmin' in pf['users'], True)

  def testOuradminIsInDSLocal(self):
    """Check for ouradmin user in local ds node."""
    plistpath = self.PathOnDMG('%s/users/ouradmin.plist' % self.localnode)
    self.assertEqual(os.path.exists(plistpath), True)

  def testOuradminPlistMode(self):
    """ouradmin.plist is supposed to be mode 600."""
    mode = self.ouradmin_stat[stat.ST_MODE]
    num_mode = oct(mode & 0777)
    self.assertEqual('0600', num_mode)

  def testOuradminPlistCheckGroup(self):
    """ouradmin.plist should be group wheel."""
    group = self.ouradmin_stat[stat.ST_GID]
    self.assertEqual(0, group)

  def testOuradminPlistCheckOwnership(self):
    """ouradmin.plist should be owned by root."""
    owner = self.ouradmin_stat[stat.ST_UID]
    self.assertEqual(0, owner)

  # lint every plist the localadmin creation package had to touch.

  def testPlistLintAdminGroup(self):
    """Make sure admin.plist passes lint."""
    cmd = dmgtestutilities.LintPlist(self.admin_plist)
    self.assertEqual(cmd, 0)

  def testPlistLintAppserverAdminGroup(self):
    """Make sure _appserveradm.plist passes lint."""
    cmd = dmgtestutilities.LintPlist(self.appserveradm_plist)
    self.assertEqual(cmd, 0)

  def testPlistLintLPAdminGroup(self):
    """Make sure _lpadmin.plist passes lint."""
    cmd = dmgtestutilities.LintPlist(self.lpadmin_plist)
    self.assertEqual(cmd, 0)

  def testOuradminPlistLint(self):
    """Make sure ouradmin.plist passes lint."""
    cmd = dmgtestutilities.LintPlist(self.ouradmin_plist)
    self.assertEqual(cmd, 0)


if __name__ == '__main__':
  macdmgtest.main()

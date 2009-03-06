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


"""Check user/group/permissions in /Applications & /Applications/Utilities.

Author: Joe Block (jpb@google.com)
"""

import logging
import os
import pprint
import stat
import macdmgtest


class TestAppDirectories(macdmgtest.DMGUnitTest):

  def setUp(self):
    """Set up exceptions to standard permissions requirements."""
    self.errors_found = []
    self.standard_stat = {'uid': 0, 'gid': 80, 'mode': '0775'}
    self.application_exceptions = {}
    self.application_exceptions['System Preferences'] = {}
    self.application_exceptions['System Preferences']['gid'] = 0
    self.application_exceptions['System Preferences']['mode'] = '0775'
    self.application_exceptions['System Preferences']['uid'] = 0
    self.utilities_exceptions = {}
    # Here are a couple of examples of making exceptions for stuff we
    # symlink into Applications or Applications/Utilities
    self.utilities_exceptions['Kerberos'] = {}
    self.utilities_exceptions['Kerberos']['gid'] = 0
    self.utilities_exceptions['Kerberos']['mode'] = '0755'
    self.utilities_exceptions['Kerberos']['symlink_ok'] = True
    self.utilities_exceptions['Kerberos']['uid'] = 0
    self.utilities_exceptions['Screen Sharing'] = {}
    self.utilities_exceptions['Screen Sharing']['gid'] = 0
    self.utilities_exceptions['Screen Sharing']['mode'] = '0755'
    self.utilities_exceptions['Screen Sharing']['symlink_ok'] = True
    self.utilities_exceptions['Screen Sharing']['uid'] = 0

  def _SanityCheckApp(self, statmatrix, overrides, thedir, name):
    """Check a .app directory and ensure it has sane perms and ownership."""
    o = os.path.splitext(name)[0]
    if o in overrides:
      g_uid = overrides[o]['uid']
      g_gid = overrides[o]['gid']
      g_mode = overrides[o]['mode']
    else:
      g_uid = statmatrix['uid']
      g_gid = statmatrix['gid']
      g_mode = statmatrix['mode']
    path = os.path.join(self.mountpoint, thedir, name)
    check_stats = os.stat(path)
    a_mode = oct(check_stats[stat.ST_MODE] & 0777)
    a_gid = check_stats[stat.ST_GID]
    a_uid = check_stats[stat.ST_UID]
    if os.path.islink(path):
      if o in overrides:
        if 'symlink_ok' in overrides[o]:
          if not overrides[o]['symlink_ok']:
            msg = '%s/%s is a symlink and should not be.' % (thedir, name)
            self.errors_found.append(msg)
            logging.debug(msg)
      else:
        msg = '%s/%s is a symlink, not an application.' % (thedir, name)
        self.errors_found.append(msg)
        logging.debug(msg)
    if a_uid != g_uid:
      msg = '%s/%s is owned by %s, should be owned by %s' % (thedir, name,
                                                             a_uid, g_uid)
      self.errors_found.append(msg)
      logging.debug(msg)
    if a_gid != g_gid:
      msg = '%s/%s is group %s, should be group %s' % (thedir, name, a_gid,
                                                       g_gid)
      self.errors_found.append(msg)
      logging.debug(msg)
    if a_mode != g_mode:
      msg = '%s/%s was mode %s, should be %s' % (thedir, name, a_mode, g_mode)
      self.errors_found.append(msg)
      logging.debug(msg)

  def testApplicationDirectory(self):
    """Sanity check all applications in /Applications."""
    self.errors_found = []
    appdir = 'Applications'
    for application in os.listdir(os.path.join(self.mountpoint, appdir)):
      if os.path.splitext(application)[1] == '.app':
        self._SanityCheckApp(self.standard_stat, self.application_exceptions,
                             appdir, application)
    if self.errors_found:
      print
      pprint.pprint(self.errors_found)
    self.assertEqual(len(self.errors_found), 0)

  def testUtilitiesDirectory(self):
    """Sanity check applications in /Applications/Utilities."""
    self.errors_found = []
    appdir = 'Applications/Utilities'
    for application in os.listdir(os.path.join(self.mountpoint, appdir)):
      if application[-3:] == 'app':
        self._SanityCheckApp(self.standard_stat, self.utilities_exceptions,
                             appdir, application)
    if self.errors_found:
      print
      pprint.pprint(self.errors_found)
    self.assertEqual(len(self.errors_found), 0)


if __name__ == '__main__':
  macdmgtest.main()

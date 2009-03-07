#!/usr/bin/python2.5
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

"""Network settings tests to cope with Airbook brain damage."""
__author__ = 'jpb@google.com (Joe Block)'

import dmgtestutilities
import macdmgtest


class TestNetworkAirbookCompliant(macdmgtest.DMGUnitTest):
  """Check that network settings suitably munged for Airbooks."""

  def setUp(self):
    """Setup paths."""
    self.system_pref_path = self.PathOnDMG(
      '/Library/Preferences/SystemConfiguration/preferences.plist')
    self.sys_prefs = dmgtestutilities.ReadPlist(self.system_pref_path)
    if not self.sys_prefs:
      self.sys_prefs = {}

  def testNetworkPlistIsAbsent(self):
    """Ensure NetworkInterfaces.plist absent, it will be rebuilt for Airbook."""
    nw = '/Library/Preferences/SystemConfiguration/NetworkInterfaces.plist'
    self.assertEqual(self.CheckForExistence(nw), False)

  def testSystemPreferencesPlistIsAbsent(self):
    """SystemConfiguration/preferences absent? will be rebuilt for Airbook."""
    self.assertEqual(self.CheckForExistence(self.system_pref_path), False)

  def testEnsureNoCurrentSet(self):
    """SystemConfiguration/preferences.plist must not have CurrentSet key."""
    self.assertEqual('CurrentSet' in self.sys_prefs, False)

  def testEnsureNoNetworkServices(self):
    """SystemConfiguration/preferences.plist can't have NetworkServices key."""
    self.assertEqual('NetworkServices' in self.sys_prefs, False)

  def testEnsureNoSets(self):
    """SystemConfiguration/preferences.plist must not have Sets key."""
    self.assertEqual('Sets' in self.sys_prefs, False)


if __name__ == '__main__':
  macdmgtest.main()

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

"""Ensure correct software update catalog url is set on image.

Author: Joe Block (jpb@google.com)
"""

import os
import stat
import dmgtestutilities
import macdmgtest


class TestSoftwareUpdateURL(macdmgtest.DMGUnitTest):
  """Check validity of Software Update preferences on image."""

  def setUp(self):
    """Setup paths and load plist data."""
    self.su_pref_path = self.PathOnDMG(
        "/Library/Preferences/com.apple.SoftwareUpdate.plist")
    self.su_prefs = dmgtestutilities.ReadPlist(self.su_pref_path)
    if not self.su_prefs:
      self.su_prefs = {}

  def testSoftwareUpdatePlist(self):
    """Ensure com.apple.SoftwareUpdate.plist is installed on the image."""
    self.assertEqual(self.CheckForExistence(
        "/Library/Preferences/com.apple.SoftwareUpdate.plist"), True)

  def testOwnerGroupMode(self):
    """test owner, group and mode of com.apple.SoftwareUpdate.plist."""
    software_update_stat = os.stat(self.su_pref_path)
    owner = software_update_stat[stat.ST_UID]
    group = software_update_stat[stat.ST_GID]
    mode = software_update_stat[stat.ST_MODE]
    num_mode = oct(mode & 0777)
    self.assertEqual(0, owner)
    self.assertEqual(80, group)
    self.assertEqual("0644", num_mode)

  def testSoftwareUpdateCatalogURL(self):
    """test that Software Update is set to use internal CatalogURL."""
    self.assertEqual("http://path/to/your/internal/swupd/",
                     self.su_prefs["CatalogURL"])

if __name__ == "__main__":
  macdmgtest.main()


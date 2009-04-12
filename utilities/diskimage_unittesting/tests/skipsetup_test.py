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

"""Make sure dmg is set to not run Apple setup application on first boot."""
__author__ = 'jpb@google.com (Joe Block)'

import macdmgtest


class TestEnsureAppleSetupWillNotRun(macdmgtest.DMGUnitTest):

  def testAppleSetupDone(self):
    """Ensure first boot setup already done: .AppleSetupDone is on the dmg."""
    apple_setup_done = 'var/db/.AppleSetupDone'
    self.assertEqual(self.CheckForExistence(apple_setup_done), True)

  def testSetupRegCompletePresent(self):
    """Ensure first boot setup already done: .SetupRegComplete is on the dmg."""
    setup_reg_complete = 'Library/Receipts/.SetupRegComplete'
    self.assertEqual(self.CheckForExistence(setup_reg_complete), True)

if __name__ == '__main__':
  macdmgtest.main()

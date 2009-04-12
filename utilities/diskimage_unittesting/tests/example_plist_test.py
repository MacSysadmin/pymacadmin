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


"""Example test showing how to check values inside a plist.

This example tests the existence of certain fields within:
/Library/Preferences/com.foo.corp.imageinfo.plist

This plist identifies the date at which an image was created, so this series
of tests simply checks whether the plist exists, whether it is a proper file
as opposed to a symlink, whether the imageVersion field exists, whether it can
be made into a valid date, and whether the date is a sane value.

As with this whole framework, the attribute self.mountpoint refers to the
location at which the image to be tested is mounted.

Note that we're copying the plist to a temporary location and converting it
to xml1 format rather than binary. We do this so that plistlib works
(it doesn't work on binary plists) and so that we're not actually trying to
modify the image, which is mounted in read-only mode.

Original Author: Nigel Kersten (nigelk@google.com)
"""

import datetime
import os
import re
import shutil
import stat
import subprocess
import tempfile
import unittest
import plistlib


# don"t use absolute paths with os.path.join
imageinfo_plist = "Library/Preferences/com.foo.corp.imageinfo.plist"


class TestMachineInfo(unittest.TestCase):

  def setUp(self):
    """copy the original file to a temp plist and convert it to xml1."""
    self.tempdir = tempfile.mkdtemp()
    self.orig_imageinfo_file = os.path.join(self.mountpoint, imageinfo_plist)
    imageinfo_file = os.path.join(self.tempdir, "imageinfo.plist")
    shutil.copyfile(self.orig_imageinfo_file, imageinfo_file)
    command = ["plutil", "-convert", "xml1", imageinfo_file]
    returncode = subprocess.call(command)
    if returncode:
      raise StandardError("unable to convert plist to xml1")
    self.imageinfo = plistlib.readPlist(imageinfo_file)

  def tearDown(self):
    """clean up the temporary location."""
    if self.tempdir:
      if os.path.isdir(self.tempdir):
        shutil.rmtree(self.tempdir)

  def testFile(self):
    """test the original file is a proper file."""
    self.assert_(os.path.isfile(self.orig_imageinfo_file))

  def testOwnerGroupMode(self):
    """test owner, group and mode of original file."""
    orig_imageinfo_stat = os.stat(self.orig_imageinfo_file)
    owner = orig_imageinfo_stat[stat.ST_UID]
    group = orig_imageinfo_stat[stat.ST_GID]
    mode = orig_imageinfo_stat[stat.ST_MODE]
    num_mode = oct(mode & 0777)
    self.assertEqual(0, owner)
    self.assertEqual(80, group)
    self.assertEqual('0644', num_mode)

  def testImageVersionPresent(self):
    """test that the ImageVersion field is present."""
    self.failUnless("ImageVersion" in self.imageinfo)

  def testImageVersionFormat(self):
    """test that the ImageVersion field is well formed."""
    pattern = re.compile("^\d{8}$")
    self.failUnless(pattern.match(self.imageinfo["ImageVersion"]))

  def testImageVersionValueIsDate(self):
    """test that the ImageVersion value is actually a date"""
    image_version = self.imageinfo["ImageVersion"]
    year = int(image_version[:4])
    month = int(image_version[4:-2])
    day = int(image_version[6:])
    now = datetime.datetime.now()
    self.failUnless(now.replace(year=year,month=month,day=day))

  def testImageVersionValueIsCurrentDate(self):
    """test that the ImageVersion value is a current date."""
    image_version = self.imageinfo["ImageVersion"]
    year = int(image_version[:4])
    year_range = range(2006, 2100)
    self.failUnless(year in year_range)



if __name__ == "__main__":
  unittest.main()

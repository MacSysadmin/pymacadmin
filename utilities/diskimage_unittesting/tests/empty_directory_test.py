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

"""Ensure directories that are supposed to be empty actually are."""

__author__ = 'jpb@google.com (Joe Block)'


import os
import macdmgtest


class TestEmptyDirectories(macdmgtest.DMGUnitTest):

  def setUp(self):
    self.empty_directories = ['var/vm',
                              '/private/tmp',
                              'Volumes',
                              'Library/Logs']

  def DirectoryEmpty(self, dirname):
    """Make sure dirname is empty."""
    path = self.PathOnDMG(dirname)
    if os.listdir(path):
      return False
    else:
      return True

  def testEmptyDirectories(self):
    """Ensure every directory that is supposed to be empty on the image, is."""
    full_dirs = []
    for d in self.empty_directories:
      if not self.DirectoryEmpty(d):
        full_dirs.append(d)
    self.assertEqual(len(full_dirs), 0)

if __name__ == '__main__':
  macdmgtest.main()

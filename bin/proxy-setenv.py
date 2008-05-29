#!/usr/bin/python
"""
Usage: eval `proxy-setenv.py`

Generates environmental variables for the current system proxy settings 
"""

from SystemConfiguration import *
import sys
import os

d = SCDynamicStoreCopyProxies(None)

if 'HTTPEnable' in d and d['HTTPEnable']:
  print "export http_proxy=http://%s:%s/" % (d['HTTPProxy'], d['HTTPPort'])
else:
  print "unset http_proxy"

if 'FTPEnable' in d and d['FTPEnable']:
  print "export ftp_proxy=http://%s:%s/" % (d['FTPProxy'], d['FTPPort'])
else:
  print "unset ftp_proxy"

#!/usr/bin/python
"""
Usage: eval `proxy-setenv.py`

Generates Bourne-shell environmental variable declarations based on the
current system proxy settings
"""

from SystemConfiguration import SCDynamicStoreCopyProxies

proxies = SCDynamicStoreCopyProxies(None)

if 'HTTPEnable' in proxies and proxies['HTTPEnable']:
    print "export http_proxy=http://%s:%s/" % (proxies['HTTPProxy'], proxies['HTTPPort'])
else:
    print "unset http_proxy"

if 'FTPEnable' in proxies and proxies['FTPEnable']:
    print "export ftp_proxy=http://%s:%s/" % (proxies['FTPProxy'], proxies['FTPPort'])
else:
    print "unset ftp_proxy"

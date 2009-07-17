#!/usr/bin/env python
# encoding: utf-8
"""
SCPreferences.py: Simplified interaction with SystemConfiguration preferences

TODO:
* Refactor getvalue/setvalue code into generic functions for dealing with things other than proxies
* Add get_proxy() to parallel set_proxy()
"""

import sys
import os
import unittest

from SystemConfiguration import *

class SCPreferences(object):
    """Utility class for working with the SystemConfiguration framework"""
    proxy_protocols = ('HTTP', 'FTP', 'SOCKS') # List of the supported protocols
    session = None

    def __init__(self):
        super(SCPreferences, self).__init__()
        self.session = SCPreferencesCreate(None, "set-proxy", None)

    def save(self):
        if not self.session:
            return
        if not SCPreferencesCommitChanges(self.session):
            raise RuntimeError("Unable to save SystemConfiguration changes")
        if not SCPreferencesApplyChanges(self.session):
            raise RuntimeError("Unable to apply SystemConfiguration changes")

    def set_proxy(self, enable=True, protocol="HTTP", server="localhost", port=3128):
        new_settings = SCPreferencesPathGetValue(self.session, u'/NetworkServices/')

        for interface in new_settings:
            new_settings[interface]['Proxies']["%sEnable" % protocol] = 1 if enable else 0
            if enable:
                new_settings[interface]['Proxies']['%sPort' % protocol]  = int(port)
                new_settings[interface]['Proxies']['%sProxy' % protocol] = server

        SCPreferencesPathSetValue(self.session, u'/NetworkServices/', new_settings)

class SCPreferencesTests(unittest.TestCase):
    def setUp(self):
        raise RuntimeError("Thwack Chris about not writing these yet")

if __name__ == '__main__':
    unittest.main()

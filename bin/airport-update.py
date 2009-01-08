#!/usr/bin/python
# encoding: utf-8
"""
Usage: airport-update.py SSID NEW_PASSWORD

Updates the System keychain to replace the existing password for the specified
SSID with NEW_PASSWORD

BUG: Currently provides no way to set a password for a previously-unseen SSID
"""

import sys
import os
from PyMacAdmin.Security.Keychain import Keychain


def main():
    if len(sys.argv) < 3:
        print >> sys.stderr, __doc__.strip()
        sys.exit(1)

    ssid, new_password = sys.argv[1:3]

    if os.getuid() == 0:
        keychain = Keychain("/Library/Keychains/System.keychain")
    else:
        keychain = Keychain()

    try:
        item = keychain.find_generic_password(account_name=ssid)
        if item.password != new_password:
            item.update_password(new_password)

    except RuntimeError, exc:
        print >> sys.stderr, "Unable to change password for Airport network %s: %s" % (ssid, exc)
        sys.exit(1)

    print "Changed password for AirPort network %s to %s" % (ssid, new_password)

if __name__ == "__main__":
    main()

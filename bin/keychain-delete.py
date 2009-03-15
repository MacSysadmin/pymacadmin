#!/usr/bin/env python
# encoding: utf-8
"""
Usage: %prog [--service=SERVICE_NAME] [--account=ACCOUNT_NAME] [--keychain=/path/to/keychain]

Remove the specified password from the keychain
"""

from PyMacAdmin.Security.Keychain import Keychain
import os
import sys
from optparse import OptionParser


def main():
    parser = OptionParser(__doc__.strip())

    parser.add_option('-a', '--account', '--account-name',
        help="Set the account name"
    )

    parser.add_option('-s', '--service', '--service-name',
        help="Set the service name"
    )

    parser.add_option('-k', '--keychain',
        help="Path to the keychain file"
    )

    (options, args) = parser.parse_args()

    if not options.keychain and os.getuid() == 0:
        options.keychain = "/Library/Keychains/System.keychain"

    if not options.account and options.service:
        parser.error("You must specify either an account or service name")

    try:
        keychain = Keychain(options.keychain)
        item = keychain.find_generic_password(
            service_name=options.service,
            account_name=options.account
        )

        print "Removing %s" % item
        keychain.remove(item)
    except KeyError, exc:
        print >>sys.stderr, exc.message
        sys.exit(0)
    except RuntimeError, exc:
        print >>sys.stderr, "Unable to delete keychain item: %s" % exc
        sys.exit(1)

if __name__ == "__main__":
    main()
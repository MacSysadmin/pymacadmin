#!/usr/bin/env python
# encoding: utf-8
"""
Updates existing keychain internet password items with a new password.
Usage: keychain-internet-password-update.py account_name new_password

Contributed by Matt Rosenberg
"""

import ctypes
import sys

# Load Security.framework
Security = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/Security.framework/Versions/Current/Security')

def FourCharCode(fcc):
    """Create an integer from the provided 4-byte string, required for finding keychain items based on protocol type"""
    return ord(fcc[0]) << 24 | ord(fcc[1]) << 16 | ord(fcc[2]) << 8 | ord(fcc[3])

def UpdatePassword(account_name, new_password, server_name, protocol_type_string=''):
    """
    Function to update an existing internet password keychain item

    Search for the existing item is based on account name, password, server, and
    protocol (optional). Additional search parameters are available, but are
    hard-coded to null here.

    The list of protocol type codes is in
    /System/Library/Frameworks/Security.framework/Versions/Current/Headers/SecKeychain.h
    """

    item             = ctypes.c_char_p()
    port_number      = ctypes.c_uint16(0) # Set port number to 0, works like setting null for most other search parameters
    password_length  = ctypes.c_uint32(256)
    password_pointer = ctypes.c_char_p()

    if protocol_type_string:
        protocol_type_code = FourCharCode(protocol_type_string)
    else:
        protocol_type_code = 0

    # Call function to locate existing keychain item
    rc = Security.SecKeychainFindInternetPassword(
        None,
        len(server_name),
        server_name,
        None,
        None,
        len(account_name),
        account_name,
        None,
        None,
        port_number,
        protocol_type_code,
        None,
        None, # To retrieve the current password, change this argument to: ctypes.byref(password_length)
        None, # To retrieve the current password, change this argument to: ctypes.pointer(password_pointer)
        ctypes.pointer(item)
    )

    if rc != 0:
        raise RuntimeError('Did not find existing password for server %s, protocol type %s, account name %s: rc=%d' % (server_name, protocol_type_code, account_name, rc))

    # Call function to update password
    rc = Security.SecKeychainItemModifyAttributesAndData(
        item,
        None,
        len(new_password),
        new_password
    )

    if rc != 0:
        raise RuntimeError('Failed to record new password for server %s, protocol type %s, account name %s: rc=%d' % (server_name, protocol_type_code, account_name, rc))

    return 0

# Start execution

# Check to make sure needed arguments were passed
if len(sys.argv) != 3:
    raise RuntimeError('ERROR: Incorrect number of arguments. Required usage: keychain-internet-password-update.py account_name new_password')

# Set variables from the argument list
account_name = sys.argv[1]
new_password = sys.argv[2]

# Call UpdatePassword for each password to update.
#
# If more than one keychain item will match a server and account name, you must
# specify a protocol type. Otherwise, only the first matching item will be
# updated.
#
# The list of protocol type codes is in
# /System/Library/Frameworks/Security.framework/Versions/Current/Headers/SecKeychain.h

# Update a password without specifying a protocol type
print "Updating password for site.domain.com"
UpdatePassword(account_name, new_password, 'site.domain.com')

# Update the password for an HTTP proxy
print "Updating HTTP Proxy password"
UpdatePassword(account_name, new_password, 'webproxy.domain.com', 'htpx')

# Update the password for an HTTPS proxy
print "Updating HTTPS Proxy password"
UpdatePassword(account_name, new_password, 'webproxy.domain.com', 'htsx')

print "Done!"
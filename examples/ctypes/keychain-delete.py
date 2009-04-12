#!/usr/bin/env python
# encoding: utf-8
"""
Demonstrates how to delete a Keychain item using Python's ctypes library
"""

import ctypes

service_name     = 'Service Name'
account_name     = 'Account Name'
password_length  = ctypes.c_uint32(256)
password_pointer = ctypes.c_char_p()
item             = ctypes.c_char_p()

print "Loading Security.framework"
Security = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/Security.framework/Versions/Current/Security')

print "Searching for the password"

rc = Security.SecKeychainFindGenericPassword(
    None,
    len(service_name),
    service_name,
    len(account_name),
    account_name,
    # Used if you want to  retrieve the password:
    None, # ctypes.byref(password_length),
    None, # ctypes.pointer(password_pointer),
    ctypes.pointer(item)
)

if rc != 0:
    raise RuntimeError('SecKeychainFindGenericPassword failed: rc=%d' % rc)

print "Deleting Keychain item"

rc = Security.SecKeychainItemDelete( item )

if rc != 0:
    raise RuntimeError('SecKeychainItemDelete failed: rc=%d' % rc)


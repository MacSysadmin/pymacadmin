#!/usr/bin/env python2.5

from PyMacAdmin import carbon_call, load_carbon_framework
from PyMacAdmin.Security import kSecCertificateItemClass
from PyMacAdmin.Security.Keychain import SecKeychainAttribute, SecKeychainAttributeList

import sys
import ctypes
from CoreFoundation import CFRelease

Security = load_carbon_framework('/System/Library/Frameworks/Security.framework/Versions/Current/Security')

label    = "<some label text here>"
plabel   = ctypes.c_char_p(label)
tag      = 'labl'

attr     = SecKeychainAttribute(tag, 1, plabel)
attrList = SecKeychainAttributeList(1, attr)

# http://developer.apple.com/DOCUMENTATION/Security/Reference/keychainservices/Reference/reference.html#//apple_ref/c/tdef/SecItemClass

searchRef = ctypes.c_void_p()
itemRef   = ctypes.c_void_p()

try:
    Security.SecKeychainSearchCreateFromAttributes(
        None,
        kSecCertificateItemClass,
        ctypes.byref(attrList),
        ctypes.pointer(searchRef)
    )

    Security.SecKeychainSearchCopyNext(
        searchRef,
        ctypes.byref(itemRef)
    )

    if searchRef:
        CFRelease(searchRef)

    Security.SecKeychainItemDelete(itemRef)

    if itemRef:
        CFRelease(itemRef)
except RuntimeError, e:
    print >>sys.stderr, "ERROR: %s" % e
    sys.exit(1)
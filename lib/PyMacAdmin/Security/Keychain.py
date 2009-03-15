#!/usr/bin/env python
# encoding: utf-8
"""
Wrapper for the core Keychain API

Most of the internals are directly based on the native Keychain API. Apple's developer documentation is highly relevant:

http://developer.apple.com/documentation/Security/Reference/keychainservices/Reference/reference.html#//apple_ref/doc/uid/TP30000898-CH1-SW1
"""

import os
import ctypes
from PyMacAdmin import Security

class Keychain(object):
    """A friendlier wrapper for the Keychain API"""
    # TODO: Add support for SecKeychainSetUserInteractionAllowed

    def __init__(self, keychain_name=None):
        self.keychain_handle = self.open_keychain(keychain_name)

    def open_keychain(self, path=None):
        """Open a keychain file - if no path is provided, the user's default keychain will be used"""
        if not path:
            return None

        if path and not os.path.exists(path):
            raise IOError("Keychain %s does not exist" % path)

        keychain     = ctypes.c_void_p()
        keychain_ptr = ctypes.pointer(keychain)

        rc           = Security.lib.SecKeychainOpen(path, keychain_ptr)
        if rc != 0:
            raise RuntimeError("Couldn't open system keychain: rc=%d" % rc)

        return keychain

    def find_generic_password(self, service_name="", account_name=""):
        """Pythonic wrapper for SecKeychainFindGenericPassword"""
        item            = ctypes.c_void_p()
        password_length = ctypes.c_uint32(0)
        password_data   = ctypes.c_char_p(256)

        # For our purposes None and "" should be equivalent but we need a real
        # string for len() below:
        if not service_name:
            service_name = ""
        if not account_name:
            account_name = ""

        rc = Security.lib.SecKeychainFindGenericPassword (
            self.keychain_handle,
            len(service_name),                  # Length of service name
            service_name,                       # Service name
            len(account_name),                  # Account name length
            account_name,                       # Account name
            ctypes.byref(password_length),      # Will be filled with pw length
            ctypes.pointer(password_data),      # Will be filled with pw data
            ctypes.pointer(item)
        )

        if rc == -25300:
            raise KeyError('No keychain entry for generic password: service=%s, account=%s' % (service_name, account_name))
        elif rc != 0:
            raise RuntimeError('Unable to retrieve generic password (service=%s, account=%s): rc=%d' % (service_name, account_name, rc))

        password = password_data.value[0:password_length.value]

        Security.lib.SecKeychainItemFreeContent(None, password_data)

        return GenericPassword(service_name=service_name, account_name=account_name, password=password, keychain_item=item)

    def find_internet_password(self, account_name="", password="", server_name="", security_domain="", path="", port=0, protocol_type=None, authentication_type=None):
        """Pythonic wrapper for SecKeychainFindInternetPassword"""
        item            = ctypes.c_void_p()
        password_length = ctypes.c_uint32(0)
        password_data   = ctypes.c_char_p(256)

        if protocol_type and len(protocol_type) != 4:
            raise TypeError("protocol_type must be a valid FourCharCode - see http://developer.apple.com/documentation/Security/Reference/keychainservices/Reference/reference.html#//apple_ref/doc/c_ref/SecProtocolType")

        if authentication_type and len(authentication_type) != 4:
            raise TypeError("authentication_type must be a valid FourCharCode - see http://developer.apple.com/documentation/Security/Reference/keychainservices/Reference/reference.html#//apple_ref/doc/c_ref/SecAuthenticationType")

        if not isinstance(port, int):
            port = int(port)

        rc = Security.lib.SecKeychainFindInternetPassword (
            self.keychain_handle,
            len(server_name),
            server_name,
            len(security_domain) if security_domain else 0,
            security_domain,
            len(account_name),
            account_name,
            len(path),
            path,
            port,
            protocol_type,
            authentication_type,
            ctypes.byref(password_length),      # Will be filled with pw length
            ctypes.pointer(password_data),      # Will be filled with pw data
            ctypes.pointer(item)
        )

        if rc == -25300:
            raise KeyError('No keychain entry for internet password: server=%s, account=%s' % (server_name, account_name))
        elif rc != 0:
            raise RuntimeError('Unable to retrieve internet password (server=%s, account=%s): rc=%d' % (server_name, account_name, rc))

        password = password_data.value[0:password_length.value]

        Security.lib.SecKeychainItemFreeContent(None, password_data)

        return InternetPassword(server_name=server_name, account_name=account_name, password=password, keychain_item=item, security_domain=security_domain, path=path, port=port, protocol_type=protocol_type, authentication_type=authentication_type)

    def add(self, item):
        """Add the provided GenericPassword or InternetPassword object to this Keychain"""
        assert(isinstance(item, GenericPassword))

        item_ref = ctypes.c_void_p()

        if isinstance(item, InternetPassword):
            rc = Security.lib.SecKeychainAddInternetPassword(
                self.keychain_handle,
                len(item.server_name),
                item.server_name,
                len(item.security_domain),
                item.security_domain,
                len(item.account_name),
                item.account_name,
                len(item.path),
                item.path,
                item.port,
                item.protocol_type,
                item.authentication_type,
                len(item.password),
                item.password,
                ctypes.pointer(item_ref)
            )
        else:
            rc = Security.lib.SecKeychainAddGenericPassword(
                self.keychain_handle,
                len(item.service_name),
                item.service_name,
                len(item.account_name),
                item.account_name,
                len(item.password),
                item.password,
                ctypes.pointer(item_ref)
            )

        if rc != 0:
            raise RuntimeError("Error adding %s: rc=%d" % (item, rc))

        item.keychain_item = item_ref

    def remove(self, item):
        """Remove the provided keychain item as the reverse of Keychain.add()"""
        assert(isinstance(item, GenericPassword))
        item.delete()


class GenericPassword(object):
    """Generic keychain password used with SecKeychainAddGenericPassword and SecKeychainFindGenericPassword"""
    # TODO: Add support for access control and attributes
    # TODO: Add item name support

    account_name  = None
    service_name  = None
    password      = None
    keychain_item = None # An SecKeychainItemRef treated as an opaque object

    def __init__(self, **kwargs):
        super(GenericPassword, self).__init__()
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise AttributeError("Unknown property %s" % k)
            setattr(self, k, v)

    def update_password(self, new_password):
        """Change the stored password"""

        rc = Security.lib.SecKeychainItemModifyAttributesAndData(
            self.keychain_item,
            None,
            len(new_password),
            new_password
        )

        if rc == -61:
            raise RuntimeError("Permission denied updating %s" % self)
        elif rc != 0:
            raise RuntimeError("Unable to update password for %s: rc = %d" % rc)

    def delete(self):
        """Removes this item from the keychain"""
        rc = Security.lib.SecKeychainItemDelete(self.keychain_item)
        if rc != 0:
            raise RuntimeError("Unable to delete %s: rc=%d" % (self, rc))

        from CoreFoundation import CFRelease
        CFRelease(self.keychain_item)

        self.keychain_item = None
        self.service_name  = None
        self.account_name  = None
        self.password      = None

    def __str__(self):
        return repr(self)

    def __repr__(self):
        props = []
        for k in ['service_name', 'account_name']:
            props.append("%s=%s" % (k, repr(getattr(self, k))))

        return "%s(%s)" % (self.__class__.__name__, ", ".join(props))


class InternetPassword(GenericPassword):
    """Specialized keychain item for internet passwords used with SecKeychainAddInternetPassword and SecKeychainFindInternetPassword"""
    account_name        = ""
    password            = None
    keychain_item       = None
    server_name         = ""
    security_domain     = ""
    path                = ""
    port                = 0
    protocol_type       = None
    authentication_type = None

    def __init__(self, **kwargs):
        super(InternetPassword, self).__init__(**kwargs)

    def __repr__(self):
        props = []
        for k in ['account_name', 'server_name', 'security_domain', 'path', 'port', 'protocol_type', 'authentication_type']:
            if getattr(self, k):
                props.append("%s=%s" % (k, repr(getattr(self, k))))

        return "%s(%s)" % (self.__class__.__name__, ", ".join(props))

class SecKeychainAttribute(ctypes.Structure):
    """Contains keychain attributes

    tag:    A 4-byte attribute tag.
    length: The length of the buffer pointed to by data.
    data:   A pointer to the attribute data.
    """
    _fields_ = [
        ('tag',     ctypes.c_char_p),
        ('length',  ctypes.c_int32),
        ('data',    ctypes.c_char_p)
    ]

class SecKeychainAttributeList(ctypes.Structure):
    """Represents a list of keychain attributes

    count:  An unsigned 32-bit integer that represents the number of keychain attributes in the array.
    attr:   A pointer to the first keychain attribute in the array.
    """
    _fields_ = [
        ('count',   ctypes.c_uint),
        ('attr',    ctypes.POINTER(SecKeychainAttribute))
    ]

class SecKeychainAttributeInfo(ctypes.Structure):
    """Represents a keychain attribute as a pair of tag and format values.

    count:  The number of tag-format pairs in the respective arrays
    tag:    A pointer to the first attribute tag in the array
    format: A pointer to the first CSSM_DB_ATTRIBUTE_FORMAT in the array
    """
    _fields_ = [
        ('count',   ctypes.c_uint),
        ('tag',     ctypes.POINTER(ctypes.c_uint)),
        ('format',  ctypes.POINTER(ctypes.c_uint))
    ]

# The APIs expect pointers to SecKeychainAttributeInfo objects and we'd
# like to avoid having to manage memory manually:
SecKeychainAttributeInfo_p = ctypes.POINTER(SecKeychainAttributeInfo)
SecKeychainAttributeInfo_p.__del__ = lambda s: Security.lib.SecKeychainFreeAttributeInfo(s)


#!/usr/bin/python
"""Updates the password for an Airport network"""

import ctypes
import sys

SECURITY = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/Security.framework/Versions/Current/Security')

def find_airport_password(ssid):
    """Returns the password and a Keychain item reference for the requested Airport network"""
    item            = ctypes.c_char_p()
    password_length = ctypes.c_uint32(0)
    password_data   = ctypes.c_char_p(256)

    rc = SECURITY.SecKeychainFindGenericPassword (
        None,
        15,                                 # Length of service name below:
        "AirPort Network", 
        len(ssid),
        ssid,
        ctypes.byref(password_length),      # Will be filled with pw length
        ctypes.pointer(password_data),      # Will be filled with pw data
        ctypes.pointer(item)
    )

    if rc != 0:
        raise RuntimeError('No existing password for Airport network %s: rc=%d' % (ssid, rc))

    return (password_data.value[0:password_length.value], item)

def change_airport_password(ssid, new_password):
    """Sets the password for the specified Airport network to the provided value"""
    password, item = find_airport_password(ssid)
    
    if password != new_password:
        rc = SECURITY.SecKeychainItemModifyAttributesAndData(
            item, 
            None, 
            len(new_password), 
            new_password
        )

        if rc != 0:
            raise RuntimeError("Unable to update password for Airport network %s: rc = %d" % (ssid, rc))
    
def main():
    if len(sys.argv) < 3:
        print >> sys.stderr, "Usage: %s SSID NEW_PASSWORD" % (sys.argv[0])
        sys.exit(1)

    ssid, new_password = sys.argv[1:3]

    try:
        change_airport_password(ssid, new_password)
    except RuntimeError, exc:
        print >> sys.stderr, "Unable to change password for Airport network %s: %s" % ( ssid, exc)
        sys.exit(1)
        
    print "Changed password for Airport network %s to %s" % (ssid, new_password)
    
if __name__ == "__main__":
    main()
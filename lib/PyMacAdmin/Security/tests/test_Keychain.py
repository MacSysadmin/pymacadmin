#!/usr/bin/env python
# encoding: utf-8

import sys
import unittest
from PyMacAdmin.Security.Keychain import Keychain, GenericPassword, InternetPassword

class KeychainTests(unittest.TestCase):
    """Unit test for the Keychain module"""

    def setUp(self):
        pass

    def test_load_default_keychain(self):
        k = Keychain()
        self.failIfEqual(k, None)

    def test_load_system_keychain(self):
        k = Keychain('/Library/Keychains/System.keychain')
        self.failIfEqual(k, None)

    def test_find_airport_password(self):
        system_keychain = Keychain("/Library/Keychains/System.keychain")
        try:
            system_keychain.find_generic_password(account_name="linksys")
        except KeyError:
            print >> sys.stderr, "test_find_airport_password: assuming the non-existence of linksys SSID is correct"
            pass

    def test_find_nonexistent_generic_password(self):
        import uuid
        system_keychain = Keychain("/Library/Keychains/System.keychain")
        self.assertRaises(KeyError, system_keychain.find_generic_password, **{ 'account_name': "NonExistantGenericPassword-%s" % uuid.uuid4() })

    def test_add_and_remove_generic_password(self):
        import uuid
        k            = Keychain()
        service_name = "PyMacAdmin Keychain Unit Test"
        account_name = str(uuid.uuid4())
        password     = str(uuid.uuid4())

        i            = GenericPassword(service_name=service_name, account_name=account_name, password=password)

        k.add(i)

        self.assertEquals(i.password, k.find_generic_password(service_name, account_name).password)
 
        k.remove(i)
        self.assertRaises(KeyError, k.find_generic_password, **{"service_name": service_name, "account_name": account_name})

    def test_find_internet_password(self):
        keychain = Keychain()
        i = keychain.find_internet_password(server_name="connect.apple.com")
        self.failIfEqual(i, None)

    def test_add_and_remove_internet_password(self):
        import uuid
        k = Keychain()
        kwargs = {
            'server_name':         "pymacadmin.googlecode.com",
            'account_name':        "unittest",
            'protocol_type':       'http',
            'authentication_type': 'http',
            'password':            str(uuid.uuid4())
        }

        i = InternetPassword(**kwargs)
        k.add(i)

        self.assertEquals(i.password, k.find_internet_password(server_name=kwargs['server_name'], account_name=kwargs['account_name']).password)

        k.remove(i)
        self.assertRaises(KeyError, k.find_internet_password, **{"server_name": kwargs['server_name'], "account_name": kwargs['account_name']})


if __name__ == '__main__':
    unittest.main()


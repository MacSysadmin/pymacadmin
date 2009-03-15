# encoding: utf-8
import ctypes
import PyMacAdmin

# This is not particularly elegant but to avoid everything having to load the
# Security framework we use a single copy hanging of this module so everything
# else can simply use Security.lib.SecKeychainFoo(…)
lib = PyMacAdmin.load_carbon_framework('/System/Library/Frameworks/Security.framework/Versions/Current/Security')

# TODO: Expand this considerably?
CSSM_DB_RECORDTYPE_APP_DEFINED_START = 0x80000000
CSSM_DL_DB_RECORD_X509_CERTIFICATE   = CSSM_DB_RECORDTYPE_APP_DEFINED_START + 0x1000
kSecCertificateItemClass             = CSSM_DL_DB_RECORD_X509_CERTIFICATE
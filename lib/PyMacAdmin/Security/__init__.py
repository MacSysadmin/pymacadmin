# encoding: utf-8
import PyMacAdmin
import ctypes
import struct
import sys

# This is not particularly elegant but to avoid everything having to load the
# Security framework we use a single copy hanging of this module so everything
# else can simply use Security.lib.SecKeychainFoo(…)
lib = PyMacAdmin.load_carbon_framework('/System/Library/Frameworks/Security.framework/Versions/Current/Security')

CSSM_DB_RECORDTYPE_APP_DEFINED_START = 0x80000000
CSSM_DL_DB_RECORD_X509_CERTIFICATE   = CSSM_DB_RECORDTYPE_APP_DEFINED_START + 0x1000

# This is somewhat gross: we define a bunch of module-level constants based on
# the SecKeychainItem.h defines (FourCharCodes) by passing them through
# struct.unpack and converting them to ctypes.c_long() since we'll never use
# them for non-native APIs

CARBON_DEFINES = {
    'kSecCreationDateItemAttr':         'cdat',
    'kSecModDateItemAttr':              'mdat',
    'kSecDescriptionItemAttr':          'desc',
    'kSecCommentItemAttr':              'icmt',
    'kSecCreatorItemAttr':              'crtr',
    'kSecTypeItemAttr':                 'type',
    'kSecScriptCodeItemAttr':           'scrp',
    'kSecLabelItemAttr':                'labl',
    'kSecInvisibleItemAttr':            'invi',
    'kSecNegativeItemAttr':             'nega',
    'kSecCustomIconItemAttr':           'cusi',
    'kSecAccountItemAttr':              'acct',
    'kSecServiceItemAttr':              'svce',
    'kSecGenericItemAttr':              'gena',
    'kSecSecurityDomainItemAttr':       'sdmn',
    'kSecServerItemAttr':               'srvr',
    'kSecAuthenticationTypeItemAttr':   'atyp',
    'kSecPortItemAttr':                 'port',
    'kSecPathItemAttr':                 'path',
    'kSecVolumeItemAttr':               'vlme',
    'kSecAddressItemAttr':              'addr',
    'kSecSignatureItemAttr':            'ssig',
    'kSecProtocolItemAttr':             'ptcl',
    'kSecCertificateType':              'ctyp',
    'kSecCertificateEncoding':          'cenc',
    'kSecCrlType':                      'crtp',
    'kSecCrlEncoding':                  'crnc',
    'kSecAlias':                        'alis',
    'kSecInternetPasswordItemClass':    'inet',
    'kSecGenericPasswordItemClass':     'genp',
    'kSecAppleSharePasswordItemClass':  'ashp',
    'kSecCertificateItemClass':         CSSM_DL_DB_RECORD_X509_CERTIFICATE
}

for k in CARBON_DEFINES:
    v = CARBON_DEFINES[k]
    if isinstance(v, str):
        assert(len(v) == 4)
        v = ctypes.c_ulong(struct.unpack(">L", v)[0])
    setattr(sys.modules[__name__], k, v)
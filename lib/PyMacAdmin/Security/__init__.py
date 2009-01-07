# encoding: utf-8
import ctypes

# This is not particularly elegant but to avoid everything having to load the
# Security framework we use a single copy hanging of this module so everything
# else can simply use Security.lib.SecKeychainFoo(…)
lib = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/Security.framework/Versions/Current/Security')

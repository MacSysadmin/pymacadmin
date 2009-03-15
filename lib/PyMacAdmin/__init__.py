# -*- coding: utf-8 -*-

from functools import wraps
import ctypes

def mac_strerror(errno):
    """Returns an error string for a classic MacOS error return code"""
    # TODO: Find a replacement which isn't deprecated in Python 3000:
    try:
        import MacOS
        return MacOS.GetErrorString(errno)
    except ImportError:
        return "Unknown error %d: MacOS.GetErrorString is not available by this Python"

def carbon_errcheck(rc, func, args):
    if rc < 0:
        # TODO: Do we need to create a function which can safely check __name__
        # and handle non-existence? It should be set for anything using ctypes
        # and this shouldn't be useful otherwise
        # TODO: Create a custom exception which preserves the original rc value?
        raise RuntimeError("%s(%s) returned %d: %s" % (func.__name__, map(repr, args), rc, mac_strerror(rc)))
    return rc

def carbon_call(f, *args):
    """
    Wrapper for Carbon calls inspired by subprocess.check_call(): a negative
    rc will generate a RuntimeError with a [hopefully] informative message.
    """
    rc = f(*args)
    return carbon_errcheck(rc, f, args)

def load_carbon_framework(f_path):
    """
    Load a Carbon framework using ctypes.CDLL and add an errcheck wrapper to
    replace traditional errno-style error checks with exception handling.

    Example:
    >>> PyMacAdmin.load_carbon_framework('/System/Library/Frameworks/Security.framework/Versions/Current/Security')
    <CDLL '/System/Library/Frameworks/Security.framework/Versions/Current/Security', handle 318320 at 2515f0>
    """
    framework = ctypes.cdll.LoadLibrary(f_path)
    old_getitem = framework.__getitem__

    # TODO: Do we ever need to wrap framework.__getattr__ too?
    @wraps(old_getitem)
    def new_getitem(k):
        v = old_getitem(k)
        if hasattr(v, "errcheck") and not v.errcheck:
            v.errcheck = carbon_errcheck
        return v

    framework.__getitem__ = new_getitem

    return framework


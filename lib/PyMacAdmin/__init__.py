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

def checked_carbon_call(rc, func, args):
    """
        Call a carbon function and raise an exception when the return code is
        less than 0. This is intended for use with load_carbon_framework but
        can also be used as a standalone function similar to
        subprocess.check_call.

        Most errors will raise RuntimeError but the intent is to raise a more
        precise exception where applicable - e.g KeyError for
        errKCItemNotFound (returned when a Keychain query matches no items)
    """

    if rc < 0:
        if rc == -25300: #errKCItemNotFound
            exc_class = KeyError
        else:
            exc_class = RuntimeError

        raise exc_class("%s(%s) returned %d: %s" % (func.__name__, map(repr, args), rc, mac_strerror(rc)))
    return rc

def load_carbon_framework(f_path):
    """
    Load a Carbon framework using ctypes.CDLL and add an errcheck wrapper to
    replace traditional errno-style error checks with exception handling.

    Example:
    >>> load_carbon_framework('/System/Library/Frameworks/Security.framework/Versions/Current/Security') # doctest: +ELLIPSIS
    <CDLL '/System/Library/Frameworks/Security.framework/Versions/Current/Security', handle ... at ...>
    """
    framework = ctypes.cdll.LoadLibrary(f_path)

    # TODO: Do we ever need to wrap framework.__getattr__ too?
    old_getitem = framework.__getitem__
    @wraps(old_getitem)
    def new_getitem(k):
        v = old_getitem(k)
        if hasattr(v, "errcheck") and not v.errcheck:
            v.errcheck = checked_carbon_call
        return v
    framework.__getitem__ = new_getitem

    return framework


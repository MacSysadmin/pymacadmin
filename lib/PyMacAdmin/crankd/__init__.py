#!/usr/bin/env python
# encoding: utf-8

import sys

def not_implemented(*args, **kwargs):
    """A dummy function which exists only to catch configuration errors"""
    # TODO: Is there a better way to report the caller's location?
    import inspect
    stack = inspect.stack()
    my_name = stack[0][3]
    caller  = stack[1][3]
    raise NotImplementedError(
        "%s should have been overridden. Called by %s as: %s(%s)" % (
            my_name,
            caller,
            my_name,
            ", ".join(map(repr, args) + [ "%s=%s" % (k, repr(v)) for k,v in kwargs.items() ])
        )
    )

from . import handlers
sys.modules[handlers.__name__] = handlers
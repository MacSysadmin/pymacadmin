#!/usr/bin/env python
# encoding: utf-8
"""
Handlers for different types of events
"""

import sys
import os
import unittest
import logging
from Cocoa import NSObject
from .. import not_implemented

__all__ = [ 'BaseHandler', 'NSNotificationHandler' ]

class BaseHandler(object):
    # pylint: disable-msg=C0111,R0903
    pass

class NSNotificationHandler(NSObject):
    """Simple base class for handling NSNotification events"""
    # Method names and class structure are dictated by Cocoa & PyObjC, which
    # is substantially different from PEP-8:
    # pylint: disable-msg=C0103,W0232,R0903

    def init(self):
        """NSObject-compatible initializer"""
        self = super(NSNotificationHandler, self).init()
        if self is None: return None
        self.callable = not_implemented
        return self # NOTE: Unlike Python, NSObject's init() must return self!

    def onNotification_(self, the_notification):
        """Pass an NSNotifications to our handler"""
        if the_notification.userInfo:
            user_info = the_notification.userInfo()
        else:
            user_info = None
        self.callable(user_info=user_info) # pylint: disable-msg=E1101
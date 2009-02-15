from crankd import BaseHandler
import socket
import os
from PyMacAdmin.SCUtilities.SCPreferences import SCPreferences


class ProxyManager(BaseHandler):
    """
        crankd event handler which selectively enables a SOCKS process based
        on the current network address
    """

    def __init__(self):
        self.socks_server = 'localhost'
        self.socks_port   = '1080'

    def onNSWorkspaceDidMountNotification_(self, aNotification):
        """Helper which triggers network_changed simply by mounting a DMG"""
        self.network_changed()

    def network_changed(self, *args, **kwargs):
        # Open a SystemConfiguration preferences session:
        sc_prefs = SCPreferences()

        # We want to enable the server when our hostname is not on the corporate network:
        current_address = socket.gethostbyname(socket.getfqdn())
        new_state       = not current_address.startswith('128.36.')

        self.logger.info("Current address is now %s: SOCKS proxy will be %s" % (current_address, "Enabled" if new_state else "Disabled"))

        try:
            sc_prefs.set_proxy(enable=new_state, protocol='SOCKS', server=self.socks_server, port=self.socks_port)
            sc_prefs.save()
            os.system("killall ssh")
            self.logger.info("Successfully updated SOCKS proxy setting")
        except RuntimeError, e:
            self.logger.error("Unable to set SOCKS proxy setting: %s" % e.message)

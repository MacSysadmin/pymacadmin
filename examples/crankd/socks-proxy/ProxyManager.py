import socket
import os
import logging

from PyMacAdmin import crankd
from PyMacAdmin.SCUtilities.SCPreferences import SCPreferences

class ProxyManager(crankd.handlers.BaseHandler):
    """
        crankd event handler which selectively enables a SOCKS process based
        on the current network address
    """

    def __init__(self):
        super(crankd.handlers.BaseHandler, self).__init__()
        self.socks_server = 'localhost'
        self.socks_port   = '1080'

        # Fire once at startup to handle situations like system bootup or a
        # crankd restart:
        self.update_proxy_settings()

    def onNSWorkspaceDidMountNotification_(self, aNotification):
        """
        Dummy handler for testing purposes which calls the update code when a
        volume is mounted - this simplifies testing or demos using a DMG.

        BUG: Although harmless, this should be removed in production
        """
        self.update_proxy_settings()

    def update_proxy_settings(self, *args, **kwargs):
        """
        When the network configuration changes, this updates the SOCKS proxy
        settings based the current IP address(es)
        """
        # Open a SystemConfiguration preferences session:
        sc_prefs = SCPreferences()

        # We want to enable the server when our hostname is not on the corporate network:
        # BUG: This does not handle multi-homed systems well:
        current_address = socket.gethostbyname(socket.getfqdn())
        new_state       = not current_address.startswith('10.0.1.')

        logging.info(
            "Current address is now %s: SOCKS proxy will be %s" % (
                current_address,
                "Enabled" if new_state else "Disabled"
            )
        )

        try:
            sc_prefs.set_proxy(
                enable=new_state,
                protocol='SOCKS',
                server=self.socks_server,
                port=self.socks_port
            )
            sc_prefs.save()

            logging.info("Successfully updated SOCKS proxy setting")
        except RuntimeError, e:
            logging.error("Unable to set SOCKS proxy setting: %s" % e.message)

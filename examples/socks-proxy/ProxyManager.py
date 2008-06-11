from kicker_replacement import BaseHandler
import socket
from PyMacAdmin.SCUtilities.SCPreferences import SCPreferences

class ProxyManager(BaseHandler):
    def __init__(self):
        self.socks_server = 'localhost'
        self.socks_port   = '1080'

    def onNSWorkspaceDidMountNotification_(self, aNotification):        
        """A simple method which exists so this can be used for the workspace mount notification during testing"""
        return self.network_changed()
        
    def network_changed(self, *args, **kwargs):
		# Open a SystemConfiguration preferences session:	
        sc_prefs = SCPreferences()

        # We want to enable the server when our hostname is not on the corporate network:
        current_address = socket.gethostbyname(socket.getfqdn())
        new_state       = not current_address.startswith('198.207.70')

        self.logger.info("Current address is now %s: SOCKS proxy will be %s" % (current_address, "Enabled" if new_state else "Disabled"))

        try:
            sc_prefs.set_proxy(enable=new_state, protocol='SOCKS', server=self.socks_server, port=self.socks_port)
            sc_prefs.save()
            self.logger.info("Successfully updated SOCKS proxy setting")
        except RuntimeError, e:
          self.logger.error("Unable to set SOCKS proxy setting: %s" % e.message)
        

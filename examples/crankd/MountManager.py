from PyMacAdmin.crankd.handlers import BaseHandler

class MountManager(BaseHandler):
    def onNSWorkspaceDidMountNotification_(self, aNotification):
        path = aNotification.userInfo()['NSDevicePath']
        self.logger.info("Mount: %s" % path)

    def onNSWorkspaceDidUnmountNotification_(self, aNotification):
        path = aNotification.userInfo()['NSDevicePath']
        self.logger.info("Unmount: %s" % path)


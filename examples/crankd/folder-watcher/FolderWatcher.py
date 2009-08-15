import pprint

class FolderWatcher(object):
    def folder_changed(self, *args, **kwargs):
        print "Folder %(path)s changed" % kwargs

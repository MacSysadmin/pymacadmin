#!/usr/bin/env python
# encoding: utf-8
"""
Usage: crankd

Monitor system event notifications

Configuration:

The configuration file is divided into sections for each class of
events. Each section is a dictionary using the event condition as the
key ("NSWorkspaceDidWakeNotification", "State:/Network/Global/IPv4",
etc). Each event must have one of the following properties:

command:      a shell command
function:     the name of a python function
class:        the name of a python class which will be instantiated once
              and have methods called as events occur.
method:       (class, method) tuple

TODO: Cleanup use of global variables

Inspired by the PyObjC SystemConfiguration callback demos:
        <https://svn.red-bean.com/pyobjc/trunk/pyobjc/pyobjc-framework-SystemConfiguration/Examples/CallbackDemo/>
"""

__all__ = ['BaseHandler', 'do_shell']

from Cocoa import CFRunLoopAddSource, NSObject, NSWorkspace, NSRunLoop, kCFRunLoopCommonModes, CFRunLoopAddTimer, CFRunLoopTimerCreate, CFAbsoluteTimeGetCurrent
from SystemConfiguration import *
from FSEvents import *
import os, os.path
import logging, logging.handlers
import sys
from subprocess import call
from optparse import OptionParser
from plistlib import readPlist, writePlist
from PyObjCTools import AppHelper
from functools import partial
import signal
from datetime import datetime

HANDLER_OBJECTS  = dict()     # Events which have a "class" handler use an instantiated object; we want to load only one copy
SC_HANDLERS      = dict()     # Callbacks indexed by SystemConfiguration keys
FS_WATCHED_FILES = dict()     # Callbacks indexed by filesystem path

class BaseHandler(object):
    """A base class from which event handlers can inherit things like the system logger"""
    options = {}
    logger  = logging.getLogger()

def get_callable_for_event(name, config, context=None):
    """
        Returns a callable object which can be used as a callback for any
        event. The returned function has context information, logging, etc.
        included so they do not need to be passed when the actual event
        occurs.

        NOTE: This function does not process "class" handlers - by design they
        are passed to the system libraries which expect a delegate object with
        various event handling methods
    """
    
    kwargs = {
        'context':  context,
        'key':      name,
        'logger':   logging.getLogger(),
        'config':   config,
        'options':  options
    }
    
    if "command" in config:
        f = partial(do_shell, config["command"], **kwargs)
    elif "function" in config:
        f = partial(get_callable_from_string(config["function"]), **kwargs)
    elif "method" in config:
        f = partial(getattr(get_handler_object(config['method'][0]), config['method'][1]), **kwargs)
    else:
        raise AttributeError("%s have a class, method, function or command" % name)
    
    return f

def get_mod_func(callback):
    """Convert a fully-qualified module.function name to (module, function) - stolen from Django"""
    try:
        dot = callback.rindex('.')
    except ValueError:
        return (callback, '')
    return (callback[:dot], callback[dot+1:])

def get_callable_from_string(f_name):
    """Takes a string containing a function name (optionally module qualified) and returns a callable object"""
    try:
        mod_name, func_name = get_mod_func(f_name)
        if mod_name == "" and func_name == "":
            raise AttributeError("%s couldn't be converted to a module or function name" % f_name)
        
        module = __import__(mod_name)
        
        if func_name == "":
            func_name = mod_name # The common case is an eponymous class
        
        return getattr(module, func_name)
    
    except (ImportError, AttributeError), exc:
        raise RuntimeError("Unable to create a callable object for '%s': %s" % (f_name, exc))

def get_handler_object(class_name):
    """Return a single instance of the given class name, instantiating it if necessary"""
    global HANDLER_OBJECTS
    
    if class_name not in HANDLER_OBJECTS:
        h_obj = get_callable_from_string(class_name)()
        if isinstance(h_obj, BaseHandler):
            h_obj.logger  = logging.getLogger()
            h_obj.options = options
        HANDLER_OBJECTS[class_name] = h_obj
    
    return HANDLER_OBJECTS[class_name]

def handle_sc_event(store, changedKeys, info):
    for key in changedKeys:
        SC_HANDLERS[key](key=key, info=info)

def list_events(option, opt_str, value, parser):
    """Displays the list of events which can be monitored on the current system"""
    
    print 'On this system SystemConfiguration supports these events:'
    for event in sorted(SCDynamicStoreCopyKeyList(get_sc_store(), '.*')):
        print "\t", event
    
    print
    print "Standard NSWorkspace Notification messages:\n\t",
    print "\n\t".join('''
        NSWorkspaceDidLaunchApplicationNotification
        NSWorkspaceDidMountNotification
        NSWorkspaceDidPerformFileOperationNotification
        NSWorkspaceDidTerminateApplicationNotification
        NSWorkspaceDidUnmountNotification
        NSWorkspaceDidWakeNotification
        NSWorkspaceSessionDidBecomeActiveNotification
        NSWorkspaceSessionDidResignActiveNotification
        NSWorkspaceWillLaunchApplicationNotification
        NSWorkspaceWillPowerOffNotification
        NSWorkspaceWillSleepNotification
        NSWorkspaceWillUnmountNotification
    '''.split())
    
    sys.exit(0)

def parse_options():
    parser          = OptionParser(__doc__.strip())
    support_path    = '/Library/' if os.getuid() == 0 else os.path.expanduser('~/Library/')
    preference_file = os.path.join(support_path, 'Preferences', 'com.googlecode.pymacadmin.crankd.plist')
    module_path     = os.path.join(support_path, 'Application Support/crankd')
    
    if os.path.exists(module_path):
        sys.path.append(module_path)
    else:
        print >>sys.stderr, "Module directory %s does not exist: Python handlers will need to use absolute pathnames" % module_path
    
    parser.add_option("-f", "--config", dest="config_file", help='Use an alternate config file instead of %default', default=preference_file)
    parser.add_option("-l", "--list-events", action="callback", callback=list_events, help="List the events which can be monitored")
    (options, args) = parser.parse_args()
    
    if len(args):
        print >>sys.stderr, "Unknown command-line arguments:", args
        sys.exit(1)
    
    options.support_path = support_path
    
    return options

def load_config(options):
    if not os.path.exists(options.config_file):
        print 'Creating %s with default options for you to customize' % options.config_file
        print '%s --list-events will list the events you can monitor on this system' % sys.argv[0]
        example_config = {
            'SystemConfiguration': {
                'State:/Network/Global/IPv4': {
                    'command': '/bin/echo "Global IPv4 config changed"'
                }
            },
            'NSWorkspace': {
                'NSWorkspaceDidMountNotification': {
                    'command': '/bin/echo "A new volume was mounted!"'
                },
                'NSWorkspaceDidWakeNotification': {
                    'command': '/bin/echo "The system woke from sleep!"'
                },
                'NSWorkspaceWillSleepNotification': {
                    'command': '/bin/echo "The system is about to go to sleep!"'
                }
            }
        }
        writePlist(example_config, options.config_file)
        sys.exit(1)
    
    plist = readPlist(options.config_file)
    
    if "imports" in plist:
        for module in plist['imports']:
            try:
                __import__(module)
            except ImportError, exc:
                print >>sys.stderr, "Unable to import %s: %s" % (module, exc)
                sys.exit(1)
    return plist

def configure_logging():
    default_level = logging.DEBUG if sys.stdin.isatty() else logging.INFO
    logging.basicConfig(level=default_level, format='%(levelname)s: %(message)s')
    # Normally this would not be necessary but logging assumes syslog listens on
    # localhost syslog/udp, which is disabled on 10.5 (rdar://5871746)
    syslog = logging.handlers.SysLogHandler('/var/run/syslog')
    syslog.setFormatter(logging.Formatter('%(name)s: %(message)s'))
    syslog.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(syslog)


def get_sc_store():
    """Returns an SCDynamicStore instance"""
    return SCDynamicStoreCreate(None, "crankd", handle_sc_event, None)

def add_workspace_notifications(nsw_config):
    # See http://developer.apple.com/documentation/Cocoa/Conceptual/Workspace/Workspace.html
    notification_center = NSWorkspace.sharedWorkspace().notificationCenter()
    
    class NotificationHandler(NSObject):
        def __init__(self):
            self.callable = compile('raise NotImplementedError("No callable provided!")')
        
        def onNotification_(self, aNotification):
            if aNotification.userInfo:
                user_info = aNotification.userInfo()
            else:
                user_info = None
            self.callable(user_info=user_info)
    
    
    for event in nsw_config:
        event_config = nsw_config[event]
        
        if "class" in event_config:
            obj         = get_handler_object(event_config['class'])
            objc_method = "on%s:" % event
            py_method   = objc_method.replace(":", "_")
            if not hasattr(obj, py_method) or not callable(getattr(obj, py_method)):
                print >>sys.stderr, \
                    "NSWorkspace Notification %s: handler class %s must define a %s method" % (event, event_config['class'], py_method)
                sys.exit(1)
            
            notification_center.addObserver_selector_name_object_(obj, objc_method, event, None)
        else:
            handler          = NotificationHandler.new()
            handler.name     = "NSWorkspace Notification %s" % event
            handler.callable = get_callable_for_event(event, event_config, context=handler.name)
            
            assert(callable(handler.onNotification_))
            
            notification_center.addObserver_selector_name_object_(handler, "onNotification:", event, None)
    
    logging.info("Listening for these NSWorkspace notifications: %s" % ', '.join(nsw_config.keys()))

def add_sc_notifications(sc_config):
    """
    This uses the SystemConfiguration framework to get a SCDynamicStore session
    and register for certain events. See the Apple SystemConfiguration
    documentation for details:
    
    <http://developer.apple.com/documentation/Networking/Reference/SysConfig/SCDynamicStore/CompositePage.html>
    
    TN1145 may also be of interest:
        <http://developer.apple.com/technotes/tn/tn1145.html>
    """
    
    keys = sc_config.keys()
    
    try:
        for key in keys:
            SC_HANDLERS[key] = get_callable_for_event(key, sc_config[key], context="SystemConfiguration: %s" % key)
    except AttributeError, e:
        print >>sys.stderr, "Error configuring SystemConfiguration events:", e
        sys.exit(1)
    
    store = get_sc_store()
    
    SCDynamicStoreSetNotificationKeys(store, None, keys)
    
    # Get a CFRunLoopSource for our store session and add it to the application's runloop:
    CFRunLoopAddSource(
        NSRunLoop.currentRunLoop().getCFRunLoop(), 
        SCDynamicStoreCreateRunLoopSource(None, store, 0), 
        kCFRunLoopCommonModes
    )
    
    logging.info("Listening for these SystemConfiguration events: %s" % ', '.join(keys))

def add_fs_notifications(fs_config):
    for path in fs_config:
        add_fs_notification(path, get_callable_for_event(path, fs_config[p], context="FSEvent: %s" % path))

def add_fs_notification(f_path, callback):
    """Adds an FSEvent notification for the specified path"""
    path = os.path.realpath(os.path.expanduser(f_path))
    if not os.path.exists(path):
        raise AttributeError("Cannot add an FSEvent notification: %s does not exist!" % path)
    
    if not os.path.isdir(path):
        path = os.path.dirname(path)
    
    try:
        FS_WATCHED_FILES[path].append(callback)
    except KeyError:
        FS_WATCHED_FILES[path] = [callback]

def start_fs_events():
    # TODO: Comment the FSEventStreamCreate() parameter list:
    streamRef = FSEventStreamCreate(
        None, # BUG: kCFAllocatorDefault?
        fsevent_callback, 
        None, 
        FS_WATCHED_FILES.keys(), 
        kFSEventStreamEventIdSinceNow, 
        1.0, 
        0
    )
    
    if not streamRef:
        raise RuntimeError("FSEventStreamCreate() failed!")
    
    FSEventStreamScheduleWithRunLoop(streamRef, NSRunLoop.currentRunLoop().getCFRunLoop(), kCFRunLoopDefaultMode)
    
    if not FSEventStreamStart(streamRef):
        raise RuntimeError("Unable to start FSEvent stream!")
    
    logging.debug("FSEventStream started for %d paths: %s" % (len(FS_WATCHED_FILES), ", ".join(FS_WATCHED_FILES)))

def fsevent_callback(streamRef, full_path, event_count, paths, masks, ids):
    for i in range(event_count):
        path = os.path.dirname(paths[i])
        
        if masks[i] & kFSEventStreamEventFlagMustScanSubDirs:
            recursive = True
        
        if masks[i] & kFSEventStreamEventFlagUserDropped:
            logging.error("We were too slow processing FSEvents and some events were dropped")
            recursive = True
        
        if masks[i] & kFSEventStreamEventFlagKernelDropped:
            logging.error("The kernel was too slow processing FSEvents and some events were dropped!")
            recursive = True
        else:
            recursive = False
        
        for p in [k for k in FS_WATCHED_FILES if path.startswith(k)]:
            logging.debug("FSEvent: %s: processing %d callback(s) for path %s" % (p, len(FS_WATCHED_FILES[p]), path))
            for c in FS_WATCHED_FILES[p]:
                c(p, path=path, recursive=recursive)

def timer_callback(*args):
    logging.debug("timer callback at %s" % datetime.now())

def main():
    global config, options
    
    options     = parse_options()
    sys.argv[0] = os.path.realpath(sys.argv[0])
    config      = load_config(options)
    
    configure_logging()
    
    if "NSWorkspace" in config:
        add_workspace_notifications(config['NSWorkspace'])
    
    if "SystemConfiguration" in config:
        add_sc_notifications(config['SystemConfiguration'])
    
    if "FSEvents" in config:
        add_fs_notifications(config['FSEvents'])
    
    # We reuse our FSEvents code to watch for changes to our files and
    # restart:
    add_conditional_restart(options.config_file, "Configuration file %s changed" % options.config_file)
    for (m_name,m_file) in [(k,v) for k,v in sys.modules.iteritems() if hasattr(v, '__file__')]:
        add_conditional_restart(m_file.__file__, "Module %s was updated" % m_name)
    
    signal.signal(signal.SIGHUP, partial(restart, "SIGHUP received"))
    
    start_fs_events()
    
    # NOTE: This timer is basically a kludge around the fact that we can't reliably get
    #       signals or Control-C inside a runloop. This wakes us up often enough to
    #       appear tolerably responsive:
    CFRunLoopAddTimer(
        NSRunLoop.currentRunLoop().getCFRunLoop(),
        CFRunLoopTimerCreate(None, CFAbsoluteTimeGetCurrent(), 5.0, 0, 0, timer_callback, None),
        kCFRunLoopCommonModes
    )
    
    try:
        AppHelper.runConsoleEventLoop(installInterrupt=True)
    except KeyboardInterrupt, e:
        logging.info("KeyboardInterrupt received, exiting")
    
    sys.exit(0)

def do_shell(command, context=None, **kwargs):
    """Executes a shell command with logging"""
    logging.info("%s: executing %s" % (context, command))
    
    child_env = {'context':context}
    for k in kwargs:
        if callable(kwargs[k]):
            continue
        elif hasattr(kwargs[k], 'keys') and callable(kwargs[k].keys):
            child_env.update(kwargs[k])
        else:
            child_env[k] = str(kwargs[k])
    
    try:
        rc = call(command, shell=True, env=child_env)
        if rc == 0:
            logging.debug("%s returned %d" % (command, rc))
        elif rc < 0:
            logging.error("%s was terminated by signal %d" % (command, -rc))
        else:
            logging.error("%s returned %d" % (command, rc))
    except OSError, e:
        logging.error("Got an exception when executing %s:" % (command, e))

def add_conditional_restart(file, reason):
    """FSEvents monitors directories, not files. This function uses stat to restart only if the file's mtime has changed"""
    file = os.path.realpath(file)
    while not os.path.exists(file):
      file = os.path.dirname(file)
    orig_stat = os.stat(file).st_mtime
    
    def cond_restart(*args, **kwargs):
        try:
            if os.stat(file).st_mtime != orig_stat:
                restart(reason)
        except Exception, e:
            restart("Exception while checking %s: %s" % (file, e))
    
    add_fs_notification(file, cond_restart)

def restart(reason, *args, **kwargs):
    logging.info("Restarting: %s" % reason)
    os.execv(sys.argv[0], sys.argv)

if __name__ == '__main__':
    main()

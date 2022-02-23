#!/usr/bin/env python3
# encoding: utf-8
"""Monitor system event notifications.

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
"""

import signal
import sys

import Cocoa
import datetime
import FSEvents
import functools
import inspect
import logging
import logging.handlers
import objc
import optparse
import os
import os.path
import plistlib
from PyObjCTools import AppHelper
import re
import subprocess
import SystemConfiguration

VERSION = "$Revision: #4 $"

# Events which have a "class" handler use an instantiated object; we want to
# load only one copy
HANDLER_OBJECTS = dict()
# Callbacks indexed by SystemConfiguration keys
SC_HANDLERS = dict()
# Callbacks indexed by filesystem path
FS_WATCHED_FILES = dict()
# handlers for workspace events
WORKSPACE_HANDLERS = dict()

CRANKD_OPTIONS = None
CRANKD_CONFIG = None


class BaseHandler(object):
  # pylint: disable=C0111,R0903
  pass


class NotificationHandler(Cocoa.NSObject):
  """Simple base class for handling NSNotification events."""

  # Method names and class structure are dictated by Cocoa & PyObjC, which
  # is substantially different from PEP-8:
  # pylint: disable=C0103,W0232,R0903

  def init(self):
    """NSObject-compatible initializer."""
    self = objc.super(NotificationHandler, self).init()
    if self is None:
      return None
    self.callable = self.not_implemented
    return self  # NOTE: Unlike Python, NSObject's init() must return self!

  def not_implemented(self, *args, **kwargs):
    """A dummy function which exists only to catch configuration errors."""
    stack = inspect.stack()
    my_name = stack[0][3]
    caller = stack[1][3]
    raise NotImplementedError(
        "%s should have been overridden. Called by %s as: %s(%s)" %
        (my_name, caller, my_name, ", ".join(
            list(map(repr, args)) +
            ["%s=%s" % (k, repr(v)) for k, v in kwargs.items()])))

  def onNotification_(self, the_notification):
    """Pass an NSNotifications to our handler."""
    if the_notification.userInfo:
      user_info = the_notification.userInfo()
    else:
      user_info = None
    self.callable(user_info=user_info)  # pylint: disable=E1101


def log_list(msg, items, level=logging.INFO):
  """Record a a list of values with a message.

  This would ordinarily be a simple logging call but we want to keep the
  length below the 1024-byte syslog() limitation and we'll format things
  nicely by repeating our message with as many of the values as will fit.

  Individual items longer than the maximum length will be truncated.

  Args:
    msg: str, message to be logged
    items: list, items to log
    level: optional logger level
  """
  max_len = 1024 - len(msg % "")
  cur_len = 0
  cur_items = list()

  while [i[:max_len] for i in items]:
    i = items.pop()
    if cur_len + len(i) + 2 > max_len:
      logging.info(msg, ", ".join(cur_items))
      cur_len = 0
      cur_items = list()

    cur_items.append(i)
    cur_len += len(i) + 2

  logging.log(level, msg, ", ".join(cur_items))


def get_callable_for_event(name, event_config, context=None):
  """Returns a callable object which can be used as a callback for any event.

  The returned function has context information, logging, etc.
  included so they do not need to be passed when the actual event
  occurs.

  NOTE: This function does not process "class" handlers - by design they
  are passed to the system libraries which expect a delegate object with
  various event handling methods

  Args:
    name: str
    event_config: str, type of event
    context: optional context

  Returns:
    A callable object for use as a callback
  Raises:
    AttributeError: if name is missing a required attribute
  """

  kwargs = {
      "context": context,
      "key": name,
      "config": event_config,
  }

  if "command" in event_config:
    f = functools.partial(do_shell, event_config["command"], **kwargs)
  elif "function" in event_config:
    f = functools.partial(
        get_callable_from_string(event_config["function"]), **kwargs)
  elif "method" in event_config:
    f = functools.partial(
        getattr(
            get_handler_object(event_config["method"][0]),
            event_config["method"][1]), **kwargs)
  else:
    raise AttributeError("%s must have a class, method, function or command" %
                         name)

  return f


def get_mod_func(callback):
  """Convert a fully-qualified module.function name to (module, function)."""
  try:
    dot = callback.rindex(".")
  except ValueError:
    return (callback, "")
  return (callback[:dot], callback[dot + 1:])


def get_callable_from_string(f_name):
  """Takes a function name and returns a callable object."""
  try:
    mod_name, func_name = get_mod_func(f_name)
    if not mod_name and not func_name:
      raise AttributeError(
          "%s couldn't be converted to a module or function name" % f_name)

    module = __import__(mod_name)

    if not func_name:
      func_name = mod_name  # The common case is an eponymous class

    return getattr(module, func_name)

  except (ImportError, AttributeError) as exc:
    raise RuntimeError("Unable to create a callable object for '%s': %s" %
                       (f_name, exc))


def get_handler_object(class_name):
  """Return a single instance of class_name, instantiating it if necessary."""

  if class_name not in HANDLER_OBJECTS:
    h_obj = get_callable_from_string(class_name)()
    if isinstance(h_obj, BaseHandler):
      pass  # TODO(anyone): Do we even need BaseHandler any more?
    HANDLER_OBJECTS[class_name] = h_obj

  return HANDLER_OBJECTS[class_name]


def handle_sc_event(unused_store, changed_keys, info):
  """Fire every event handler for one or more events."""
  try:
    for key in changed_keys:
      SC_HANDLERS[key](key=key, info=info)
  except KeyError:
    # If there's no exact match, go through the list again assuming regex
    for key in changed_keys:
      for handler in SC_HANDLERS:
        if re.match(handler, key):
          SC_HANDLERS[handler](key=key, info=info)


def list_events(*_):
  """Displays list of events which can be monitored on the current system."""

  print("On this system SystemConfiguration supports these events:")
  for event in sorted(
      SystemConfiguration.SCDynamicStoreCopyKeyList(get_sc_store(), ".*")):
    print("\t", event)

  print()
  print("Standard NSWorkspace Notification messages:\n\t", end=" ")
  print("\n\t".join("""
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
    """.split()))

  sys.exit(0)


def process_commandline():
  """Process command-line options, load prefs, configure module path."""
  parser = optparse.OptionParser(__doc__.strip())
  if os.getuid() == 0:
    support_path = "/Library/"
  else:
    support_path = os.path.expanduser("~/Library/")
  preference_file = os.path.join(support_path, "Preferences",
                                 "com.googlecode.pymacadmin.crankd.plist")
  module_path = os.path.join(support_path, "Application Support/crankd")

  if os.path.exists(module_path):
    sys.path.append(module_path)
  else:
    print(
        "Module directory %s does not exist: "
        "Python handlers will need to use absolute pathnames" % module_path,
        file=sys.stderr)

  parser.add_option(
      "-f",
      "--config",
      dest="config_file",
      help="Use an alternate config file instead of %default",
      default=preference_file)
  parser.add_option(
      "-l",
      "--list-events",
      action="callback",
      callback=list_events,
      help="List the events which can be monitored")
  parser.add_option(
      "-d",
      "--debug",
      action="count",
      default=False,
      help="Log detailed progress information")
  (options, args) = parser.parse_args()

  if args:
    parser.error("Unknown command-line arguments: %s" % args)

  options.support_path = support_path
  options.config_file = os.path.realpath(options.config_file)

  # This is somewhat messy but we want to alter the command-line to use full
  # file paths in case someone's code changes the current directory or the
  sys.argv = [
      os.path.realpath(sys.argv[0]),
  ]

  if options.debug:
    logging.getLogger().setLevel(logging.DEBUG)
    sys.argv.append("--debug")

  if options.config_file:
    sys.argv.append("--config")
    sys.argv.append(options.config_file)

  return options


def load_config(options):
  """Load our configuration from plist or create if none exists."""
  if not os.path.exists(options.config_file):
    logging.info(
        "%s does not exist - initializing with an example configuration",
        CRANKD_OPTIONS.config_file)
    print(
        "Creating %s with default options for you to customize" %
        options.config_file,
        file=sys.stderr)
    print(
        "%s --list-events will list the events you can monitor on this system" %
        sys.argv[0],
        file=sys.stderr)
    example_config = {
        "SystemConfiguration": {
            "State:/Network/Global/IPv4": {
                "command": '/bin/echo "Global IPv4 config changed"'
            }
        },
        "NSWorkspace": {
            "NSWorkspaceDidMountNotification": {
                "command": '/bin/echo "A new volume was mounted!"'
            },
            "NSWorkspaceDidWakeNotification": {
                "command": '/bin/echo "The system woke from sleep!"'
            },
            "NSWorkspaceWillSleepNotification": {
                "command": '/bin/echo "The system is about to go to sleep!"'
            }
        }
    }
    try:
      with open(options.config_file, "wb") as f:
        plistlib.dump(example_config, f)
    except (TypeError, OSError) as e:
      logging.error("Could not write %s: %s", options.config_file, str(e))
      sys.exit(1)

  logging.info("Loading configuration from %s", CRANKD_OPTIONS.config_file)

  try:
    with open(options.config_file, "rb") as f:
      plist = plistlib.load(f)
  except (TypeError, OSError) as e:
    logging.error("Could not read %s: %s", options.config_file, str(e))
    sys.exit(1)

  if "imports" in plist:
    for module in plist["imports"]:
      try:
        __import__(module)
      except ImportError as exc:
        print("Unable to import %s: %s" % (module, exc), file=sys.stderr)
        sys.exit(1)
  return plist


def configure_logging():
  """Configures the logging module."""
  logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

  # Enable logging to syslog as well:
  # Normally this would not be necessary but logging assumes syslog listens on
  # localhost syslog/udp, which is disabled on 10.5 (rdar://5871746)
  syslog = logging.handlers.SysLogHandler("/var/run/syslog")
  syslog.setFormatter(
      logging.Formatter("%(pathname)s[%(process)d]:%(message)s"))
  syslog.setLevel(logging.INFO)
  logging.getLogger().addHandler(syslog)


def get_sc_store():
  """Returns an SCDynamicStore instance."""
  return SystemConfiguration.SCDynamicStoreCreate(None, "crankd",
                                                  handle_sc_event, None)


def add_workspace_notifications(nsw_config):
  """Add workspace notifications."""
  notification_center = Cocoa.NSWorkspace.sharedWorkspace().notificationCenter()

  for event in nsw_config:
    event_config = nsw_config[event]

    if "class" in event_config:
      obj = get_handler_object(event_config["class"])
      objc_method = "on%s:" % event
      py_method = objc_method.replace(":", "_")
      if not hasattr(obj, py_method) or not callable(getattr(obj, py_method)):
        print(
            "NSWorkspace Notification %s: "
            "handler class %s must define a %s method" %
            (event, event_config["class"], py_method),
            file=sys.stderr)
        sys.exit(1)

      notification_center.addObserver_selector_name_object_(
          obj, objc_method, event, None)
    else:
      handler = NotificationHandler.new()
      handler.name = "NSWorkspace Notification %s" % event
      handler.callable = get_callable_for_event(
          event, event_config, context=handler.name)

      assert callable(handler.onNotification_)

      notification_center.addObserver_selector_name_object_(
          handler, "onNotification:", event, None)
      WORKSPACE_HANDLERS[event] = handler
  log_list("Listening for these NSWorkspace notifications: %s",
           list(nsw_config.keys()))


def add_sc_notifications(sc_config):
  """Get SCDynamicStore session and register for events.

  This uses the SystemConfiguration framework to get a SCDynamicStore session
  and register for certain events. See the Apple SystemConfiguration
  documentation for details:

  <http://developer.apple.com/documentation/Networking/Reference/SysConfig/SCDynamicStore/CompositePage.html>

  TN1145 may also be of interest:
      <http://developer.apple.com/technotes/tn/tn1145.html>

  Inspired by the PyObjC SystemConfiguration callback demos:
  <https://svn.red-bean.com/pyobjc/trunk/pyobjc/pyobjc-framework-SystemConfiguration/Examples/CallbackDemo/>

  Args:
    sc_config: dict
  """

  keys = list(sc_config.keys())

  try:
    for key in keys:
      SC_HANDLERS[key] = get_callable_for_event(
          key, sc_config[key], context="SystemConfiguration: %s" % key)
  except AttributeError as exc:
    print(
        "Error configuring SystemConfiguration events: %s" % exc,
        file=sys.stderr)
    sys.exit(1)

  store = get_sc_store()

  SystemConfiguration.SCDynamicStoreSetNotificationKeys(store, None, keys)

  # Get a CFRunLoopSource and add it to the application's runloop:
  Cocoa.CFRunLoopAddSource(
      Cocoa.NSRunLoop.currentRunLoop().getCFRunLoop(),
      SystemConfiguration.SCDynamicStoreCreateRunLoopSource(None, store, 0),
      Cocoa.kCFRunLoopCommonModes)

  log_list("Listening for these SystemConfiguration events: %s", keys)


def add_fs_notifications(fs_config):
  for path in fs_config:
    add_fs_notification(
        path,
        get_callable_for_event(
            path, fs_config[path], context="FSEvent: %s" % path))


def add_fs_notification(f_path, callback):
  """Adds an FSEvent notification for the specified path."""
  path = os.path.realpath(os.path.expanduser(f_path))
  if not os.path.exists(path):
    raise AttributeError(
        "Cannot add an FSEvent notification: %s does not exist!" % path)

  if not os.path.isdir(path):
    path = os.path.dirname(path)

  try:
    FS_WATCHED_FILES[path].append(callback)
  except KeyError:
    FS_WATCHED_FILES[path] = [callback]


def start_fs_events():
  """Start FSEevents stream."""
  stream_ref = FSEvents.FSEventStreamCreate(
      None,  # Use the default Cocoa.CFAllocator
      fsevent_callback,
      None,  # We don't need a FSEventStreamContext
      list([str(f) for f in FS_WATCHED_FILES.keys()]),
      FSEvents.kFSEventStreamEventIdSinceNow,  # Only events in the future
      1.0,  # Process events within 1 second
      0  # We don't need any special flags for our stream
  )

  if not stream_ref:
    raise RuntimeError("FSEventStreamCreate() failed!")

  FSEvents.FSEventStreamScheduleWithRunLoop(
      stream_ref,
      Cocoa.NSRunLoop.currentRunLoop().getCFRunLoop(),
      Cocoa.kCFRunLoopDefaultMode)

  if not FSEvents.FSEventStreamStart(stream_ref):
    raise RuntimeError("Unable to start FSEvent stream!")

  logging.debug("FSEventStream started for %d paths: %s", len(FS_WATCHED_FILES),
                b", ".join(FS_WATCHED_FILES))


def fsevent_callback(unused_stream_ref, unused_full_path, event_count, paths,
                     masks, unused_ids):
  """Process an FSEvent and call each handler for that path or parent."""
  for i in list(range(event_count)):
    path = os.path.dirname(paths[i])

    if masks[i] & FSEvents.kFSEventStreamEventFlagMustScanSubDirs:
      recursive = True

    if masks[i] & FSEvents.kFSEventStreamEventFlagUserDropped:
      logging.error(
          "We were too slow processing FSEvents and some events were dropped")
      recursive = True

    if masks[i] & FSEvents.kFSEventStreamEventFlagKernelDropped:
      logging.error("The kernel was too slow processing FSEvents "
                    "and some events were dropped!")
      recursive = True
    else:
      recursive = False

    for j in [k for k in FS_WATCHED_FILES if path.startswith(k)]:
      logging.debug("FSEvent: %s: processing %d callback(s) for path %s", j,
                    len(FS_WATCHED_FILES[j]), path)
      for l in FS_WATCHED_FILES[j]:
        l(j, path=path, recursive=recursive)


def timer_callback(*unused_args):
  """Handles the timer events.

  We use this to have the runloop run regularly. Currently this logs a
  timestamp for debugging purposes.
  """
  logging.debug("timer callback at %s", datetime.datetime.now())


def create_env_name(name):
  """Converts input names into more traditional shell environment name style.

  >>> create_env_name("NSApplicationBundleIdentifier")
  'NSAPPLICATION_BUNDLE_IDENTIFIER'
  >>> create_env_name("NSApplicationBundleIdentifier-1234$foobar!")
  'NSAPPLICATION_BUNDLE_IDENTIFIER_1234_FOOBAR'

  Args:
    name: str, name to convert

  Returns:
    str, converted name
  """
  new_name = re.sub(r"""(?<=[a-z])([A-Z])""", "_\\1", name)
  new_name = re.sub(r"\W+", "_", new_name)
  new_name = re.sub(r"_{2,}", "_", new_name)
  return new_name.upper().strip("_")


def do_shell(command, context=None, **kwargs):
  """Executes a shell command with logging."""
  logging.info("%s: executing %s", context, command)

  child_env = {"CRANKD_CONTEXT": context}

  # We'll pull a subset of the available information in for shell scripts.
  # Anyone who needs more will probably want to write a Python handler
  # instead so they can reuse things like our logger & config info and avoid
  # ordeals like associative arrays in Bash
  for k in ["info", "key"]:
    if k in kwargs and kwargs[k]:
      child_env["CRANKD_%s" % k.upper()] = str(kwargs[k])

  if "user_info" in kwargs:
    for k, v in kwargs["user_info"].items():
      child_env[create_env_name(k)] = str(v)

  try:
    rc = subprocess.call(command, shell=True, env=child_env)
    if rc == 0:
      logging.debug("`%s` returned %d", command, rc)
    elif rc < 0:
      logging.error("`%s` was terminated by signal %d", command, -rc)
    else:
      logging.error("`%s` returned %d", command, rc)
  except OSError as exc:
    logging.error("Got an exception when executing %s: %s", command, exc)


def add_conditional_restart(file_name, reason):
  """Use stat to restart only if file mtime has changed."""
  file_name = os.path.realpath(file_name.encode())
  while not os.path.exists(file_name):
    file_name = os.path.dirname(file_name)
  orig_stat = os.stat(file_name).st_mtime

  def cond_restart(*unused_args, **unused_kwargs):
    try:
      if os.stat(file_name).st_mtime != orig_stat:
        restart(reason)
    except (OSError, IOError, RuntimeError) as exc:
      restart("Exception while checking %s: %s" % (file_name, exc))

  add_fs_notification(file_name, cond_restart)


def restart(reason, *unused_args, **unused_kwargs):
  """Perform a complete restart of the current process using exec()."""
  logging.info("Restarting: %s", reason)
  os.execv(sys.argv[0], sys.argv)


def main():
  configure_logging()

  global CRANKD_OPTIONS, CRANKD_CONFIG
  CRANKD_OPTIONS = process_commandline()
  CRANKD_CONFIG = load_config(CRANKD_OPTIONS)

  if "NSWorkspace" in CRANKD_CONFIG:
    add_workspace_notifications(CRANKD_CONFIG["NSWorkspace"])

  if "SystemConfiguration" in CRANKD_CONFIG:
    add_sc_notifications(CRANKD_CONFIG["SystemConfiguration"])

  if "FSEvents" in CRANKD_CONFIG:
    add_fs_notifications(CRANKD_CONFIG["FSEvents"])

  # We reuse our FSEvents code to watch for changes to our files and
  # restart if any of our libraries have been updated:
  add_conditional_restart(
      CRANKD_OPTIONS.config_file,
      "Configuration file %s changed" % CRANKD_OPTIONS.config_file)
  for m in [
      i for i in list(sys.modules.values())
      if i and hasattr(i, "__file__") and i.__file__ is not None
  ]:
    if m.__name__ == "__main__":
      msg = "%s was updated" % m.__file__
    else:
      msg = "Module %s was updated" % m.__name__

    add_conditional_restart(m.__file__, msg)

  signal.signal(signal.SIGHUP, functools.partial(restart, "SIGHUP received"))

  start_fs_events()

  # NOTE: This timer is basically a kludge around the fact that we can't
  # reliably get signals or Control-C inside a runloop. This wakes us up
  # often enough to appear tolerably responsive:
  Cocoa.CFRunLoopAddTimer(
      Cocoa.NSRunLoop.currentRunLoop().getCFRunLoop(),
      Cocoa.CFRunLoopTimerCreate(None, Cocoa.CFAbsoluteTimeGetCurrent(), 2.0, 0,
                                 0, timer_callback, None),
      Cocoa.kCFRunLoopCommonModes)

  try:
    AppHelper.runConsoleEventLoop(installInterrupt=True)
  except KeyboardInterrupt:
    logging.info("KeyboardInterrupt received, exiting")

  sys.exit(0)


if __name__ == "__main__":
  main()

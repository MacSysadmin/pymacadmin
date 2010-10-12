#!/usr/bin/env python
#
# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""pymacds - various directoryservice related functions."""

__author__ = 'Nigel Kersten (nigelk@google.com)'
__version__ = '0.2'


import filecmp
import os
import shutil
import subprocess
import syslog
from Foundation import NSString
import plistlib


_DSCL = '/usr/bin/dscl'
_DSCACHEUTIL = '/usr/bin/dscacheutil'
_DSEDITGROUP = '/usr/sbin/dseditgroup'


class DSException(Exception):
  """Module specific error class."""
  pass


def RunProcess(cmd, stdinput=None, env=None, cwd=None, sudo=False,
               sudo_password=None):
  """Executes cmd using suprocess.

  Args:
    cmd: An array of strings as the command to run
    stdinput: An optional sting as stdin
    env: An optional dictionary as the environment
    cwd: An optional string as the current working directory
    sudo: An optional boolean on whether to do the command via sudo
    sudo_password: An optional string of the password to use for sudo
  Returns:
    A tuple of two strings and an integer: (stdout, stderr, returncode).
  Raises:
    DSException: if both stdinput and sudo_password are specified
  """
  if sudo:
    sudo_cmd = ['sudo']
    if sudo_password and not stdinput:
      # Set sudo to get password from stdin
      sudo_cmd = sudo_cmd + ['-S']
      stdinput = sudo_password + '\n'
    elif sudo_password and stdinput:
      raise DSException('stdinput and sudo_password '
                        'are mutually exclusive')
    else:
      sudo_cmd = sudo_cmd + ['-p',
                             "%u's password is required for admin access: "]
    cmd = sudo_cmd + cmd
  environment = os.environ
  environment.update(env)
  task = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          stdin=subprocess.PIPE, env=environment, cwd=cwd)
  (stdout, stderr) = task.communicate(input=stdinput)
  return (stdout, stderr, task.returncode)


def FlushCache():
  """Flushes the DirectoryService cache."""
  command = [_DSCACHEUTIL, '-flushcache']
  RunProcess(command)


def _GetCSPSearchPathForPath(path):
  """Returns list of search nodes for a given path.

  Args:
    path: One of '/Search' or '/Search/Contacts' only.
  Returns:
    nodes: list of search nodes for given path.
  Raises:
    DSException: Unable to retrieve search nodes in path.
  """

  command = [_DSCL, '-plist', path, '-read', '/', 'CSPSearchPath']
  (stdout, stderr, unused_returncode) = RunProcess(command)
  result = plistlib.readPlistFromString(stdout)
  if 'dsAttrTypeStandard:CSPSearchPath' in result:
    search_nodes = result['dsAttrTypeStandard:CSPSearchPath']
    return search_nodes
  else:
    raise DSException('Unable to retrieve search nodes: %s' % stderr)


def _ModifyCSPSearchPathForPath(action, node, path):
  """Modifies the search nodes for a given path.

  Args:
    action: one of (["append", "delete"]) only.
    node: the node to append or delete.
    path: the DS path to modify.
  Returns:
    True on success
  Raises:
    DSException: Could not modify nodes for path.
  """

  command = [_DSCL, path, '-%s' % action, '/', 'CSPSearchPath', node]
  (unused_stdout, stderr, returncode) = RunProcess(command)
  if returncode:
    raise DSException('Unable to perform %s on CSPSearchPath '
                      'for node: %s on path: %s '
                      'Error: %s '% (action, node, path, stderr))
  FlushCache()
  return True


def GetSearchNodes():
  """Returns search nodes for DS /Search path."""
  return _GetCSPSearchPathForPath('/Search')


def GetContactsNodes():
  """Returns search nodes for DS /Search/Contacts path."""
  return _GetCSPSearchPathForPath('/Search/Contacts')


def AddNodeToSearchPath(node):
  """Adds a given DS node to the /Search path."""
  _ModifyCSPSearchPathForPath('append', node, '/Search')


def AddNodeToContactsPath(node):
  """Adds a given DS node to the /Search/Contacts path."""
  _ModifyCSPSearchPathForPath('append', node, '/Search/Contacts')


def DeleteNodeFromSearchPath(node):
  """Deletes a given DS node from the /Search path."""
  _ModifyCSPSearchPathForPath('delete', node, '/Search')


def DeleteNodeFromContactsPath(node):
  """Deletes a given DS node from the /Search/Contacts path."""
  _ModifyCSPSearchPathForPath('delete', node, '/Search/Contacts')


def EnsureSearchNodePresent(node):
  """Ensures a given DS node is present in the /Search path."""
  if node not in GetSearchNodes():
    AddNodeToSearchPath(node)


def EnsureSearchNodeAbsent(node):
  """Ensures a given DS node is absent from the /Search path."""
  if node in GetSearchNodes():
    DeleteNodeFromSearchPath(node)


def EnsureContactsNodePresent(node):
  """Ensures a given DS node is present in the /Search/Contacts path."""
  if node not in GetContactsNodes():
    AddNodeToContactsPath(node)


def EnsureContactsNodeAbsent(node):
  """Ensures a given DS node is absent from the /Search path."""
  if node in GetContactsNodes():
    DeleteNodeFromContactsPath(node)


def DSQuery(dstype, objectname, attribute=None):
  """DirectoryServices query.

  Args:
    dstype: The type of objects to query. user, group.
    objectname: the object to query.
    attribute: the optional attribute to query.
  Returns:
    If an attribute is specified, the value of the attribute. Otherwise, the
    entire plist.
  Raises:
    DSException: Cannot query DirectoryServices.
  """
  ds_path = '/%ss/%s' % (dstype.capitalize(), objectname)
  cmd = [_DSCL, '-plist', '.', '-read', ds_path]
  if attribute:
    cmd.append(attribute)
  (stdout, stderr, returncode) = RunProcess(cmd)
  if returncode:
    raise DSException('Cannot query %s for %s: %s' % (ds_path,
                                                      attribute,
                                                      stderr))
  plist = NSString.stringWithString_(stdout).propertyList()
  if attribute:
    value = None
    if 'dsAttrTypeStandard:%s' % attribute in plist:
      value = plist['dsAttrTypeStandard:%s' % attribute]
    elif attribute in plist:
      value = plist[attribute]
    try:
      # We're copying to a new list to convert from NSCFArray
      return value[:]
    except TypeError:
      # ... unless we can't
      return value
  else:
    return plist


def DSSet(dstype, objectname, attribute=None, value=None):
  """DirectoryServices attribute set.

  This uses dscl create, wmich overwrites any existing objects or attributes.

  Args:
    dstype: The type of objects to query. user, group.
    objectname: the object to set.
    attribute: the optional attribute to set.
    value: the optional value to set, only handles strings and simple lists
  Raises:
    DSException: Cannot modify DirectoryServices.
  """
  ds_path = '/%ss/%s' % (dstype.capitalize(), objectname)
  cmd = [_DSCL, '.', '-create', ds_path]
  if attribute:
    cmd.append(attribute)
    if value:
      if type(value) == type(list()):
        cmd.extend(value)
      else:
        cmd.append(value)
  (unused_stdout, stderr, returncode) = RunProcess(cmd)
  if returncode:
    raise DSException('Cannot set %s for %s: %s' % (attribute,
                                                    ds_path,
                                                    stderr))


def DSDelete(dstype, objectname, attribute=None, value=None):
  """DirectoryServices attribute delete.

  Args:
    dstype: The type of objects to delete. user, group.
    objectname: the object to delete.
    attribute: the attribute to delete.
    value: the value to delete
  Raises:
    DSException: Cannot modify DirectoryServices.
  """
  ds_path = '/%ss/%s' % (dstype.capitalize(), objectname)
  cmd = [_DSCL, '.', '-delete', ds_path]
  if attribute:
    cmd.append(attribute)
    if value:
      cmd.extend([value])
  (unused_stdout, stderr, returncode) = RunProcess(cmd)
  if returncode:
    raise DSException('Cannot delete %s for %s: %s' % (attribute,
                                                       ds_path,
                                                       stderr))


def UserAttribute(username, attribute):
  """Returns the requested DirectoryService attribute for this user.

  Args:
    username: the user to retrieve a value for.
    attribute: the attribute to retrieve.
  Returns:
    the value of the attribute.
  """
  return DSQuery('user', username, attribute)


def GroupAttribute(groupname, attribute):
  """Returns the requested DirectoryService attribute for this group.

  Args:
    groupname: the group to retrieve a value for.
    attribute: the attribute to retrieve.
  Returns:
    the value of the attribute.
  """
  return DSQuery('group', groupname, attribute)


def AddUserToLocalGroup(username, group):
  """Adds user to a local group, uses dseditgroup to deal with GUIDs.

  Args:
    username: user to add
    group: local group to add user to
  Returns:
    Nothing
  Raises:
    DSException: Can't add user to group
  """
  cmd = [_DSEDITGROUP, '-o', 'edit', '-n', '.',
         '-a', username, '-t', 'user', group]
  (stdout, stderr, rc) = RunProcess(cmd)
  if rc is not 0:
    raise DSException('Error adding %s to group %s, returned %s\n%s' %
                      (username, group, stdout, stderr))


def RemoveUserFromLocalGroup(username, group):
  """Removes user from a local group, uses dseditgroup to deal with GUIDs.

  Args:
    username: user to remove
    group: local group to remove user from
  Returns:
    Nothing
  Raises:
    DSException: Can't remove user from
  """
  cmd = [_DSEDITGROUP, '-o', 'edit', '-n', '.',
         '-d', username, '-t', 'user', group]
  (unused_stdout, stderr, rc) = RunProcess(cmd)
  if rc is not 0:
    raise DSException('Error removing %s from group %s, returned %s' %
                      (username, group, stderr))

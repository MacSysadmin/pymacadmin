#!/usr/bin/python
"""
Usage: create_location.py loc_name

Creates a new SystemConfiguration location for use in Network Preferences by
copying the Automatic location
"""

from SystemConfiguration import \
    SCPreferencesApplyChanges, \
    SCPreferencesCommitChanges, \
    SCPreferencesCreate, \
    SCPreferencesGetValue, \
    SCPreferencesPathCreateUniqueChild, \
    SCPreferencesPathSetValue, \
    kSCPrefSets, \
    kSCPropUserDefinedName

from CoreFoundation import CFDictionaryCreateMutableCopy
import sys
import re


def main():
    if len(sys.argv) != 2:
        print >> sys.stderr, __doc__.strip()
        sys.exit(1)

    new_name      = sys.argv[1]

    sc_prefs      = SCPreferencesCreate(None, "create_location", None)

    sets          = SCPreferencesGetValue(sc_prefs, kSCPrefSets)
    automatic_set = None

    for k in sets:
        if sets[k][kSCPropUserDefinedName] == new_name:
            raise KeyError("A set named %s already exists" % new_name)
        elif sets[k][kSCPropUserDefinedName] == "Automatic":
            automatic_set = sets[k]

    if not automatic_set:
        raise RuntimeError("Couldn't find Automatic set")

    new_set = CFDictionaryCreateMutableCopy(None, 0, automatic_set)
    new_set[kSCPropUserDefinedName] = new_name
    new_set_path = SCPreferencesPathCreateUniqueChild(sc_prefs, "/%s" % kSCPrefSets)

    if not new_set_path \
      or not re.match(r"^/%s/[^/]+$" % kSCPrefSets, new_set_path) \
      or new_set_path in sets:
        raise RuntimeError("SCPreferencesPathCreateUniqueChild() returned an invalid path for the new location: %s" % new_set_path)

    print 'Creating "%s" at %s using a copy of "%s"' % (new_name, new_set_path, automatic_set[kSCPropUserDefinedName])

    SCPreferencesPathSetValue(sc_prefs, new_set_path, new_set)

    if not SCPreferencesCommitChanges(sc_prefs):
        raise RuntimeError("Unable to save SystemConfiguration changes")
        
    if not SCPreferencesApplyChanges(sc_prefs):
        raise RuntimeError("Unable to apply SystemConfiguration changes")

if __name__ == '__main__':
    try:
        main()
    except StandardError, e:
        print >> sys.stderr, "ERROR: " + e.message

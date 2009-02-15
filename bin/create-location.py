#!/usr/bin/python
"""
Usage: create_location.py loc_name

Creates a new SystemConfiguration location for use in Network Preferences.
Currently it copies the Automatic location but there's no reason why it
couldn't be extended to define & configure the services at the same time.
"""

from SystemConfiguration import SCPreferencesCreate, \
    SCPreferencesCommitChanges, SCPreferencesApplyChanges, SCPreferencesGetValue, \
    kSCPrefSets, kSCPropUserDefinedName, SCPreferencesPathCreateUniqueChild, \
    SCPreferencesPathSetValue, CFDictionaryCreateMutableCopy
import sys
import re

def main():
    if len(sys.argv) != 2:
        print >> sys.stderr, __doc__.strip()
        sys.exit(1)
        
    new_name      = sys.argv[1] # How's that for old-school command-line handling?

    sc_prefs      = SCPreferencesCreate(None, "create_location", None)
    
    sets          = SCPreferencesGetValue(sc_prefs, kSCPrefSets)
    automatic_set = None # TODO: Can we simply look for ID=0? I think that will break on upgraded systems

    for k in sets:
        if sets[k][kSCPropUserDefinedName] == new_name:
            raise KeyError("A set named %s already exists" % new_name)
        elif sets[k][kSCPropUserDefinedName] == "Automatic": 
            automatic_set = sets[k]
    
    if not automatic_set:
        raise RuntimeError("Couldn't find the automatic set! Maybe you can help write code to copy another one?")

    new_set                         = CFDictionaryCreateMutableCopy(None, 0, automatic_set)
    new_set[kSCPropUserDefinedName] = new_name

    new_set_path                    = SCPreferencesPathCreateUniqueChild(sc_prefs, "/%s" % kSCPrefSets)
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

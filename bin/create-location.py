#!/usr/bin/python
"""
Usage: %prog USER_VISIBLE_NAME

Creates a new SystemConfiguration location for use in Network Preferences by
copying the Automatic location
"""

from SystemConfiguration import *
from CoreFoundation import *
import sys
import re
import logging
from optparse import OptionParser


def copy_set(path, old_id, old_set):
    new_set      = CFPropertyListCreateDeepCopy(None, old_set, kCFPropertyListMutableContainersAndLeaves)
    new_set_path = SCPreferencesPathCreateUniqueChild(sc_prefs, path)

    if not new_set_path \
      or not re.match(r"^%s/[^/]+$" % path, new_set_path):
        raise RuntimeError("SCPreferencesPathCreateUniqueChild() returned an invalid path for the new location: %s" % new_set_path)

    return new_set_path, new_set


def main():
    # Ugly but this is easiest until we refactor this into an SCPrefs class:
    global sc_prefs

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    parser = OptionParser(__doc__.strip())

    parser.add_option('-v', '--verbose', action="store_true",
        help="Print more information"
    )

    (options, args) = parser.parse_args()

    if not args:
        parser.error("You must specify the user-visible name for the new location")

    if options.verbose:
        logging.getLogger().setLevel(logging.DEBUG)


    new_name   = " ".join(args)
    sc_prefs   = SCPreferencesCreate(None, "create_location", None)
    sets       = SCPreferencesGetValue(sc_prefs, kSCPrefSets)
    old_set_id = None
    old_set    = None

    for k in sets:
        if sets[k][kSCPropUserDefinedName] == new_name:
            raise RuntimeError("A set named %s already exists" % new_name)
        elif sets[k][kSCPropUserDefinedName] == "Automatic":
            old_set_id = k

    if not old_set_id:
        raise RuntimeError("Couldn't find Automatic set")

    old_set = sets[old_set_id]
    logging.debug("Old set %s:\n%s" % (old_set_id, old_set))

    logging.info('Creating "%s" using a copy of "%s"' % (new_name, old_set[kSCPropUserDefinedName]))
    new_set_path, new_set           = copy_set("/%s" % kSCPrefSets, old_set_id, old_set)
    new_set_id                      = new_set_path.split('/')[-1]
    new_set[kSCPropUserDefinedName] = new_name

    service_map = dict()

    for old_service_id in old_set[kSCCompNetwork][kSCCompService]:
        assert(
            old_set[kSCCompNetwork][kSCCompService][old_service_id][kSCResvLink].startswith("/%s" % kSCPrefNetworkServices)
        )

        new_service_path = SCPreferencesPathCreateUniqueChild(sc_prefs, "/%s" % kSCPrefNetworkServices)
        new_service_id   = new_service_path.split("/")[2]
        new_service_cf   = CFPropertyListCreateDeepCopy(
            None,
            SCPreferencesGetValue(sc_prefs, kSCPrefNetworkServices)[old_service_id],
            kCFPropertyListMutableContainersAndLeaves
        )
        SCPreferencesPathSetValue(sc_prefs, new_service_path, new_service_cf)

        new_set[kSCCompNetwork][kSCCompService][new_service_id] = {
            kSCResvLink: new_service_path
        }
        del new_set[kSCCompNetwork][kSCCompService][old_service_id]

        service_map[old_service_id] = new_service_id

    for proto in new_set[kSCCompNetwork][kSCCompGlobal]:
        new_set[kSCCompNetwork][kSCCompGlobal][proto][kSCPropNetServiceOrder] = map(
            lambda k: service_map[k],
            old_set[kSCCompNetwork][kSCCompGlobal][proto][kSCPropNetServiceOrder]
        )

    SCPreferencesPathSetValue(sc_prefs, new_set_path, new_set)

    logging.debug("New Set %s:\n%s\n" % (new_set_id, new_set))

    if not SCPreferencesCommitChanges(sc_prefs):
        raise RuntimeError("Unable to save SystemConfiguration changes")

    if not SCPreferencesApplyChanges(sc_prefs):
        raise RuntimeError("Unable to apply SystemConfiguration changes")


if __name__ == '__main__':
    try:
        main()
    except RuntimeError, e:
        logging.critical(str(e))
        sys.exit(1)

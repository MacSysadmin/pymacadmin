#!/bin/sh

# Script to install crankd
# It is very rudimentary, and doesn't install any plist files

if [[ $UID -ne 0 ]]; then
	echo "$0 must be run as root"
	exit 1
fi


INITIAL_DIR=`pwd`
BASE_DIR=`dirname "$0"`
cd "$BASE_DIR"

mkdir -p /usr/local/sbin
cp bin/crankd.py /usr/local/sbin/
mkdir -p /Library/Application\ Support/crankd
cp -R lib/PyMacAdmin /Library/Application\ Support/crankd/


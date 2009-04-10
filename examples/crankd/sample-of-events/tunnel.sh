#!/bin/sh

if [[ "$#" -lt 2 ]] ; then 
  cat <<EndUsageText
  This is a stub/forwarder script.
  It exists to make it easy to change the target action of a crankd script
  (ex. to change from 'echo' to 'say', you just have to edit it here)
  or to send the output to multiple programs.

  It expects two parameters -- an event category, and a specific event
  For example, the category might be "NSWorkspace" and the event might be
  NSWorkspaceDidMountNotification.
EndUsageText

else
  echo "----------------------------------------------------------------------"
  echo "Called as: $0 $*"
  env | sort

  CATEGORY=$1
  SPECIFIC=$2

  # echoing is only useful if you invoke crankd in a Terminal
  echo "[$CATEGORY] $SPECIFIC event occurred."

  # You will need to install growl and growlnotify to use this.
  # http://growl.info/
  if [ ! -z "`which growlnotify`" ]; then
    growlnotify --message "$SPECIFIC event occurred" --title "$CATEGORY event" --name "crankd notification"
  fi

  # Open up Console to see the syslogged events
  logger "[$CATEGORY] $SPECIFIC event occurred"

  # Speak the event out loud
  # (I am expanding the text, so that "NSWorkspaceDidTerminateApplicationNotification"
  # becomes "N S Workspace Did Terminate Application Notification", which is more
  # readily pronounced; see http://stackoverflow.com/questions/199059/
  # im-looking-for-a-pythonic-way-to-insert-a-space-before-capital-letters ,
  # and add a bunch of escaping backslashes!)

  echo "$SPECIFIC" | python -c 'import re, sys; print re.sub(r"""\B([A-Z])""", r""" \1""", sys.stdin.read().replace(":", " "))' | say -f-
fi




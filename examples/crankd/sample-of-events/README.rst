sample-of-events
================

This sample is designed to allow you to easily get a feel for what sort of
events you can tap into with `crankd`.  `generate-event-plist.py` will create a
file called `crankd-config.plist`, which configures crankd to call our wrapper
script, `tunnel.sh` when any of a large sampling of system events (such as
joining networks or mounting volumes) occur.

To use it, open up a `Terminal` window to the directory containing the files.

1.  Generate the plist:

> `python generate-event-plist.py`

2.  If desired, edit `tunnel.sh` until you are satisfied with what commands it
will trigger.  It is intially set up to log the event (so you can see it in
`Console`) and to [Growl](http://growl.info/) the event (but you need to have
`growlnotify` installed), to `say` that an event occured, and to `echo` the
event.

3.  Run crankd:

> `/path/to/bin/crankd.py --config=crankd-config.plist`

4.  Generate some events -- (dis)connect to/from a network, (un)mount a volume,
(un)plug the power adapter, and so on.  Watch as the events are triggered.

5.  When you are done, press `Ctrl-C` to kill `crankd`.

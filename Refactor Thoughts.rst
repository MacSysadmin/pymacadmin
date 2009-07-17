Refactor Goals
==============

* Cleaner core code
* Easier start for new users
* Easier testing with mock events

Global variable cleanup
-----------------------

* Finish cleaning up "magic" variables: e.g. handlers should do something like::

	from PyMacAdmin import crankd
	if crankd.debug:
		…
		
* Remove all specific event handling code to separate classes which inherit from `EventSource`


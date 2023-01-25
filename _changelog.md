History:

2022.0.10 (25-Jan-2023) -- DaveL17
* Moves constants to separate file, and refactors for PEP8.
* Moves change log to separate file.
* Code cleanup.

2022.0.9 (20-Jan-2023) -- DaveL17
* Changes status message for unrecognized responses to be "unknown".

2022.0.3 (23-Dec-2022) -- DaveL17
* Addresses telnet error "str vs. bytes"

2022.0.2 (19-Dec-2022) -- DaveL17
* (Some) more code clean up.

2022.0.1 (18-Dec-2022) -- DaveL17
* Updates to Indigo 2022.1 and Python 3.
* Improves compliance with PEP8.

1.0.8 (27-Sep-2015)
* Fixed another bug that caused the plugin to crash when communicating with the VSX-1123-K.
1.0.7 (25-Sep-2015)
* Fixed 2 bugs that caused the plugin to crash when communicating with the VSX-1123-K.

1.0.6 (18-Aug-2014)
* Fixed bug in 1.0.5 that caused every receiver except for the VSX-1021-K to return E06 (invalid
parameter) errors when the Pioneer Receiver plugin attempted to gather all input source names.

1.0.5 (10-Aug-2014)
* Added support for SC-75.
* Improved Zone 1 power-on command reliability for 2012 or later models.
* Improved Zone 1 power toggle command reliability for 2012+ models.
* Added the "MHL" input as a valid input option for VSX-1123-K.

1.0.4 (16-Dec-2013)
* Added support for VSX-1123-K and other newer models.
* Having heard no reports of issues, the VSX-1022-K support is no longer "experimental".
* Changed audio input/output frequencies from a number to a string to match state definition in
  Devices.xml.

1.0.3 (01-Sep-2013)
* Fixed a bug that prevented zone 2 volume device states and any associated Virtual Volume Controllers
  from updating properly.

1.0.2 (30-Jul-2013)
* Added the indigoPluginUpdateChecker module (code by Travis CooK) to facilitate automatic plugin
  version checking.

1.0.1 (24-Feb-2013)
*  Added experimental support for the VSX-1022-K.

1.0 (08-Nov-2012)
*  Finalized support for the VSX-1122-K.
*  Updated UI for improved Indigo 6 compatibility.
*  Improved coherence to Pioneer recommended delays between sending commands, especially during initial
   zone power-on and plugin startup.

0.9.13 (31-Oct-2012, unreleased)
*  Began modifying plugin for improved Indigo compatibility.

0.9.12 (29-Oct-2012, unreleased)
*  Performed additional testing on VSX-1122-K hardware. Slightly modified when the startup information
   gathering process sleeps.
*  Minor modifications to the action definitions.

0.9.11 (26-Oct-2012, unreleased)
*  Continued work on fixing the text encoding bug in the processResponse method.  Changed the unicode()
   call by specifying "errors='replace'" to force ASCII output. Also added code to the readData method
   to force the response from the receiver to be in ASCII.

0.9.10 (25-Oct-2012, unreleased)
*  Attempted to fix a bug in the video status information processing of the processResponse method that
   was causing the runConcurrentThread to crash, leaving the connection to the receiver open, forcing
   the user to reload the plugin in order to reconnect to the receiver.
*  Fixed a bug in the Video Color Space status information interpretation which caused the device state
   to show the wrong color space.

0.9.9 (23-Oct-2012)
*  Fixed a character encoding bug in the startDeviceComm method which would return an error if the
   expanded device object contained non-ASCII characters.
*  Fixed an audio input signal format interpretation bug that caused the runConcurrentThread to crash
   whenever the input signal format was "07" (undefined) on newer VSX receiver models.

0.9.8 (07-Oct-2012)
*  Began adding experimental support for the VSX-1122-K.
*  Added additional error checking code throughout.

0.9.7 (09-Sep-2012)
*  Added "Power On/Off" state which will show "On" if any zone is in use.
*  Changed most true/false states to On/Off-type states for better clarity and consistency.
*  Changed values in states that contain "off" or "on" conditions as well as other conditions (like
   "auto") to all lower-case for easier scripting.
*  Changed plugin ID from com.nathansheldon.indigoplugin.pioneerreceiver to
   com.nathansheldon.indigoplugin.PioneerReceiver to be more consistent with other plugin IDs.

0.9.6 (17-Aug-2012)
*  Added "Next Stereo Listening Mode", "Next Auto Surround Listening Mode", "Next Advanced Surround
   Listening Mode", and "Select Listening Mode" actions to Actions.xml and plugin.py.
*  Added "Set Display Brightness" action to Actions.xml and plugin.py
*  Added "Set Sleep Timer" action to Actions.xml and plugin.py.
*  Changed names of surroundListeningMode and playbackListeningMode to more accurately represent their
   function in the receiver.
*  Changed Devices.xml "Virtual Volume Controller" method used to list receiver devices in
   configuration dialog.

0.9.5 (15-Aug-2012)
*  Added a "Virtual Volume Controller" device that provides an Indigo native dimmer device which in
   turn controls a receiver device's zone 1 or 2 volume.
*  Corrected support URL typo.

0.9.4 (13-Aug-2012)
*  Allowed for IP addresses with 0 as a component.

0.9.3 (13-Aug-2012)
*  Better fix for device validation bug.

0.9.1, 0.9.2 (13-Aug-2012)
*  Tried to fix a device validation bug, but failed.

0.9 (13-Aug-2012)
*  Initial (beta) release

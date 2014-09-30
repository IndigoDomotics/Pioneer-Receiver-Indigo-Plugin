#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2012, Nathan Sheldon. All rights reserved.
# http://www.nathansheldon.com/files/Pioneer-Receiver-Plugin.php
#
#	Version 1.0.6
#
#	History:	1.0.6 (18-Aug-2014)
#				* Fixed bug in 1.0.5 that caused every receiver except for the VSX-1021-K
#				  to return E06 (invalid parameter) errors when the Pioneer Receiver
#				  plugin attempted to gather all input source names.
#				--
#				1.0.5 (10-Aug-2014)
#				* Added support for SC-75.
#				* Improved Zone 1 power-on command reliability for 2012 or later models.
#				* Improved Zone 1 power toggle command reliability for 2012+ models.
#				* Added the "MHL" input as a valid input option for VSX-1123-K.
#				--
#				1.0.4 (16-Dec-2013)
#				* Added support for VSX-1123-K and other newer models.
#				* Having heard no reports of issues, the VSX-1022-K support is no
#				  longer "experimental".
#				* Changed audio input/output frequencies from a number to a string
#				  to match state definition in Devices.xml.
#				--
#				1.0.3 (01-Sep-2013)
#				* Fixed a bug that prevented zone 2 volume device states and any
#				  associated Virtual Volume Controllers from updating properly.
#				--
#				1.0.2 (30-Jul-2013)
#				* Added the indigoPluginUpdateChecker module (code by Travis CooK)
#				  to facilitate automatic plugin version checking.
#				--
#				1.0.1 (24-Feb-2013)
#				*  Added experimental support for the VSX-1022-K.
#				--
#				1.0 (08-Nov-2012)
#				*  Finalized support for the VSX-1122-K.
#				*  Updated UI for improved Indigo 6 compatibility.
#				*  Improved coherence to Pioneer recommended delays between
#				   sending commands, especially during initial zone power-on
#				   and plugin startup.
#				--
#				0.9.13 (31-Oct-2012, unreleased)
#				*  Began modifying plugin for improved Indigo compatibility.
#				--
#				0.9.12 (29-Oct-2012, unreleased)
#				*  Performed additional testing on VSX-1122-K hardware.
#				   Slightly modified when the startup information gathering
#				   process sleeps.
#				*  Minor modifications to the action definitions.
#				--
#				0.9.11 (26-Oct-2012, unreleased)
#				*  Continued work on fixing the text encoding bug in the
#				   processResponse method.  Changed the unicode() call by
#				   specifying "errors='replace'" to force ASCII output. Also
#				   added code to the readData method to force the response
#				   from the receiver to be in ASCII.
#				--
#				0.9.10 (25-Oct-2012, unreleased)
#				*  Attempted to fix a bug in the video status information
#				   processing of the processResponse method that was causing
#				   the runConcurrentThread to crash, leaving the connection
#				   to the receiver open, forcing the user to reload the
#				   plugin in order to reconnect to the receiver.
#				*  Fixed a bug in the Video Color Space status information
#				   interpretation which caused the device state to show
#				   the wrong color space.
#				--
#				0.9.9 (23-Oct-2012)
#				*  Fixed a character encoding bug in the startDeviceComm
#				   method which would return an error if the expanded
#				   device object contained non-ASCII characters.
#				*  Fixed an audio input signal format interpretation bug
#				   that caused the runConcurrentThread to crash whenever
#				   the input signal format was "07" (undefined) on newer
#				   VSX receiver models.
#				--
#				0.9.8 (07-Oct-2012)
#				*  Began adding experimental support for the VSX-1122-K.
#				*  Added additional error checking code throughout.
#				--
#				0.9.7 (09-Sep-2012)
#				*  Added "Power On/Off" state which will show "On" if any
#				   zone is in use.
#				*  Changed most true/false states to On/Off-type states
#				   for better clarity and consistency.
#				*  Changed values in states that contain "off" or "on"
#				   conditions as well as other conditions (like "auto")
#				   to all lower-case for easier scripting.
#				*  Changed plugin ID from
#				   com.nathansheldon.indigoplugin.pioneerreceiver to
#				   com.nathansheldon.indigoplugin.PioneerReceiver
#				   to be more consistant with other plugin IDs.
#				--
#				0.9.6 (17-Aug-2012)
#				*  Added "Next Stereo Listening Mode", "Next Auto Surround
#				   Listening Mode", "Next Advanced Surround Listening Mode",
#				   and "Select Listening Mode" actions to Actions.xml and
#				   plugin.py.
#				*  Added "Set Display Brightness" action to Actions.xml and
#				   plugin.py
#				*  Added "Set Sleep Timer" action to Actions.xml and plugin.py.
#				*  Changed names of surroundListeningMode and playbackListeningMode
#				   to more accurately represent their function in the receiver.
#				*  Changed Devices.xml "Virtual Volume Controller" method
#				   used to list receiver devices in configuration dialog.
#				--
#				0.9.5 (15-Aug-2012)
#				*  Added a "Virtual Volume Controller" device that
#				   provides an Indigo native dimmer device which in turn
#				   controls a receiver device's zone 1 or 2 voluem.
#				*  Corrected support URL typo.
#				--
#				0.9.4 (13-Aug-2012)
#				*  Allowed for IP addresses with 0 as a component.
#				--
#				0.9.3 (13-Aug-2012)
#				*  Better fix for device validation bug.
#				--
#				0.9.1, 0.9.2 (13-Aug-2012)
#				*  Tried to fix a device validation bug, but failed.
#				--
#				0.9 (13-Aug-2012)
#				*  Initial (beta) release
#

################################################################################
import os
import sys
import signal
import telnetlib
import indigoPluginUpdateChecker

# Special display character number mapping dictionary.
characterMap = {0:u"", 1:u"rpt+shfl ", 2:u"rpt ", 3:u"shfl ", 4:u"◊ ", 5:u"[)", 6:u"(]", 7:u"I", 8:u"II", 9:u"<", 10:u">", 11:u"\\^^/", 12:u".", 13:u".0", 14:u".5", 15:u"Ω", 16:u"0", 17:u"1", 18:u"2", 19:u"3", 20:u"4", 21:u"5", 22:u"6", 23:u"7", 24:u"8", 25:u"9", 26:u"A", 27:u"B", 28:u"C", 29:u"F", 30:u"M", 31:u"¯", 127:"◊", 128:u"Œ", 129:u"œ", 130:u"IJ", 131:u"ij", 132:u"π", 133:u"±", 134:u"", 135:u"", 136:u"", 137:u"", 138:u"", 139:u"", 140:u"<-", 141:u"^", 142:u"->", 143:u"v", 144:u"+", 145:u"√", 146:u"ƒ", 147:u"", 148:u"", 149:u"", 150:u"", 151:u"", 152:u"", 153:u"", 154:u"", 155:u"", 156:u"", 157:u"", 158:u"", 159:u"", 160:u"", 161:u"¡", 162:u"¢", 163:u"£", 164:u"Ø", 165:u"¥", 166:u"|", 167:u"§", 168:u"¨", 169:u"©", 170:u"a", 171:u"«", 172:u"¬", 173:u"-", 174:u"®", 175:u"¯", 176:u"°", 177:u"±", 178:u"2", 179:u"3", 180:u"’", 181:u"µ", 182:u"¶", 183:u"·", 184:u"‚", 185:u"1", 186:u"0", 187:u"»", 188:u"1/4", 189:u"1/2", 190:u"3/4", 191:u"¿", 192:u"À", 193:u"Á", 194:u"Â", 195:u"Ã", 196:u"Ä", 197:u"Å", 198:u"Æ", 199:u"Ç", 200:u"È", 201:u"É", 202:u"Ê", 203:u"Ë", 204:u"Ì", 205:u"Í", 206:u"Î", 207:u"Ï", 208:u"D", 209:u"Ñ", 210:u"Ò", 211:u"Ó", 212:u"Ô", 213:u"Õ", 214:u"Ö", 215:u"x", 216:u"Ø", 217:u"Ù", 218:u"Ú", 219:u"Û", 220:u"Ü", 221:u"Y", 222:u"p", 223:u"ß", 224:u"à", 225:u"á", 226:u"â", 227:u"ã", 228:u"ä", 229:u"å", 230:u"æ", 231:u"ç", 232:u"è", 233:u"é", 234:u"ê", 235:u"ë", 236:u"ì", 237:u"í", 238:u"î", 239:u"ï", 240:u"∂", 241:u"ñ", 242:u"ò", 243:u"ó", 244:u"ô", 245:u"õ", 246:u"ö", 247:u"÷", 248:u"ø", 249:u"ù", 250:u"ú", 251:u"û", 252:u"ü", 253:u"y", 254:u"p", 255:u"ÿ"}
# Channel volume receiver responses to device states map.
channelVolumes = {"L__":'channelVolumeL', "R__":'channelVolumeR', "C__":'channelVolumeC', "SL_":'channelVolumeSL', "SR_":'channelVolumeSR', "SBL":'channelVolumeSBL', "SBR":'channelVolumeSBR', "SW_":'channelVolumeSW', "LH_":'channelVolumeLH', "RH_":'channelVolumeRH', "LW_":'channelVolumeLW', "RW_":'channelVolumeRW'}
# Input source IDs to default names map.
sourceNames = {'00':"PHONO", '01':"CD", '02':"TUNER", '03':"CD-R/TAPE", '04':"DVD", '05':"TV", '06':"SAT/CBL", '10':"VIDEO 1 (VIDEO)", '12':"MULTI CH IN", '13':"USB-DAC", '14':"VIDEO 2", '15':"DVR/BDR", '17':"iPod/USB", '19':"HDMI 1", '20':"HDMI 2", '21':"HDMI 3", '22':"HDMI 4", '23':"HDMI 5", '24':"HDMI 6", '25':"BD", '26':"NETWORK", '27':"SIRIUS", '31':"HDMI (cyclic)", '33':"ADAPTER PORT", '34':"HDMI 7", '35':"HDMI 8", '38':"INTERNET RADIO", '40':"SiriusXM", '41':"PANDORA", '44':"MEDIA SERVER", '45':"FAVORITES", '46':"AirPlay", '47':"DMR", '48':"MHL"}
# VSX-1021-K source mask.
vsx1021kSourceMask = ['00', '06', '12', '13', '20', '21', '22', '23', '24', '31', '34', '35', '38', '40', '41', '44', '45', '46', '47', '48']
# VSX-1021-K zone 2 source mask.
vsx1021kZone2SourceMask = ['00', '06', '12', '13', '19', '20', '21', '22', '23', '24', '25', '31', '34', '35', '38', '40', '41', '44', '45', '46', '47', '48']
# VSX-1022-K source mask.
vsx1022kSourceMask = ['00', '03', '12', '13', '14', '19', '20', '21', '22', '23', '24', '26', '27', '31', '34', '35', '40', '48']
# VSX-1022-K zone 2 source mask.
vsx1022kZone2SourceMask = ['00', '03', '12', '13', '14', '19', '20', '21', '22', '23', '24', '25', '26', '27', '31', '34', '35', '40', '48']
# VSX-1122-K source mask.
vsx1122kSourceMask = ['03', '10', '12', '13', '14', '26', '27', '31', '34', '35', '46', '47', '48']
# VSX-1122-K zone 2 source mask.
vsx1122kZone2SourceMask = ['03', '10', '12', '13', '14', '19', '25', '26', '27', '31', '34', '35', '46', '47', '48']
# VSX-1123-K source mask.
vsx1123kSourceMask = ['03', '10', '12', '13', '14', '26', '27', '31', '35', '46', '47']
# VSX-1123-K zone 2 source mask.
vsx1123kZone2SourceMask = ['03', '10', '12', '13', '14', '19', '25', '26', '27', '31', '35', '46', '47']
# SC-75 source mask.
sc75SourceMask = ['00', '03', '12', '13', '14', '27', '46', '47']
# SC-75 zone 2 source mask.
sc75Zone2SourceMask = ['00', '03', '12', '13', '14', '27','46', '47']

# Listening Mode IDs to names map.
listeningModes = {'0001':"Stereo (cyclic)", '0003':"Front Stage Surround Advance Focus", '0004':"Front Stage Surround Advance Wide", '0005':"Auto Surround/Stream Direct (cyclic)", '0006':"Auto Surround", '0007':"Direct", '0008':"Pure Direct", '0009':"Stereo", '0010':"Standard (cyclic)", '0011':"2-ch Source", '0012':"Dolby Pro Logic", '0013':"Dolby Pro Logic II Movie", '0014':"Dolby Pro Logic II Music", '0015':"Dolby Pro Logic II Game", '0016':"DTS Neo:6 Cinema", '0017':"DTS Neo:6 Music", '0018':"Dolby Pro Logic IIx Movie", '0019':"Dolby Pro Logic IIx Music", '0020':"Dolby Pro Logic IIx Game", '0021':"Multi-ch Source", '0022':"Dolby EX (Multi-ch Source)", '0023':"Dolby Pro Logic IIx Movie (Multi-ch Source)", '0024':"Dolby Pro Logic IIx Music (Multi-ch Source)", '0025':"DTS-ES Neo:6 (Multi-ch Source)", '0026':"DTS-ES Matrix (Multi-ch Source)", '0027':"DTS-ES Discrete (Multi-ch Source)", '0028':"XM HD Surround", '0029':"Neural Surround", '0030':"DTS-ES 8-ch Discrete (Multi-ch Source)", '0031':"Dolby Pro Logic IIz Height", '0032':"Wide Surround Movie", '0033':"Wide Surround Music", '0034':"Dolby Pro Logic IIz Height (Multi-ch Source)", '0035':"Wide Surround Movie (Multi-ch Source)", '0036':"Wide Surround Music (Multi-ch Source)", '0037':"DTS Neo:X Cinema", '0038':"DTS Neo:X Music", '0039':"DTS Neo:X Game", '0040':"Neural Surround + DTS Neo:X Cinema", '0041':"Neural Surround + DTS Neo:X Music", '0042':"Neural Surround + DTS Neo:X Game", '0043':"DTS-ES Neo:X (Multi-ch Source)", '0050':"THX (cyclic)", '0051':"Dolby Pro Logic + THX Cinema", '0052':"Dolby Pro Logic II Movie + THX Cinema", '0053':"DTS Neo:6 Cinema + THX Cinema", '0054':"Dolby Pro Logic IIx Movie + THX Cinema", '0055':"THX Select 2 Games", '0056':"THX Cinema (Multi-ch Source)", '0057':"THX Surround EX (Multi-ch Source)", '0058':"Dolby Pro Logic IIx Movie + THX Cinema (Multi-ch Source)", '0059':"DTS-ES Neo:6 + THX Cinema (Multi-ch Source)", '0060':"DTS-ES Matrix + THX Cinema (Multi-ch Source)", '0061':"DTS-ES Discrete + THX Cinema (Multi-ch Source)", '0062':"THX Select 2 Cinema (Multi-ch Source)", '0063':"THX Select 2 Music (Multi-ch Source)", '0064':"THX Select 2 Games (Multi-ch Source)", '0065':"THX Ultra 2 Cinema (Multi-ch Source)", '0066':"THX Ultra 2 Music (Multi-ch Source)", '0067':"DTS-ES 8-ch Discrete + THX Cinema (Multi-ch Source)", '0068':"THX Cinema (2-ch)", '0069':"THX Music (2-ch)", '0070':"THX Games (2-ch)", '0071':"Dolby Pro Logic II Music + THX Music", '0072':"Dolby Pro Logic IIx Music + THX Music", '0073':"DTS Neo:6 Music + THX Music", '0074':"Dolby Pro Logic II Game + THX Games", '0075':"Dolby Pro Logic IIx Game + THX Games", '0076':"THX Ultra 2 Games", '0077':"Dolby Pro Logic + THX Music", '0078':"Dolby Pro Logic + THX Games", '0079':"THX Ultra 2 Games (Multi-ch Source)", '0080':"THX Music (Multi-ch Source)", '0081':"THX Games (Multi-ch Source)", '0082':"Dolby Pro Logic IIx Music + THX Music (Multi-ch Source)", '0083':"Dolby Digital EX + THX Games (Multi-ch Source)", '0084':"DTS Neo:6 + THX Music (Multi-ch Source)", '0085':"DTS Neo:6 + THX Games (Multi-ch Source)", '0086':"Dolby Digital ES Matrix + THX Music (Multi-ch Source)", '0087':"Dolby Digital ES Matrix + THX Games (Multi-ch Source)", '0088':"Dolby Digital ES Discrete + THX Music (Multi-ch Source)", '0089':"Dolby Digital ES Discrete + THX Games (Multi-ch Source)", '0090':"Dolby Digital ES 8-ch Discrete + THX Music (Multi-ch Source)", '0091':"Dolby Digital ES 8-ch Discrete + THX Games (Multi-ch Source)", '0092':"Dolby Pro Logic IIz Height + THX Cinema", '0093':"Dolby Digital Pro Logic IIz Height + THX Music", '0094':"Dolby Pro Logic IIz Height + THX Games", '0095':"Dolby Pro Logic IIz Height + THX Cinema (Multi-ch Source)", '0096':"Dolby Pro Logic IIz Height + THX Music (Multi-ch Source)", '0097':"Dolby Pro Logic IIz Height + THX Games (Multi-ch Source)", '0100':"Advanced Surround (cyclic)", '0101':"Action", '0102':"Sci-Fi", '0103':"Drama", '0104':"Entertainment Show", '0105':"Mono Film", '0106':"Expanded Theater", '0107':"Classical", '0109':"Unplugged", '0110':"Rock/Pop", '0112':"Extended Stereo", '0113':"Phones Surround", '0116':"TV Surround", '0117':"Sports", '0118':"Advanced Games", '0151':"Auto Level Control (A.L.C.)", '0152':"Optimum Surround", '0153':"Retriever Air", '0200':"ECO Mode (cyclic)", '0201':"DTS Neo:X Cinema + THX Cinema", '0202':"DTS Neo:X Music + THX Music", '0203':"DTS Neo:X Game + THX Games", '0204':"DTS Neo:X + THX Cinema (Multi-ch Source)", '0205':"DTS Neo:X + THX Music (Multi-ch Source)", '0206':"DTS Neo:X + THX Games (Multi-ch Source)", '0212':"ECO Mode 1", '0213':"ECO Mode 2"}
# VSX-1021-K Surround Listening Mode ID mask.
vsx1021kListeningModeMask = ['0011', '0028', '0037', '0038', '0039', '0040', '0041', '0042', '0043', '0050', '0051', '0052', '0053', '0054', '0055', '0056', '0057', '0058', '0059', '0060', '0061', '0062', '0063', '0064', '0065', '0066', '0067', '0068', '0069', '0070', '0071', '0072', '0073', '0074', '0075', '0076', '0077', '0078', '0079', '0080', '0081', '0082', '0083', '0084', '0085', '0086', '0087', '0088', '0089', '0090', '0091', '0092', '0093', '0094', '0095', '0096', '0097', '0152', '0200', '0201', '0202', '0203', '0204', '0205', '0206', '0212', '0213']
# VSX-1022-K Surround Listening Mode ID mask.
vsx1022kListeningModeMask = ['0011', '0028', '0037', '0038', '0039', '0040', '0041', '0042', '0043', '0050', '0051', '0052', '0053', '0054', '0055', '0056', '0057', '0058', '0059', '0060', '0061', '0062', '0063', '0064', '0065', '0066', '0067', '0068', '0069', '0070', '0071', '0072', '0073', '0074', '0075', '0076', '0077', '0078', '0079', '0080', '0081', '0082', '0083', '0084', '0085', '0086', '0087', '0088', '0089', '0090', '0091', '0092', '0093', '0094', '0095', '0096', '0097', '0152', '0200', '0201', '0202', '0203', '0204', '0205', '0206', '0212', '0213']
# VSX-1122-K Surround Listening Mode ID mask.
vsx1122kListeningModeMask = ['0011', '0028', '0029', '0037', '0038', '0039', '0040', '0041', '0042', '0043', '0044', '0045', '0050', '0051', '0052', '0053', '0054', '0055', '0056', '0057', '0058', '0059', '0060', '0061', '0062', '0063', '0064', '0065', '0066', '0067', '0068', '0069', '0070', '0071', '0072', '0073', '0074', '0075', '0076', '0077', '0078', '0079', '0080', '0081', '0082', '0083', '0084', '0085', '0086', '0087', '0088', '0089', '0090', '0091', '0092', '0093', '0094', '0095', '0096', '0097', '0152', '0200', '0201', '0202', '0203', '0204', '0205', '0206', '0212', '0213']
# VSX-1123-K Surround Listening Mode ID mask.
vsx1123kListeningModeMask = ['0011', '0016', '0017', '0025', '0028', '0029', '0037', '0038', '0039', '0040', '0041', '0042', '0043', '0044', '0045', '0050', '0051', '0052', '0053', '0054', '0055', '0059', '0060', '0061', '0062', '0063', '0064', '0065', '0066', '0067', '0068', '0069', '0070', '0071', '0072', '0073', '0074', '0075', '0076', '0077', '0078', '0079', '0080', '0081', '0082', '0083', '0084', '0085', '0086', '0087', '0088', '0089', '0090', '0091', '0092', '0093', '0094', '0095', '0096', '0097', '0152', '0201', '0202', '0203', '0204', '0205', '0206']
# SC-75 Surround Listening Mode ID mask.
sc75ListeningModeMask = ['0011', '0016', '0017', '0025', '0028', '0029', '0037', '0038', '0039', '0040', '0041', '0042', '0043', '0044', '0045', '0053', '0055', '0057', '0058', '0059', '0062', '0063', '0064', '0065', '0066', '0073', '0076', '0077', '0078', '0079', '0083', '0084', '0085']
# Display Listening Mode IDs to names map.
displayListeningModes = {'0101':"[)(]PLIIx MOVIE", '0102':"[)(]PLII MOVIE", '0103':"[)(]PLIIx MUSIC", '0104':"[)(]PLII MUSIC", '0105':"[)(]PLIIx GAME", '0106':"[)(]PLII GAME", '0107':"[)(]PROLOGIC", '0108':"Neo:6 CINEMA", '0109':"Neo:6 MUSIC", '010a':"XM HD Surround", '010b':"NEURAL SURR", '010c':"2ch Straight Decode", '010d':"[)(]PLIIz HEIGHT", '010e':"WIDE SURR MOVIE", '010f':"WIDE SURR MUSIC", '0110':"STEREO", '0111':"Neo:X CINEMA", '0112':"Neo:X MUSIC", '0113':"Neo:X GAME", '0114':"NEURAL SURROUND+Neo:X CINEMA", '0115':"NEURAL SURROUND+Neo:X MUSIC", '0116':"NEURAL SURROUND+Neo:X GAMES", '1101':"[)(]PLIIx MOVIE", '1102':"[)(]PLIIx MUSIC", '1103':"[)(]DIGITAL EX", '1104':"DTS + Neo:6 / DTS-HD + Neo:6", '1105':"ES MATRIX", '1106':"ES DISCRETE", '1107':"DTS-ES 8ch", '1108':"multi ch Straight Decode", '1109':"[)(]PLIIz HEIGHT", '110a':"WIDE SURR MOVIE", '110b':"WIDE SURR MUSIC", '110c':"ES Neo:X", '0201':"ACTION", '0202':"DRAMA", '0203':"SCI-FI", '0204':"MONO FILM", '0205':"ENT.SHOW", '0206':"EXPANDED", '0207':"TV SURROUND", '0208':"ADVANCED GAME", '0209':"SPORTS", '020a':"CLASSICAL", '020b':"ROCK/POP", '020c':"UNPLUGGED", '020d':"EXT.STEREO", '020e':"PHONES SURR.", '020f':"FRONT STAGE SURROUND ADVANCE FOCUS", '0210':"FRONT STAGE SURROUND ADVANCE WIDE", '0211':"SOUND RETRIEVER AIR", '0212':"ECO MODE 1", '0213':"ECO MODE 2", '0301':"[)(]PLIIx MOVIE + THX", '0302':"[)(]PLII MOVIE + THX", '0303':"[)(]PL + THX CINEMA", '0304':"Neo:6 CINEMA + THX", '0305':"THX CINEMA", '0306':"[)(]PLIIx MUSIC + THX", '0307':"[)(]PLII MUSIC + THX", '0308':"[)(]PL + THX MUSIC", '0309':"Neo:6 MUSIC + THX", '030a':"THX MUSIC", '030b':"[)(]PLIIx GAME + THX", '030c':"[)(]PLII GAME + THX", '030d':"[)(]PL + THX GAMES", '030e':"THX ULTRA2 GAMES", '030f':"THX SELECT2 GAMES", '0310':"THX GAMES", '0311':"[)(]PLIIz + THX CINEMA", '0312':"[)(]PLIIz + THX MUSIC", '0313':"[)(]PLIIz + THX GAMES", '0314':"Neo:X CINEMA + THX CINEMA", '0315':"Neo:X MUSIC + THX MUSIC", '0316':"Neo:X GAMES + THX GAMES", '1301':"THX Surr EX", '1302':"Neo:6 + THX CINEMA", '1303':"ES MTRX + THX CINEMA", '1304':"ES DISC + THX CINEMA", '1305':"ES 8ch + THX CINEMA", '1306':"[)(]PLIIx MOVIE + THX", '1307':"THX ULTRA2 CINEMA", '1308':"THX SELECT2 CINEMA", '1309':"THX CINEMA", '130a':"Neo:6 + THX MUSIC", '130b':"ES MTRX + THX MUSIC", '130c':"ES DISC + THX MUSIC", '130d':"ES 8ch + THX MUSIC", '130e':"[)(]PLIIx MUSIC + THX", '130f':"THX ULTRA2 MUSIC", '1310':"THX SELECT2 MUSIC", '1311':"THX MUSIC", '1312':"Neo:6 + THX GAMES", '1313':"ES MTRX + THX GAMES", '1314':"ES DISC + THX GAMES", '1315':"ES 8ch + THX GAMES", '1316':"[)(]EX + THX GAMES", '1317':"THX ULTRA2 GAMES", '1318':"THX SELECT2 GAMES", '1319':"THX GAMES", '131a':"[)(]PLIIz + THX CINEMA", '131b':"[)(]PLIIz + THX MUSIC", '131c':"[)(]PLIIz + THX GAMES", '131d':"Neo:X + THX CINEMA", '131e':"Neo:X + THX MUSIC", '131f':"Neo:X + THX GAMES", '0401':"STEREO", '0402':"[)(]PLII MOVIE", '0403':"[)(]PLIIx MOVIE", '0404':"Neo:6 CINEMA", '0405':"AUTO SURROUND Straight Decode", '0406':"[)(]DIGITAL EX", '0407':"[)(]PLIIx MOVIE", '0408':"DTS + Neo:6", '0409':"ES MATRIX", '040a':"ES DISCRETE", '040b':"DTS-ES 8ch", '040c':"XM HD Surround", '040d':"NEURAL SURR", '040e':"RETRIEVER AIR", '040f':"Neo:X CINEMA", '0410':"ES Neo:X", '0501':"STEREO", '0502':"[)(]PLII MOVIE", '0503':"[)(]PLIIx MOVIE", '0504':"Neo:6 CINEMA", '0505':"ALC Straight Decode", '0506':"[)(]DIGITAL EX", '0507':"[)(]PLIIx MOVIE", '0508':"DTS + Neo:6", '0509':"ES MATRIX", '050a':"ES DISCRETE", '050b':"DTS-ES 8ch", '050c':"XM HD Surround", '050d':"NEURAL SURR", '050e':"RETRIEVER AIR", '050f':"Neo:X CINEMA", '0510':"ES Neo:X", '0601':"STEREO", '0602':"[)(]PLII MOVIE", '0603':"[)(]PLIIx MOVIE", '0604':"Neo:6 CINEMA", '0605':"STREAM DIRECT NORMAL Straight Decode", '0606':"[)(]DIGITAL EX", '0607':"[)(]PLIIx MOVIE", '0608':"(nothing)", '0609':"ES MATRIX", '060a':"ES DISCRETE", '060b':"DTS-ES 8ch", '060c':"Neo:X CINEMA", '060d':"ES Neo:X", '0701':"STREAM DIRECT PURE 2ch", '0702':"[)(]PLII MOVIE", '0703':"[)(]PLIIx MOVIE", '0704':"Neo:6 CINEMA", '0705':"STREAM DIRECT PURE Straight Decode", '0706':"[)(]DIGITAL EX", '0707':"[)(]PLIIx MOVIE", '0708':"(nothing)", '0709':"ES MATRIX", '070a':"ES DISCRETE", '070b':"DTS-ES 8ch", '070c':"Neo:X CINEMA", '070d':"ES Neo:X", '0881':"OPTIMUM", '0e01':"HDMI THROUGH", '0f01':"MULTI CH IN"}
# (This version expands the abbreviated text descriptions of the original version).
# displayListeningModes = {'0101':"Dolby Pro Logic IIx Movie", '0102':"Dolby Pro Logic II Movie", '0103':"Dolby Pro Logic IIx Music", '0104':"Dolby Pro Logic II Music", '0105':"Dolby Pro Logic IIx Game", '0106':"Dolby Pro Logic II Game", '0107':"Dolby Pro Logic", '0108':"DTS Neo:6 Cinema", '0109':"DTS Neo:6 Music", '010a':"XM HD Surround", '010b':"Neural Surround", '010c':"2-ch Straight Decode", '010d':"Dolby Pro Logic IIz Height", '010e':"Wide Surround Movie", '010f':"Wide Surround Music", '0110':"Stereo", '0111':"DTS Neo:X Cinema", '0112':"DTS Neo:X Music", '0113':"DTS Neo:X Game", '0114':"Neural Surround + DTS Neo:X Cinema", '0115':"Neural Surround + DTS Neo:X Music", '0116':"Neural Surround + DTS Neo:X Games", '0201':"Action", '0202':"Drama", '0203':"Sci-Fi", '0204':"Mono Film", '0205':"Entertainment Show", '0206':"Expanded", '0207':"TV Surround", '0208':"Advanced Game", '0209':"Sports", '020a':"Classical", '020b':"Rock/Pop", '020c':"Unplugged", '020d':"Extended Stereo", '020e':"Phones Surround", '020f':"Front Stage Surround Advanced Focus", '0210':"Front Stage Surround Advanced Wide", '0211':"Sound Retriever Air", '0301':"Dolby Pro Logic IIx Movie + THX", '0302':"Dolby Pro Logic II Movie + THX", '0303':"Dolby Pro Logic + THX Cinema", '0304':"DTS Neo:6 Cinema + THX", '0305':"THX Cinema", '0306':"Dolby Pro Logic IIx Music + THX", '0307':"Dolby Pro Logic II Music + THX", '0308':"Dolby Pro Logic + THX Music", '0309':"DTS Neo:6 Music + THX", '030a':"THX Music", '030b':"Dolby Pro Logic IIx Game + THX", '030c':"Dolby Pro Logic II Game + THX", '030d':"Dolby Pro Logic + THX Games", '030e':"THX Ultra 2 Games", '030f':"THX Select 2 Games", '0310':"THX Games", '0311':"Dolby Pro Logic IIz + THX Cinema", '0312':"Dolby Pro Logic IIz + THX Music", '0313':"Dolby Pro Logic IIz + THX Games", '0314':"DTS Neo:X Cinema + THX Cinema", '0315':"DTS Neo:X Music + THX Music", '0316':"DTS Neo:X Games + THX Games", '0401':"Stereo", '0402':"Dolby Pro Logic II Movie", '0403':"Dolby Pro Logic IIx Movie", '0404':"DTS Neo:6 Cinema", '0405':"Auto Surround Straight Decode", '0406':"Dolby Digital EX", '0407':"Dolby Pro Logic IIx Movie", '0408':"DTS Neo:6", '0409':"DTS-ES Matrix", '040a':"DTS-ES Discrete", '040b':"DTS-ES 8-ch", '040c':"XM HD Surround", '040d':"Neural Surround", '040e':"Retriever Air", '040f':"DTS Neo:X Cinema", '0410':"DTS-ES Neo:X", '0501':"Stereo", '0502':"Dolby Pro Logic II Movie", '0503':"Dolby Pro Logic IIx Movie", '0504':"DTS Neo:6 Cinema", '0505':"Auto Level Control (A.L.C.) Straight Decode", '0506':"Dolby Digital EX", '0507':"Dolby Pro Logic IIx Movie", '0508':"DTS Neo:6", '0509':"DTS-ES Matrix", '050a':"DTS-ES Discrete", '050b':"DTS-ES 8-ch", '050c':"XM HD Surround", '050d':"Neural Surround", '050e':"Retriever Air", '050f':"DTS Neo:X Cinema", '0510':"DTS-ES Neo:X", '0601':"Stereo", '0602':"Dolby Pro Logic II Movie", '0603':"Dolby Pro Logic IIx Movie", '0604':"DTS Neo:6 Cinema", '0605':"Stream Direct Normal Straight Decode", '0606':"Dolby Digital EX", '0607':"Dolby Pro Logic IIx Movie", '0608':"(nothing)", '0609':"DTS-ES Matrix", '060a':"DTS-ES Discrete", '060b':"DTS-ES 8-ch", '060c':"DTS Neo:X Cinema", '060d':"DTS-ES Neo:X", '0701':"Stream Direct Pure 2-ch", '0702':"Dolby Pro Logic II Movie", '0703':"Dolby Pro Logic IIx Movie", '0704':"DTS Neo:6 Cinema", '0705':"Stream Direct Pure Straight Decode", '0706':"Dolby Digital EX", '0707':"Dolby Pro Logic IIx Movie", '0708':"(nothing)", '0709':"DTS-ES Matrix", '070a':"DTS-ES Discrete", '070b':"DTS-ES 8-ch", '070c':"DTS Neo:X Cinema", '070d':"DTS-ES Neo:X", '0881':"Optimum", '0e01':"HDMI Through", '0f01':"Multi-ch In", '1101':"Dolby Pro Logic IIx Movie", '1102':"Dolby Pro Logic IIx Music", '1103':"Dolby Digital EX", '1104':"DTS Neo:6/DTS-HD Neo:6", '1105':"DTS-ES Matrix", '1106':"DTS-ES Discrete", '1107':"DTS-ES 8-ch", '1108':"Multi-ch Straight Decode", '1109':"Dolby Pro Logic IIz Height", '110a':"Wide Surround Movie", '110b':"Wide Surround Music", '110c':"DTS-ES Neo:X", '1301':"THX Surround EX", '1302':"DTS Neo:6 THX Cinema", '1303':"DTS-ES Matrix + THX Cinema", '1304':"DTS-ES Discrete + THX Cinema", '1305':"DTS-ES 8-ch + THX Cinema", '1306':"Dolby Pro Logic IIx Movie + THX", '1307':"THX Ultra 2 Cinema", '1308':"THX Select 2 Cinema", '1309':"THX Cinema", '130a':"DTS Neo:6 + THX Music", '130b':"DTS-ES Matrix + THX Music", '130c':"DTS-ES Discrete + THX Music", '130d':"DTS-ES 8-ch + THX Music", '130e':"Dolby Pro Logic IIx Music + THX", '130f':"THX Ultra 2 Music", '1310':"THX Select 2 Music", '1311':"THX Music", '1312':"DTS Neo:6 + THX Games", '1313':"DTS-ES Matrix + THX Games", '1314':"DTS-ES Discrete + THX Games", '1315':"DTS-ES 8-ch + THX Games", '1316':"Dolby Digital EX + THX Games", '1317':"THX Ultra 2 Games", '1318':"THX Select 2 Games", '1319':"THX Games", '131a':"Dolby Pro Logic IIz + THX Cinema", '131b':"Dolby Pro Logic IIz + THX Music", '131c':"Dolby Pro Logic IIz + THX Games", '131d':"DTS Neo:X + THX Cinema", '131e':"DTS Neo:X + THX Music", '131f':"DTS Neo:X + THX Games"}
# VSX-1021-K Playback Listening Mode mask.
vsx1021kDisplayListeningModeMask = ['010a', '0108', '0109', '0111', '0112', '0113', '0114', '0115', '0116', '1104', '110c', '0301', '0302', '0303', '0304', '0305', '0306', '0307', '0308', '0309', '030a', '030b', '030c', '030d', '030e', '030f', '0310', '0311', '0312', '0313', '0314', '0315', '0316', '1301', '1302', '1303', '1304', '1305', '1306', '1307', '1308', '1309', '130a', '130b', '130c', '130d', '130e', '130f', '1310', '1311', '1312', '1313', '1314', '1315', '1316', '1317', '1318', '1319', '131a', '131b', '131c', '131d', '131e', '131f', '040c', '040f', '0410', '050c', '050f', '0510', '0608', '060c', '060d', '0708', '070c', '070d', '0881', '0f01']
# VSX-1022-K Playback Listening Mode mask.
vsx1022kDisplayListeningModeMask = ['010a', '0108', '0109', '0111', '0112', '0113', '0114', '0115', '0116', '1104', '110c', '0301', '0302', '0303', '0304', '0305', '0306', '0307', '0308', '0309', '030a', '030b', '030c', '030d', '030e', '030f', '0310', '0311', '0312', '0313', '0314', '0315', '0316', '1301', '1302', '1303', '1304', '1305', '1306', '1307', '1308', '1309', '130a', '130b', '130c', '130d', '130e', '130f', '1310', '1311', '1312', '1313', '1314', '1315', '1316', '1317', '1318', '1319', '131a', '131b', '131c', '131d', '131e', '131f', '040c', '040f', '0410', '050c', '050f', '0510', '0608', '060c', '060d', '0708', '070c', '070d', '0881', '0f01']
# VSX-1122-K Playback Listening Mode mask.
vsx1122kDisplayListeningModeMask = ['010a', '010b', '010c', '0108', '0109', '0111', '0112', '0113', '0114', '0115', '0116', '1104', '110c', '110d', '110e', '0301', '0302', '0303', '0304', '0305', '0306', '0307', '0308', '0309', '030a', '030b', '030c', '030d', '030e', '030f', '0310', '0311', '0312', '0313', '0314', '0315', '0316', '1301', '1302', '1303', '1304', '1305', '1306', '1307', '1308', '1309', '130a', '130b', '130c', '130d', '130e', '130f', '1310', '1311', '1312', '1313', '1314', '1315', '1316', '1317', '1318', '1319', '131a', '131b', '131c', '131d', '131e', '131f', '040c', '040d', '040f', '0410', '050c', '050d', '050f', '0510', '0608', '060c', '060d', '0708', '070c', '070d', '0881', '0f01']
# VSX-1123-K Playback Listening Mode mask.
vsx1123kDisplayListeningModeMask = ['010a', '010b', '010c', '0108', '0109', '0111', '0112', '0113', '0114', '0115', '0116', '1104', '110c', '110d', '110e', '0301', '0302', '0303', '0304', '0305', '0306', '0307', '0308', '0309', '030a', '030b', '030c', '030d', '030e', '030f', '0310', '0311', '0312', '0313', '0314', '0315', '0316', '1301', '1302', '1303', '1304', '1305', '1306', '1307', '1308', '1309', '130a', '130b', '130c', '130d', '130e', '130f', '1310', '1311', '1312', '1313', '1314', '1315', '1316', '1317', '1318', '1319', '131a', '131b', '131c', '131d', '131e', '131f', '040c', '040d', '040f', '0410', '050c', '050d', '050f', '0510', '0608', '060c', '060d', '0708', '070c', '070d', '0881', '0f01']
# SC-75 Playback Listening Mode mask.
sc75DisplayListeningModeMask = ['010a', '010b', '010c', '0108', '0109', '0111', '0112', '0113', '0114', '0115', '0116', '1104', '110c', '110d', '110e', '0301', '0302', '0303', '0304', '0305', '0306', '0307', '0308', '0309', '030a', '030b', '030c', '030d', '030e', '030f', '0310', '0311', '0312', '0313', '0314', '0315', '0316', '1301', '1302', '1303', '1304', '1305', '1306', '1307', '1308', '1309', '130a', '130b', '130c', '130d', '130e', '130f', '1310', '1311', '1312', '1313', '1314', '1315', '1316', '1317', '1318', '1319', '131a', '131b', '131c', '131d', '131e', '131f', '040c', '040d', '040f', '0410', '050c', '050d', '050f', '0510', '0608', '060c', '060d', '0708', '070c', '070d', '0881', '0f01']
# Preferred Video Resolution ID to name map.
videoResolutionPrefs = {'00':"AUTO", '01':"PURE", '02':"Reserved", '03':"480/576p", '04':"720p", '05':"1080i", '06':"1080p", '07':"1080/24p"}
# Video Resolution ID to name map.
videoResolutions = {'00':"", '01':"480/60i", '02':"576/50i", '03':"480/60p", '04':"576/50p", '05':"720/60p", '06':"720/50p", '07':"1080/60i", '08':"1080/50i", '09':"1080/60p", '10':"1080/50p", '11':"1080/24p", '12':"4Kx2K/24Hz", '13':"4Kx2K/25Hz", '14':"4Kx2K/30Hz", '15':"4Kx2K/24Hz (SMPTE)"}
# Audio Input Signal ID to name map.
audioInputFormats = {'00':"ANALOG", '01':"ANALOG", '02':"ANALOG", '03':"PCM", '04':"PCM", '05':"DOLBY DIGITAL", '06':"DTS", '07':"DTS-ES Matrix", '08':"DTS-ES Discrete", '09':"DTS 96/24", '10':"DTS 96/24 ES Matrix", '11':"DTS 96/24 ES Discrete", '12':"MPEG-2 AAC", '13':"WMA9 Pro", '14':"DSD->PCM", '15':"HDMI THROUGH", '16':"DOLBY DIGITAL PLUS", '17':"DOLBY TrueHD", '18':"DTS EXPRESS", '19':"DTS-HD Master Audio", '20':"DTS-HD High Resolution", '21':"DTS-HD High Resolution", '22':"DTS-HD High Resolution", '23':"DTS-HD High Resolution", '24':"DTS-HD High Resolution", '25':"DTS-HD High Resolution", '26':"DTS-HD High Resolution", '27':"DTS-HD Master Audio", '28':"DSD (HDMI/File)", '64':"MP3", '65':"WAV", '66':"WMA", '67':"MPEG4-AAC", '68':"FLAC", '69':"ALAC (Apple Lossless)", '70':"AIFF", '71':"DSD (USB)"}
# Audio Input Frequency ID to frequency (in kHz) map.
audioInputFrequencies = {'00':"32 kHz", '01':"44.1 kHz", '02':"48 kHz", '03':"88.2 kHz", '04':"96 kHz", '05':"176.4 kHz", '06':"192 kHz", '07':"-", '32':"2.8 MHz", '33':"5.6 MHz"}
audioOutputFrequencies = {'00':"32 kHz", '01':"44.1 kHz", '02':"48 kHz", '03':"88.2 kHz", '04':"96 kHz", '05':"176.4 kHz", '06':"192 kHz", '07':"-", '32':"2.8 MHz", '33':"5.6 MHz"}
# Audio Channel list.
audioChannels = ['L', 'C', 'R', 'SL', 'SR', 'SBL', 'S', 'SBR', 'LFE', 'FHL', 'FHR', 'FWL', 'FWR', 'XL', 'XC', 'XR', '(future)', '(future)', '(future)', '(future)', '(future)']
# Map button commands for Indigo actions to actual button names for display.
remoteButtonNames = {'CUP':"Cursor UP", 'CDN':"Cursor DOWN", 'CRI':"Cursor RIGHT", 'CLE':"Cursor LEFT", 'CEN':"ENTER", 'CRT':"RETURN", '33NW':"CLEAR", 'HM':"HOME", 'STS':"DISPLAY", '00IP':"PLAY", '01IP':"PAUSE", '02IP':"STOP", '03IP':"PREVIOUS", '04IP':"NEXT", '07IP':"REPEAT", '08IP':"SHUFFLE", '19SI':"MENU", '00SI':"0", '01SI':"1", '02SI':"2", '03SI':"3", '04SI':"4", '05SI':"5", '06SI':"6", '07SI':"7", '08SI':"8", '09SI':"9"}
# Specify the order in which button names should appear in the UI menu.
#   This is necessary because, until Python 2.7 (Indigo uses versoin 2.5),
#   Python dictionaries (like remoteButtonNames) cannot be itterated
#   through in a set order.
remoteButtonNamesOrder = ['CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', '33NW', 'HM', 'STS', '00IP', '01IP', '02IP', '03IP', '04IP', '07IP', '08IP', '19SI', '00SI', '01SI', '02SI', '03SI', '04SI', '05SI', '06SI', '07SI', '08SI', '09SI']

# Connection retry delay (in approximately 1/10th second increments).
connectionRetryDelay = 300

################################################################################
class Plugin(indigo.PluginBase):
	########################################
	# Class Globals
	########################################
	
	# Dictionary of device telnet sessions.
	tn = dict()
	# List of devices whose complete status is being updated.
	devicesBeingUpdated = []
	# Dictionary of device connection waiting counters
	#   (device ID:1/10 second count)
	devicesWaitingToConnect = dict()
	
	########################################
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.debug = pluginPrefs.get('showDebugInfo', False)
		self.deviceList = []
		self.volumeDeviceList = []
		# Load the update checker module.
		self.updater = indigoPluginUpdateChecker.updateChecker(self, 'http://www.nathansheldon.com/files/PluginVersions/Pioneer-Receiver.html')
	
	########################################
	def __del__(self):
		indigo.PluginBase.__del__(self)
	
	########################################
	# Class-Supported Methods
	########################################
	
	# Device Start
	########################################
	def startup(self):
		# Perform an initial version check.
		self.updater.checkVersionPoll()
		
	########################################
	def deviceCreated(self, device):
		try:
			self.debugLog("deviceCreated called: " + str(device))
		except Exception, e:
			self.debugLog("deviceCreated called: " + device.name + " (Unable to display device states due to error: " + str(e) + ")")
		
		#
		# VSX-1021-K, VSX-1022-K, VSX-1122-K, VSX-1123-K, SC-75 Devices
		#
		if device.deviceTypeId == "vsx1021k" or device.deviceTypeId == "vsx1022k" or device.deviceTypeId == "vsx1122k" or device.deviceTypeId == "vsx1123k" or device.deviceTypeId == "sc75":
			# If the device has the same IP address as another device,
			#   generate an error.
			self.debugLog("deviceCreated: Testing to see if using duplicate IP.")
			devProps = device.pluginProps
			for deviceId in self.deviceList:
				self.debugLog("deviceCreated: checking device " + indigo.devices[deviceId].name + " (ID " + str(deviceId) + " address " + indigo.devices[deviceId].pluginProps['address'] + ".")
				if (deviceId != device.id) and (devProps['address'] == indigo.devices[deviceId].pluginProps['address']):
					self.errorLog(device.name + " is configured to connect on the same IP address as \"" + indigo.devices[deviceId].name + "\". Only one Indigo device can connect to the same Pioneer receiver at a time. Change the IP address of, or remove one of the devices.")
					self.updateDeviceState(device, 'status', "error")
					self.updateDeviceState(device, 'connected', False)
					indigo.device.enable(device, False)
			
			# Start the device.
			if device.enabled:
				self.deviceStartComm(device)
		
		#
		# Virtual Volume Controller Device
		#
		if device.deviceTypeId == "virtualVolume":
			self.deviceStartComm(device)
	
	########################################
	def deviceStartComm(self, device):
		try:
			self.debugLog("deviceStartComm called: " + str(device))
		except Exception, e:
			self.debugLog("deviceStartComm called: " + device.name + " (Unable to display device states due to error: " + str(e) + ")")
		#
		# VSX-1021-K Device
		#
		if device.deviceTypeId == "vsx1021k":
			# Prior to version 0.9.7, the "onOffState" state did not exist. If
			#   that state does not exist, force an update of the device.
			if not device.states.get('onOffState', False):
				self.debugLog(u"Updating device state list.")
				# This will forece Indigo to update the device with the new states.
				device.stateListOrDisplayStateIdChanged()
			
			# Add this device to the list of devices associated with this plugin.
			if device.id not in self.deviceList:
				self.debugLog("deviceStartComm: adding vsx1021k deviceId " + str(device.id) + " to deviceList.")
				self.deviceList.append(device.id)
		
		#
		# VSX-1022-K Device
		#
		if device.deviceTypeId == "vsx1022k":
			# Add this device to the list of devices associated with this plugin.
			if device.id not in self.deviceList:
				self.debugLog("deviceStartComm: adding vsx1022k deviceId " + str(device.id) + " to deviceList.")
				self.deviceList.append(device.id)
		
		#
		# VSX-1122-K Device
		#
		if device.deviceTypeId == "vsx1122k":
			# Add this device to the list of devices associated with this plugin.
			if device.id not in self.deviceList:
				self.debugLog("deviceStartComm: adding vsx1122k deviceId " + str(device.id) + " to deviceList.")
				self.deviceList.append(device.id)
		
		#
		# VSX-1123-K Device
		#
		if device.deviceTypeId == "vsx1123k":
			# Add this device to the list of devices associated with this plugin.
			if device.id not in self.deviceList:
				self.debugLog("deviceStartComm: adding vsx1123k deviceId " + str(device.id) + " to deviceList.")
				self.deviceList.append(device.id)
		
		#
		# SC-75 Device
		#
		if device.deviceTypeId == "sc75":
			# Add this device to the list of devices associated with this plugin.
			if device.id not in self.deviceList:
				self.debugLog("deviceStartComm: adding sc75 deviceId " + str(device.id) + " to deviceList.")
				self.deviceList.append(device.id)
		
		#
		# Virtual Volume Controller Device
		#
		if device.deviceTypeId == "virtualVolume":
			# Add this device to the list of volume devices associated with this plugin.
			if device.id not in self.volumeDeviceList:
				self.debugLog("deviceStartComm: adding virtualVolume deviceId " + str(device.id) + " to volumeDeviceList.")
				self.volumeDeviceList.append(device.id)
			# Update the device to the value of the receiver device control to which it is
			#   configured to virtualize.
			receiverDeviceId = int(device.pluginProps.get('receiverDeviceId', ""))
			controlDestination = device.pluginProps.get('controlDestination', "")
			if receiverDeviceId > 0 and len(controlDestination) > 0:
				# Query the receiver devices for volume and mute status.
				#   This will update the virtual volume controller.
				receiver = indigo.devices[receiverDeviceId]
				if receiver.states['connected']:
					self.getVolumeStatus(receiver)
					self.getMuteStatus(receiver)
	
	########################################
	def deviceStopComm(self, device):
		self.debugLog("deviceStopComm called: " + device.name)
		#
		# VSX-1021-K Device
		#
		if device.deviceTypeId == "vsx1021k":
			# Remove this device from the list of devices associated with this plugin.
			if device.id in self.deviceList:
				self.deviceList.remove(device.id)
			# Make sure it's disconnected.
			if device.states['connected']:
				self.disconnect(device)
		
		#
		# VSX-1022-K Device
		#
		if device.deviceTypeId == "vsx1022k":
			# Remove this device from the list of devices associated with this plugin.
			if device.id in self.deviceList:
				self.deviceList.remove(device.id)
			# Make sure it's disconnected.
			if device.states['connected']:
				self.disconnect(device)
		
		#
		# VSX-1122-K Device
		#
		if device.deviceTypeId == "vsx1122k":
			# Remove this device from the list of devices associated with this plugin.
			if device.id in self.deviceList:
				self.deviceList.remove(device.id)
			# Make sure it's disconnected.
			if device.states['connected']:
				self.disconnect(device)
		
		#
		# VSX-1123-K Device
		#
		if device.deviceTypeId == "vsx1123k":
			# Remove this device from the list of devices associated with this plugin.
			if device.id in self.deviceList:
				self.deviceList.remove(device.id)
			# Make sure it's disconnected.
			if device.states['connected']:
				self.disconnect(device)
		
		#
		# SC-75 Device
		#
		if device.deviceTypeId == "sc75":
			# Remove this device from the list of devices associated with this plugin.
			if device.id in self.deviceList:
				self.deviceList.remove(device.id)
			# Make sure it's disconnected.
			if device.states['connected']:
				self.disconnect(device)
		
		#
		# Virtual Volume Controller Device
		#
		if device.deviceTypeId == "virtualVolume":
			# Remove this device from the list of level devices associated with this plugin.
			if device.id in self.volumeDeviceList:
				self.volumeDeviceList.remove(device.id)
	
	########################################
	def didDeviceCommPropertyChange(self, origDev, newDev):
		# Automatically called by plugin host when device properties change.
		self.debugLog("didDeviceCommPropertyChange called.")
		#
		# VSX-1021-K, VSX-1022-K, VSX-1122-K, VSX-1123-K, or SC-75
		#
		if origDev.deviceTypeId == "vsx1021k" or newDev.deviceTypeId == "vsx1022k" or newDev.deviceTypeId == "vsx1122k" or newDev.deviceTypeId == "vsx1123k" or newDev.deviceTypeId == "sc75":
			if origDev.pluginProps['address'] != newDev.pluginProps['address']:
				return True
			return False
		else:
			if origDev.pluginProps != newDev.pluginProps:
				return True
			return False
	
	########################################
	def runConcurrentThread(self):
		self.debugLog("runConcurrentThread called.")
		loopCount = 0
		#
		# Continuously loop through all receiver devices. Obtain
		#   any data that they might be providing and process it.
		#
		try:
			while True:
				# Check for newer plugin versions.
				if loopCount % 100 == 0:
					# Only check every 10 seconds.
					self.updater.checkVersionPoll()
					loopCount = 0
				# Increment loop counter.
				loopCount += 1
				
				# self.debugLog("runConcurrentThread while loop started.")
				self.sleep(0.1)
				# Cycle through each receiver device.
				for deviceId in self.deviceList:
					response     = ""
					responseLine = ""
					result       = ""
					
					connected = indigo.devices[deviceId].states.get('connected', False)
					
					# Only proceed if we're connected.
					if connected:
						# Remove the device ID from the devicesWaitingToConnect dictionary.
						if self.devicesWaitingToConnect.get(deviceId, -1) > -1:
							del self.devicesWaitingToConnect[deviceId]
						# Call the readData method with the device instance
						# self.debugLog("Reading data for " + indigo.devices[deviceId].name + ".")
						response = self.readData(indigo.devices[deviceId])
						# If a response was returned, process it.
						if response != "":
							# There is often more than one line.  Process all of them.
							for responseLine in response.splitlines():
								result = self.processResponse(indigo.devices[deviceId], responseLine)
								# If there was a result, send it to the log.
								if result != "":
									indigo.server.log(result, indigo.devices[deviceId].name)
					else:
						# Since we're not connected, try to connect.
						self.connect(indigo.devices[deviceId])
						
		except self.StopThread:
			self.debugLog("runConcurrentThread stopped.")
			# Cycle through each receiver device.
			for deviceId in self.deviceList:
				self.disconnect(indigo.devices[deviceId])
			pass
		
		self.debugLog("runConcurrentThread exiting.")
	
	
	########################################
	# Core Custom Methos
	########################################
	
	# Update Device State
	########################################
	def updateDeviceState(self, device, state, newValue):
		# Change the device state on the server
		#   if it's different than the current state.
		if (newValue != device.states[state]):
			try:
				self.debugLog("updateDeviceState: Updating device " + device.name + " state: " + str(state) + " = " + str(newValue))
			except Exception, e:
				self.debugLog("updateDeviceState: Updating device " + device.name + " state: (Unable to display state due to error: " + str(e) + ")")
			# If this is a floating point number, specify the maximum
			#   number of digits to make visible in the state.  Everything
			#   in this plugin only needs 1 decimal place of precission.
			#   If this isn't a floating point value, don't specify a number
			#   of decimal places to display.
			if newValue.__class__.__name__ == 'float':
				device.updateStateOnServer(key=state, value=newValue, decimalPlaces=1)
			else:
				device.updateStateOnServer(key=state, value=newValue)
	
	# Update Device Properties
	########################################
	def updateDeviceProps(self, device, newProps):
		# Change the properties for this device that are
		#   stored on the server.
		if device.pluginProps != newProps:
			self.debugLog("updateDeviceProps: Updating device " + device.name + " properties.")
			device.replacePluginPropsOnServer(newProps)
	
	# Connect to a Receiver Device
	########################################
	def connect(self, device):
		# Display this debug message only once every 50 times the method is called.
		if self.devicesWaitingToConnect.get(device.id, 0)%10 == 0 or self.devicesWaitingToConnect.get(device.id, 0) == 0:
			self.debugLog("connect method called.")
		
		connected = device.states['connected']
		devProps = device.pluginProps
		connecting = devProps.get('tryingToConnect', False)
		# Get the device address.
		receiverIp = devProps['address']
		
		# Display these debug messages only once every 50 times the method is called.
		if self.devicesWaitingToConnect.get(device.id, 0)%50 == 0:
			self.debugLog("connect: " + device.name + " connected? " + str(connected))
			self.debugLog("connect: " + device.name + " connecting? " + str(connecting))
		
		# Only try to connect if we're not already connected and aren't
		#   trying to connect.
		if not connected and not connecting:
			connecting = True
			# Update the device properties just in case the properties aren't up to date.
			devProps['tryingToConnect'] = True
			self.updateDeviceProps(device, devProps)
			
			# Try to connect to the receiver.
			self.debugLog("connect: Connecting to " + device.name + " at " + receiverIp)
			try:
				self.updateDeviceState(device, 'status', "connecting")
				
				# Use the correct TCP port number based on device type.
				if device.deviceTypeId == "vsx1022k":
					# The VSX-1022-K only accepts connections on port 8102.
					self.tn[device.id] = telnetlib.Telnet(receiverIp, 8102)
				else:
					# All other receivers accept connections on the standard telnet port.
					self.tn[device.id] = telnetlib.Telnet(receiverIp)
					
				# Connection established if we get to this point.
				indigo.server.log(u"Connection established.", device.name)
				connected = True
				# Upon initial connection to a Pioneer receiver, it is necessary to
				#   "prime" the connection by simply sending a CR and LF.
				self.tn[device.id].write("\r\n")
				connecting = False
				# Update the device state on the server.
				self.updateDeviceState(device, 'status', "connected")
				self.updateDeviceState(device, 'connected', True)
				devProps['tryingToConnect'] = False
				self.updateDeviceProps(device, devProps)
				# Remove the device ID from the list of devices waiting to connect.
				waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
				if waitingCount > -1:
					del self.devicesWaitingToConnect[device.id]
				
				# Now that we're connected, gather receiver status information.
				self.getReceiverStatus(device)
			
			except Exception, e:
				# If this was a connection refused error, report it.
				if "(61," in str(e):
					self.errorLog("Connection refused when trying to connect to " + device.name + ". Will try again in " + str(float((connectionRetryDelay / 10))) + " seconds.")
					# Increment the number of times we attempted to connect but reached
					#   this point because we were already trying to connect.
					waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
					if waitingCount > -1:
						self.devicesWaitingToConnect[device.id] += 1
					else:
						self.devicesWaitingToConnect[device.id] = 1
				else:
					self.errorLog("Unable to establish a connection to " + device.name + ": " + str(e) + ". Will try again in " + str(float(connectionRetryDelay / 10)) + " seconds.")
					# Increment the number of times we attempted to connect but reached
					#   this point because we were already trying to connect.
					waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
					if waitingCount > -1:
						self.devicesWaitingToConnect[device.id] += 1
					else:
						self.devicesWaitingToConnect[device.id] = 1
			except self.StopThread:
				self.debugLog("connect: Cancelling connection attempt.")
				return
				pass
		
		elif not connected and connecting:
			# Increment the number of times we attempted to connect but reached
			#   this point because we were already trying to connect.
			waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
			if waitingCount > -1:
				self.devicesWaitingToConnect[device.id] += 1
			else:
				self.devicesWaitingToConnect[device.id] = 1
			# If the number of times we've waited to connect is greater than
			#   connectionRetryDelay, then reset the tryingToConnect property.
			if self.devicesWaitingToConnect.get(device.id, -1) > connectionRetryDelay:
				connecting = False
				devProps['tryingToConnect'] = False
				self.updateDeviceProps(device, devProps)
				# Remove the device ID from the list of devices waiting to connect.
				waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
				if waitingCount > -1:
					del self.devicesWaitingToConnect[device.id]
					self.debugLog("connect: Re-connect wait period over. Will try to connect next time the connect method is called.")
				else:
					self.debugLog("connect: Attempt to connect to " + device.name + " skipped because we're still trying to connect to it.")
		
		elif connected:
			self.debugLog("connect: Attempt to connect to " + device.name + " skipped because we're already connected to it.")
			connected = True
			# Update the device to reflect this.
			self.updateDeviceState(device, 'connected', True)
			devProps['tryingToConnect'] = False
			self.updateDeviceProps(device, devProps)
			# Remove the device ID from the list of devices waiting to connect.
			waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
			if waitingCount > -1:
				del self.devicesWaitingToConnect[device.id]
		
		# Display wait count in debug log.
		if self.devicesWaitingToConnect.get(device.id, 0)%50 == 0:
			self.debugLog("connect: Connection wait count: " + str(self.devicesWaitingToConnect.get(device.id, 0)))
	
	# Disconnect from a Receiver Device
	#########################################
	def disconnect(self, device):
		self.debugLog("disconnect method called.")
		
		connected = device.states['connected']
		devProps = device.pluginProps
		connecting = devProps.get('tryingToConnect', False)
		
		# Disconnect the telnet session.
		try:
			self.tn[device.id].close()
			# Update the "status" device state.
			self.updateDeviceState(device, 'status', "disconnected")
			# Update the "connected" state on the server as well.
			self.updateDeviceState(device, 'connected', False)
			# Make sure the tryingToConnect device property is not on.
			devProps['tryingToConnect'] = False
			self.updateDeviceProps(device, devProps)
			self.debugLog("disconnect: " + device.name + " telnet connection is now closed.")
			# Remove the device ID from the list of devices waiting to connect (if it's in there).
			waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
			if waitingCount > -1:
				del self.devicesWaitingToConnect[device.id]
		except EOFError:
			self.debugLog("disconnect: Connection to " + device.name + " is already closed.")
			self.updateDeviceState(device, 'status', "disconnected")
			self.updateDeviceState(device, 'connected', False)
			devProps['tryingToConnect'] = False
			self.updateDeviceProps(device, devProps)
			self.debugLog("disconnect: " + device.name + " connection is already closed.")
			# Remove the device ID from the list of devices waiting to connect (if it's in there).
			waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
			if waitingCount > -1:
				del self.devicesWaitingToConnect[device.id]
		except Exception, e:
			self.errorLog("disconnect: Error disconnecting from " + device.name + ": " + str(e))
			self.updateDeviceState(device, 'status', "error")
			self.updateDeviceState(device, 'connected', False)
			devProps['tryingToConnect'] = False
			self.updateDeviceProps(device, devProps)
			self.debugLog("disconnect: " + device.name + " is now disconnected (error while disconnecting).")
			# Remove the device ID from the list of devices waiting to connect (if it's in there).
			waitingCount = self.devicesWaitingToConnect.get(device.id, -1)
			if waitingCount > -1:
				del self.devicesWaitingToConnect[device.id]
	
	
	#########################################
	# Send a Command
	#########################################
	def sendCommand(self, device, command):
		# Get the device type. Future versions of this plugin will support other receiver models.
		devType = device.deviceTypeId
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if devType == "virtualVolume":
			self.errorLog(u"Device \"" + dev.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command \"" + str(command) + "\" to a Pioneer receiver instead of this device.")
			return None
		
		# Get the device current connection status.
		connected = device.states['connected']
		# Get the device properties.
		devProps = device.pluginProps
		connecting = devProps.get('tryingToConnect', False)
		
		# Make sure the command is a string.
		command = str(command)
		# Make sure there's only one set of a carriage return and line feed.
		command = command.rstrip("\r\n")
		# SPECIAL CIRCUMSTANCE:
		#   The "TAC", "TFI" and "TFD" commands change the Tuner frequency. We need to
		#   clear the "tunerPreset" state if either of these commands are being sent.
		if command in ['TAC', 'TFI', 'TFD']:
			self.updateDeviceState(device, "tunerPreset", "")
		# Now send the command.
		self.debugLog(u"sendCommand: Telling " + device.name + u": " + command)
		command = command + "\r"
		
		# Only proceed if we're not trying to connect.
		if connected:
			try:
				self.tn[device.id].write(command)
			except EOFError:
				# Connection is closed. Update status and try to re-open.
				self.errorLog(u"Connection to " + device.name + u" lost while trying to send data. Will attempt to connect.")
				self.updateDeviceState(device, 'status', "disconnected")
				self.updateDeviceState(device, 'connected', False)
				self.connect(device)
			except Exception, e:
				# Unknown error.
				self.errorLog(u"Failed to send data to " + device.name + u": " + str(e))
				self.updateDeviceState(device, 'status', "error")
				self.updateDeviceState(device, 'connected', False)
		elif not connected and not connecting:
			# Show an error and try to connect.
			self.errorLog(u"Unable to send command to " + device.name + u". It is not connected. Attempting to re-connect.")
			self.connect(device)
		elif not connected and connecting:
			# Show an error indicating that we're still trying to connect.
			self.errorLog(u"Unable to send command to " + device.name + u". Still trying to connect to it.")
	
	
	#########################################
	# Read Data from a Receiver Connection
	#########################################
	def readData(self, device):
		
		response = ""
		
		# Get the device connection state and properties.
		connected = device.states['connected']
		devProps = device.pluginProps
		connecting = devProps.get('tryingToConnect', False)
		
		# Only proceed if we're connected.
		if connected:
			try:
				# Read the data and return it without blocking.
				response = self.tn[device.id].read_very_eager()
				# Strip the CR and LF from the end of the response.
				response = response.rstrip("\r\n")
				# Force the response to be an ASCII string.
				response = unicode(response, errors='replace')
				if response != "":
					self.debugLog("readData: " + device.name + " said: " + response)
			except EOFError:
				# Connection is closed, try to re-open.
				self.errorLog(u"Connection to " + device.name + u" lost while trying to receive data. Trying to re-connect.")
				self.updateDeviceState(device, 'status', "disconnected")
				self.updateDeviceState(device, 'connected', False)
				self.connect(device)
			except Exception, e:
				# Unknown error.
				self.errorLog(u"Failed to receive data from " + device.name + u": " + str(e))
				self.updateDeviceState(device, 'status', "error")
				self.updateDeviceState(device, 'connected', False)
		elif not connected and not connecting:
			# Show an error and try to connect.
			self.errorLog(u"Unable to read data from " + device.name + u". It is not connected. Attempting to re-connect.")
			self.connect(device)
		elif not connected and connecting:
			# Show an error indicating that we're still trying to connect.
			self.errorLog(u"Unable to read data from " + device.name + u". Still trying to connect to it.")
		
		return response
	
	#########################################
	# Process a Command Response
	#########################################
	def processResponse(self, device, response):
		# Update the Indigo receiver device based on the
		#   response from the receiver.
		self.debugLog("processResponse: from " + device.name + ".")
		
		# Get the type of device.  In the future, we'll support different receiver types.
		devType  = device.deviceTypeId
		
		# Make a copy of the device properties so we can change them if needed.
		devProps = device.pluginProps
		
		result   = ""
		state    = ""
		newValue = ""
		
		#
		# Test for each type of command response.
		#
		
		#
		# ERRORS
		#
		if response == "E02":
			state = "status"
			newValue = "error"
			self.errorLog(device.name + ": not available now.")
		elif response == "E03":
			state = "status"
			newValue = "error"
			self.errorLog(device.name + ": invalid command.")
		elif response == "E04":
			state = "status"
			newValue = "error"
			self.errorLog(device.name + ": command error.")
		elif response == "E06":
			state = "status"
			newValue = "error"
			self.errorLog(device.name + ": parameter error.")
		elif response == "B00":
			state = "status"
			newValue = "busy"
			self.errorLog(device.name + ": system busy.")
		#
		# General Acknowledgement Response
		#
		elif response == "R":
			self.debugLog("processResponse: " + device.name + ": command acknowledged.")
		#
		# Zone 1 Specific Items
		#
		elif response.startswith("PWR"):
			# Power (zone 1) status.
			state = "zone1power"
			if response == "PWR0":
				# Power (zone 1) is on.
				newValue = True
				# Only set a result message if this is a change from the current state.
				if not device.states['zone1power']:
					# Set the result to be logged.
					result = "power (zone 1): on"
				# Update the onOffState.
				self.updateDeviceState(device, 'onOffState', True)
				# If zone 2 is also on, make sure the status reflects that.
				if device.states['zone2power']:
					# Set the "status" state on the server.
					self.updateDeviceState(device, "status", "on (zones 1+2)")
				else:
					self.updateDeviceState(device, "status", "on (zone 1)")
			elif response == "PWR1":
				# Power (zone 1) is off.
				newValue = False
				if device.states['zone1power']:
					result = "power (zone 1): off"
				# If zone 2 is on, make sure the status reflects that.
				if device.states['zone2power']:
					self.updateDeviceState(device, "status", "on (zone 2)")
				else:
					self.updateDeviceState(device, "status", "off")
					# Update the onOffState.
					self.updateDeviceState(device, 'onOffState', False)
				# Clear all the state values.
				#   Set "zone1volume" to -999.0 dB.
				self.updateDeviceState(device, "zone1volume", -999.0)
				#   Set "zone1source" to 0 (no source)
				self.updateDeviceState(device, "zone1source", 0)
				#   Set "zone1sourceName to (no source)
				self.updateDeviceState(device, "zone1sourceName", "")
				#   Set all channel levels to 0.
				for theChannel, theName in channelVolumes.items():
					self.updateDeviceState(device, theName, 0)
				#   Set MCACC Memory number to 0.
				self.updateDeviceState(device, "mcaccMemory", 0)
				#   Clear the MCACC memory name.
				self.updateDeviceState(device, "mcaccMemoryName", "")
				# Look for Virtual Volume Controllers that might need setting to zero.
				for thisId in self.volumeDeviceList:
					virtualVolumeDevice = indigo.devices[thisId]
					controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
					if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone1volume":
						self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
			elif response == "PWR2":
				# Power (zone 1) is off (network standby mode, only VSX-1022-K reports this).
				newValue = False
				if device.states['zone1power']:
					result = "power (zone 1): off"
				# If zone 2 is on, make sure the status reflects that.
				if device.states['zone2power']:
					self.updateDeviceState(device, "status", "on (zone 2)")
				else:
					self.updateDeviceState(device, "status", "off")
					# Update the onOffState.
					self.updateDeviceState(device, 'onOffState', False)
				# Clear all the state values.
				#   Set "zone1volume" to -999.0 dB.
				self.updateDeviceState(device, "zone1volume", -999.0)
				#   Set "zone1source" to 0 (no source)
				self.updateDeviceState(device, "zone1source", 0)
				#   Set "zone1sourceName to (no source)
				self.updateDeviceState(device, "zone1sourceName", "")
				#   Set all channel levels to 0.
				for theChannel, theName in channelVolumes.items():
					self.updateDeviceState(device, theName, 0)
				#   Set MCACC Memory number to 0.
				self.updateDeviceState(device, "mcaccMemory", 0)
				#   Clear the MCACC memory name.
				self.updateDeviceState(device, "mcaccMemoryName", "")
				# Look for Virtual Volume Controllers that might need setting to zero.
				for thisId in self.volumeDeviceList:
					virtualVolumeDevice = indigo.devices[thisId]
					controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
					if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone1volume":
						self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
		elif response.startswith("MUT"):
			# Mute (zone 1) status.
			state = "zone1mute"
			if response == "MUT0":
				# Mute is on.
				newValue = True
				if not device.states['zone1mute']:
					result = "mute (zone 1): on"
				# Look for Virtual Volume Controllers that might need updating.
				for thisId in self.volumeDeviceList:
					virtualVolumeDevice = indigo.devices[thisId]
					controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
					if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone1volume":
						self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
			elif response == "MUT1":
				# Mute is off.
				newValue = False
				if device.states['zone1mute']:
					result = "mute (zone 1): off"
				# Look for Virtual Volume Controllers that might need updating.
				for thisId in self.volumeDeviceList:
					virtualVolumeDevice = indigo.devices[thisId]
					controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
					if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone1volume":
						# Update the Virtual Volume Controller to match current volume.
						#   Get the receiver's volume.
						theVolume = float(device.states[controlDestination])
						# Convert the current volume of the receiver to a percentage
						# to be displayed as a brightness level. If the volume is
						# less than -80.5, the receiver is off and the brightness should be 0.
						if float(theVolume) < -80.5:
							theVolume = -80.5
						theVolume = int(100-round(theVolume/-80.5*100, 0))
						self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', theVolume)
		elif response.startswith("FN"):
			# Source/function (zone 1) status.
			state = "zone1source"
			newValue = int(response[2:])
			# Check to see if zone 1 is already set to this input or if zone 1
			#   power is off.  In either case, ignore this update.
			if device.states[state] == newValue or device.states['zone1power'] == False:
				state = ""
				newValue = ""
		elif response.startswith("VOL"):
			# Volume (zone 1) status.
			state = "zone1volume"
			# Convert to dB.
			newValue = float(response[3:]) * 1.0
			newValue = -80.5 + 0.5 * newValue
			# Volume is at minimum or zone 1 power is off, volume is meaningless, so set it to minimum.
			if (newValue < -80.0) or (not device.states['zone1power']):
				newValue = -999.0
				result = "volume (zone 1): minimum."
			else:
				result = "volume (zone 1): " + str(newValue) + " dB"
			# Look for Virtual Volume Controllers that might need updating.
			self.debugLog("processResponse: Looking for connected Virtual Volume Controllers. volumeDeviceList: " + str(self.volumeDeviceList))
			for thisId in self.volumeDeviceList:
				virtualVolumeDevice = indigo.devices[thisId]
				self.debugLog("processResponse: Examining Virtual Volume Controller ID " + str(thisId))
				self.debugLog("processResponse: " + str(virtualVolumeDevice))
				controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
				if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone1volume":
					self.debugLog("processResponse: Virtual Volume Controller ID " + str(thisId) + " is connected.")
					# Update the Virtual Volume Controller to match new volume.
					theVolume = newValue
					# Convert the current volume of the receiver to a percentage
					# to be displayed as a brightness level. If the volume is
					# less than -80.5, the receiver is off and the brightness should be 0.
					if theVolume < -80.0:
						theVolume = -80.5
					theVolume = int(100-round(theVolume/-80.5*100, 0))
					self.debugLog("processResponse: updating Virtual Volume Device ID " + str(thisId) + " brightness level to " + str(theVolume))
					self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', theVolume)
		#
		# Zone 2 Specific Items
		#
		elif response.startswith("APR"):
			# Power (zone 2) status.
			state = "zone2power"
			if response == "APR0":
				# Power (zone 2) is on.
				newValue = True
				if not device.states['zone2power']:
					result = "power (zone 2): on"
				# Update the onOffState.
				self.updateDeviceState(device, 'onOffState', True)
				# If main power (zone 1) is on, set the status to reflect that.
				if device.states['zone1power']:
					self.updateDeviceState(device, "status", "on (zones 1+2)")
				else:
					self.updateDeviceState(device, "status", "on (zone 2)")
			elif response == "APR1":
				# Power (zone 2) is off.
				newValue = False
				if device.states['zone2power']:
					result = "power (zone 2): off"
				# If main power (zone 1) is on, make sure the status reflects that.
				if device.states['zone1power']:
					self.updateDeviceState(device, "status", "on (zone 1)")
				else:
					self.updateDeviceState(device, "status", "off")
					# Update the onOffState.
					self.updateDeviceState(device, 'onOffState', False)
				# Clear all the state values.
				#   Set "zone1volume" to -999 dB.
				self.updateDeviceState(device, "zone2volume", -999)
				#   Set "zone1source" to 0 (no source)
				self.updateDeviceState(device, "zone2source", 0)
				#   Set "zone1sourceName to (no source)
				self.updateDeviceState(device, "zone2sourceName", "")
				# Clear the tuner settings if zone 1 isn't using it.
				if device.states['zone1source'] != 2:
					self.updateDeviceState(device, 'tunerPreset', "")
					self.updateDeviceState(device, 'tunerFrequency', 0)
					self.updateDeviceState(device, 'tunerFrequencyText', "")
					self.updateDeviceState(device, 'tunerBand', "")
				# Look for Virtual Volume Controllers that might need setting to zero.
				for thisId in self.volumeDeviceList:
					virtualVolumeDevice = indigo.devices[thisId]
					controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
					if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone2volume":
						self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
		elif response.startswith("Z2F"):
			# Source/function (zone 2) status.
			state = "zone2source"
			newValue = int(response[3:])
			# Check to see if zone 2 is already set to this input or if zone 2
			#   power is off.  If either is the case, ignore this update.
			if device.states[state] == newValue or device.states['zone2power'] == False:
				state = ""
				newValue = ""
		elif response.startswith("Z2MUT"):
			# Mute (zone 2) status.
			state = "zone2mute"
			# If the speaker system arranement is not set to A + Zone 2, zone
			#   mute and volume settings returned by the receiver are meaningless.
			#   Set the state on the server to properly reflect this.
			if device.states['speakerSystem'] == "A + Zone 2":
				if response == "Z2MUT0":
					# Mute is on.
					newValue = True
					result = "mute (zone 2): on"
					# Look for Virtual Volume Controllers that might need updating.
					for thisId in self.volumeDeviceList:
						virtualVolumeDevice = indigo.devices[thisId]
						controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
						if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone2volume":
							self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
				elif response == "Z2MUT1":
					# Mute is off.
					newValue = False
					result = "mute (zone 2): off"
					# Look for Virtual Volume Controllers that might need updating.
					for thisId in self.volumeDeviceList:
						virtualVolumeDevice = indigo.devices[thisId]
						controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
						if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone2volume":
							# Update the Virtual Volume Controller to match current volume.
							#   Get the receiver's volume.
							theVolume = float(device.states[controlDestination])
							# Convert the current volume of the receiver to a percentage
							# to be displayed as a brightness level. If the volume is
							# less than -80.5, the receiver is off and the brightness should be 0.
							if float(theVolume) < -81:
								theVolume = -81
							theVolume = int(100-round(theVolume/-81*100, 0))
							self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', theVolume)
			else:
				newValue = False
				result = ""
				# Zone 2 mute is meaningless when using the RCA line outputs, so
				# look for Virtual Volume Controllers that might need updating.
				# If zone 2 power is on, the zone 2 line output will always be at 100% volume.
				if device.states['zone2power'] == True:
					for thisId in self.volumeDeviceList:
						virtualVolumeDevice = indigo.devices[thisId]
						controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
						if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone2volume":
							self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 100)
				else:
					# If zone 2 power is off, the zone 2 line output will always be at 0% volume.
					for thisId in self.volumeDeviceList:
						virtualVolumeDevice = indigo.devices[thisId]
						controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
						if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone2volume":
							self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
		elif response.startswith("ZV"):
			# Volume (zone 2) status.
			state = "zone2volume"
			# Convert to dB.
			newValue = int(response[2:])
			newValue = -81 + newValue
			if newValue < -80 or device.states['zone2power'] == False:
				newValue = -999
				result = "volume (zone 2): minimum."
			else:
				result = "volume (zone 2): " + str(newValue) + " dB"
			# If the speaker system arranement is not set to A + Zone 2, zone
			#   mute and volume settings returned by the receiver are meaningless.
			#   Set the state on the server to properly reflect this.
			if device.states['speakerSystem'] == "A + Zone 2":
				# Look for Virtual Volume Controllers that might need updating.
				self.debugLog("processResponse: Looking for zone 2 connected Virtual Volume Controllers. volumeDeviceList: " + str(self.volumeDeviceList))
				for thisId in self.volumeDeviceList:
					virtualVolumeDevice = indigo.devices[thisId]
					self.debugLog("processResponse: Examining Virtual Volume Controller ID " + str(thisId))
					self.debugLog("processResponse: " + str(virtualVolumeDevice))
					controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
					if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone2volume":
						self.debugLog("processResponse: Virtual Volume Controller ID " + str(thisId) + " is connected to zone 2 volume.")
						# Update the Virtual Volume Controller to match current volume.
						#   Get the receiver's volume.
						theVolume = newValue
						# Convert the current volume of the receiver to a percentage
						# to be displayed as a brightness level. If the volume is
						# less than -81, the receiver is off and the brightness should be 0.
						if theVolume < -81:
							theVolume = -81
						theVolume = 100 - int(round(theVolume / -81.0 * 100, 0))
						# If zone 2 power is on, use theVolume. If not, use zero.
						if device.states['zone2power'] == True:
							self.debugLog("processResponse: updating Virtual Volume Device ID " + str(thisId) + " brightness level to " + str(theVolume))
							self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', theVolume)
						else:
							self.debugLog("processResponse: updating Virtual Volume Device ID " + str(thisId) + " brightness level to 0")
							self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
			else:
				newValue = 0
				result = ""
				# Zone 2 volume is meaningless when using the RCA line outputs, so
				# look for Virtual Volume Controllers that might need updating.
				# If zone 2 power is on, the zone 2 line output will always be at 100% volume.
				if device.states['zone2power'] == True:
					for thisId in self.volumeDeviceList:
						virtualVolumeDevice = indigo.devices[thisId]
						controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
						if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone2volume":
							self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 100)
				else:
					# If zone 2 power is off, the zone 2 line output will always be at 0% volume.
					for thisId in self.volumeDeviceList:
						virtualVolumeDevice = indigo.devices[thisId]
						controlDestination = virtualVolumeDevice.pluginProps.get('controlDestination', "")
						if int(virtualVolumeDevice.pluginProps.get('receiverDeviceId', "")) == device.id and controlDestination == "zone2volume":
							self.updateDeviceState(virtualVolumeDevice, 'brightnessLevel', 0)
		#
		# System-Wide Items
		#
		elif response.startswith("RGB"):
			# Source name update.
			newValue = response[6:]
			# Define the device property to update and make the change to the local copy.
			propName = 'source' + response[3:5] + 'label'
			devProps[propName] = newValue
			# Update the source name in the device properties on the server.
			self.updateDeviceProps(device, devProps)
			# If the input source name update is for the currently selected
			#   zone 1 input source or zone 2 input source, change the
			#   appropriate state in the device.
			if device.states['zone1source'] == int(response[3:5]):
				state = "zone1sourceName"
				result = "input source (zone 1): " + newValue
				self.updateDeviceState(device, state, newValue)
			if device.states['zone2source'] == int(response[3:5]):
				state = "zone2sourceName"
				result = "input source (zone 2): " + newValue
				self.updateDeviceState(device, state, newValue)
		elif response.startswith("FL"):
			# Display update.
			state = "display"
			newValue = u""
			# All characters after character 4 are ASCII representations
			#   of HEX numbers that represent ASCII characters (!?)
			theString = response[4:]
			index = 0
			while index < 28:
				# Convert the 2-character HEX reprentations to actual ASCII values.
				#   -- Add "0x" to the front of the 2-character representation
				#      to indicate that it should be a HEX number.
				#   -- Use the "int" builtin to convert from ASCII base 16
				#      to an integer.
				asciiVal = int("0x" + theString[index:index+2], 16)
				# Check for special characters.
				if asciiVal < 32 or asciiVal > 126:
					# Add the special character to the newValue string from the
					#   character map dictionary defined at the top.
					newValue += characterMap[asciiVal]
				else:
					# Use the "chr" builtin to convert from integer to an ASCII
					#   character then add that to the existing newValue string.
					newValue += unicode(str(chr(asciiVal)))
				# Increment the index by 2
				index += 2
		elif response.startswith("MC"):
			# MCACC Memory update.
			state = "mcaccMemory"
			newValue = int(response[2:])
			propName = 'mcaccMemory' + str(newValue) + 'label'
			mcaccName = devProps.get(propName, "")
			result = "MCACC memory: " + str(newValue) + ": " + mcaccName
		elif response.startswith("IS"):
			# Phase Control update.
			state = "phaseControl"
			if response == "IS0":
				# Phase Control Off.
				newValue = "off"
			elif response == "IS1":
				# Phase Control On.
				newValue = "on"
			elif response == "IS2":
				# Full Band Phase Control On.
				newValue = "on - full band"
			result = "Phase Control: " + newValue
		elif response.startswith("VSP"):
			# Virtual Speakers.
			state = "vsp"
			if response == "VSP0":
				# Virtual Speakers Auto.
				newValue = "auto"
				result = "Virtual Speakers: auto"
			elif response == "VSP1":
				# Virtual Speakers Manual.
				newValue = "manual"
				result = "Virtual Speakers: manual"
		elif response.startswith("VSB"):
			# Virtual Surround Back update.
			state = "vsb"
			if response == "VSB0":
				# Virtual Surround Back Off.
				newValue = False
				result = "Virtual Surround Back: off"
			elif response == "VSB1":
				# Virtual Surround Back On.
				newValue = True
				result = "Virtual Surround Back: on"
		elif response.startswith("VHT"):
			# Virtual Surround Height update.
			state = "vht"
			if response == "VHT0":
				# Virtual Surround Height Off.
				newValue = False
				result = "Virtual Surround Height: off"
			elif response == "VSB1":
				# Virtual Surround Height On.
				newValue = True
				result = "Virtual Surround Height: on"
		elif response.startswith("CLV"):
			# Channel Volume Level update.
			channel = response[3:6]
			# Get the state name from the global dictionary defined at the top.
			state = channelVolumes[channel]
			level = float(response[6:]) * 1.0
			# Conver the level to decibels.
			newValue = -12 + 0.5 * (level - 26.0)
			result = "" + channel.strip("_") + " channel level: " + str(newValue) + " dB"
		elif response.startswith("SPK"):
			# Speaker mode update.
			state = "speakers"
			if response == "SPK0":
				# Speakers off.
				newValue = "off"
			elif response == "SPK1":
				# Speaker group A on.
				newValue = "on - A"
			elif response == "SPK2":
				# Speaker group B on.
				newValue = "on - B"
			elif response == "SPK3":
				# Both speaker groups A and B on.
				newValue = "on - A+B"
			result = "speaker mode: " + newValue
		elif response.startswith("HA"):
			# HDMI Audio Pass-through update.
			state = "hdmiAudio"
			if response == "HA0":
				# HDMI Audio processed by amp.
				newValue = False
				result = "HDMI Audio Pass-Through: off"
			elif response == "HA1":
				# HDMI Audio passed through unaltered.
				newValue = True
				result = "HDMI Audio Pass-Through: on"
		elif response.startswith("PQ"):
			# PQLS status update.
			state = "pqls"
			if response == "PQ0":
				# PQLS off.
				newValue = False
				result = "PQLS: off"
			elif response == "PQ1":
				# PQLS auto.
				newValue = True
				result = "PQLS: on"
		elif response.startswith("SSA"):
			# Operating Mode.
			state = "operatingMode"
			if response == "SSA0":
				# Expert Mode.
				newValue = "Expert"
			elif response == "SSA1":
				# reserved mode.
				newValue = "(factory reserved)"
			elif response == "SSA2":
				# Basic Mode.
				newValue = "Basic"
			result = "operating mode: " + newValue
		elif response.startswith("SSE"):
			# OSD Language setting.
			if response == "SSE00":
				newValue = "English"
			else:
				newValue = "non-English"
			# Define the device property to update and make the change to the local copy.
			propName = 'osdLanguage'
			devProps[propName] = newValue
			# Update the source name in the device properties on the server.
			self.updateDeviceProps(device, devProps)
		elif response.startswith("SSF"):
			# Speaker System status.
			state = "speakerSystem"
			if response == "SSF00":
				newValue = "A + Surround Height"
			if response == "SSF01":
				newValue = "A + Surround Width"
			if response == "SSF02":
				newValue = "A Bi-Amped"
			if response == "SSF03":
				newValue = "A + B 2-Channel"
			if response == "SSF04":
				newValue = "A + Zone 2"
			result = "speaker system layout: " + newValue
		elif response.startswith("SAA"):
			# Dimmer Brightness change.
			if response == "SAA0":
				newValue = "bright"
			elif response == "SAA1":
				newValue = "medium"
			elif response == "SAA2":
				newValue = "dim"
			elif response == "SAA3":
				newValue = "off"
		elif response.startswith("SAB"):
			# Sleep Timer time remaining.
			state = "sleepTime"
			newValue = int(response[3:])
			if newValue == 0:
				# Sleep timer is off
				self.updateDeviceState(device, "sleepMode", False)
				result = "sleep timer: off"
			else:
				# Sleep timer is on
				self.updateDeviceState(device, "sleepMode", True)
				result = "sleep timer: " + str(newValue) + " minutes remaining"
		elif response.startswith("PKL"):
			# Panel Key Lock status.
			state = "panelKeyLockMode"
			if response == "PKL0":
				# Unlocked.
				newValue = "off"
			elif response == "PKL1":
				# Panel locked.
				newValue = "on - panel"
			elif response == "PKL2":
				# Panel and volume locked.
				newValue = "on - panel+volume"
			result = "front panel lock: " + newValue
		elif response.startswith("RML"):
			# Remote Lock Mode status.
			state = "remoteLock"
			if response == "RML0":
				newValue = False
				result = "remote control lock: off"
			elif response == "RML1":
				newValue = True
				result = "remote control lock: on"
		elif response.startswith("FR"):
			# Tuner Frequency update.
			# Only update the state if either zone 1 or 2 is actually using the Tuner.
			if device.states['zone1source'] == 2 or device.states['zone2source'] == 2:
				state = "tunerFrequency"
				# Extract the band (AM or FM)
				band = response[2:3] + "M"
				# Set the tuner band on the server.
				self.updateDeviceState(device, "tunerBand", str(band))
				# Extract the frequency.
				frequency = response[3:]
				frequencyText = frequency
				if band == "FM":
					# If the band is FM, put the decimal in the right place.
					frequencyText = frequency[0:3] + "." + frequency[3:] + " MHz"
					frequencyText = frequencyText.lstrip("0")	# Eliminate leading zeros.
					frequency = float(frequency[0:3] + "." + frequency[3:])
				elif band == "AM":
					# If the band is AM, convert the text to an integer.
					frequency = int(frequency)		# Eliminates leading zeros.
					frequencyText = str(frequency) + " kHz"
				# Only log the change if the frequency is actually different.
				if frequency != device.states['tunerFrequency'] or band != device.states['tunerBand']:
					result = "tuner frequency: " + frequencyText + " " + band
				# Set the tuner frequency on the server
				newValue = frequency
		elif response.startswith("PR"):
			# Tuner Preset update.
			# Only update the state if either zone 1 or 2 is actually using the Tuner.
			if device.states['zone1source'] == 2 or device.states['zone2source'] == 2:
				state = "tunerPreset"
				# Get the preset letter plus the non-leading-zero number.
				newValue = response[2:3] + str(int(response[3:]))
				# Now add the custom name (if set) for the preset.
				propName = 'tunerPreset' + newValue + 'label'
				newValue += ": " + device.pluginProps[propName]
				# Ignore this information if the state is already set to this setting.
				if device.states[state] == newValue:
					state = ""
					newValue = ""
				else:
					result = "tuner preset: " + newValue
		elif response.startswith("TQ"):
			# Tuner Preset Label update.
			newValue = response[4:]			# Strip off the "TQ"
			newValue = newValue.strip('"')	# Remove the enclosing quotes.
			newValue = newValue.strip()		# Remove the white space.
			# Define the device property to update and make the change to the local copy.
			propName = 'tunerPreset' + response[2:4] + 'label'
			devProps[propName] = newValue
			# Update the source name in the device properties on the server.
			self.updateDeviceProps(device, devProps)
		elif response.startswith("SR"):
			# Listening Mode update.
			state = "listeningMode"
			newValue = listeningModes[response[2:]]
			# Ignore this information if the state is already set to this setting.
			if device.states[state] == newValue:
				state = ""
				newValue = ""
			else:
				result = "listening mode: " + newValue
		elif response.startswith("LM"):
			# Playback Listening Mode update.
			state = "displayListeningMode"
			newValue = displayListeningModes[response[2:]]
			# Ignore this information if the state is already set to this setting.
			if device.states[state] == newValue:
				state = ""
				newValue = ""
			else:
				result = "displayed listening mode: " + newValue
		elif response.startswith("TO"):
			# Tone Control on/off change.
			state = "toneControl"
			if response == "TO0":
				newValue = False
				result = "tone control: off"
			elif response == "TO1":
				newValue = True
				result = "tone control: on"
		elif response.startswith("BA"):
			# Bass Tone Control change.
			state = "toneBass"
			newValue = (6 - int(response[2:]))
			result = "bass tone level: " + str(newValue) + " dB"
		elif response.startswith("TR"):
			# Treble Tone Control change.
			state = "toneTreble"
			newValue = (6 - int(response[2:]))
			result = "bass tone level: " + str(newValue) + " dB"
		elif response.startswith("ATA"):
			# Sound Retriever status change.
			state = "soundRetriever"
			if response == "ATA0":
				newValue = False
				result = "Sound Retriever: off"
			elif response == "ATA1":
				newValue = True
				result = "Sound Retriever: on"
		elif response.startswith("SDA"):
			# Signal Source selection.
			state = "signalSource"
			if response == "SDA0":
				newValue = "AUTO"
			elif response == "SDA1":
				newValue = "ANALOG"
			elif response == "SDA2":
				newValue = "DIGITAL"
			elif response == "SDA3":
				newValue = "HDMI"
			result = "audio signal source: " + newValue
		elif response.startswith("SDB"):
			# Analog Input Attenuator status.
			state = "analogInputAttenuator"
			if response == "SDB0":
				newValue = False
				result = "analog input attenuator: off"
			elif response == "SDB1":
				newValue = True
				result = "analog input attenuator: on"
		elif response.startswith("ATC"):
			# Equalizer status.
			state = "equalizer"
			if response == "ATC0":
				newValue = False
				result = "equalizer: off"
			elif response == "ATC1":
				newValue = True
				result = "equalizer: on"
			# Don't update the state if it's the same.
			if device.states[state] == newValue:
				state = ""
				newValue = ""
				result = ""
		elif response.startswith("ATD"):
			# Standing Wave compensation status.
			state = "standingWave"
			if response == "ATD0":
				newValue = False
				result = "standing wave compensation: off"
			elif response == "ATD1":
				newValue = True
				result = "standing wave compensation: on"
			# Don't update the state if it's the same.
			if device.states[state] == newValue:
				state = ""
				newValue = ""
				result = ""
		elif response.startswith("ATE"):
			# Phase Control Plus delay time (ms) change.
			state = "phaseControlPlusTime"
			newValue = int(response[3:])
			result = "Phase Control Plus time: " + str(newValue) + " ms"
		elif response.startswith("ATF"):
			# Sound Delay time (fractional sample frames) change.
			state = "soundDelay"
			newValue = (float(response[3:]) / 10.0)
			result = "sound delay: " + str(newValue) + " sample frames"
		elif response.startswith("ATG"):
			# Digital Noise Reduction status.
			state = "digitalNR"
			if response == "ATG0":
				newValue = False
				result = "Digital Noise Reduction: off"
			elif response == "ATG1":
				newValue = True
				result = "Digital Noise Reduction: on"
		elif response.startswith("ATH"):
			# Dialog Enhancement change.
			state = "dialogEnhancement"
			if response == "ATH0":
				newValue = "off"
			elif response == "ATH1":
				newValue = "flat"
			elif response == "ATH2":
				newValue = "up1"
			elif response == "ATH3":
				newValue = "up2"
			elif response == "ATH4":
				newValue = "up3"
			elif response == "AHT5":
				newValue = "up4"
			result = "Dialog Enhancement mode: " + newValue
		elif response.startswith("ATI"):
			# Hi-bit 24 status.
			state = "hiBit24"
			if response == "ATI0":
				newValue = False
				result = "Hi-bit 24: off"
			elif response == "ATI1":
				newValue = True
				result = "Hi-bit 24: on"
		elif response.startswith("ATJ"):
			# Dual Mono processing chnage.
			state = "dualMono"
			if response == "ATJ0":
				newValue = False
				result = "Dual Mono sound processing: off"
			elif response == "ATJ1":
				newValue = True
				result = "Dual Mono sound processing: on"
		elif response.startswith("ATK"):
			# Fixed PCM rate processing change.
			state = "fixedPCM"
			if response == "ATK0":
				newValue = False
				result = "fixed rate PCM: off"
			elif response == "ATK1":
				newValue = True
				result = "fixed rate PCM: on"
		elif response.startswith("ATL"):
			# Dynamic Range Compression mode change.
			state = "dynamicRangeCompression"
			if response == "ATL0":
				newValue = "off"
			elif response == "ATL1":
				newValue = "auto"
			elif response == "ATL2":
				newValue = "mid"
			elif response == "ATL3":
				newValue = "max"
			result = "Dynamic Range Compression: " + newValue
		elif response.startswith("ATM"):
			# LFE Attenuation change.
			state = "lfeAttenuatorAmount"
			newValue = (-5 * int(response[3:]))
			result = "LFE attenuation amount: " + str(newValue) + " dB"
			if newValue < -20:
				# A response of ATM5 translates to the attenuator being turned off.
				self.updateDeviceState(device, "lfeAttenuator", False)
				result = "LFE attenuation: off"
			else:
				self.updateDeviceState(device, "lfeAttenuator", True)
		elif response.startswith("ATN"):
			# SACD Gain change.
			state = "sacdGain"
			if response == "ATN0":
				newValue = 0
			elif response == "ATN1":
				newValue = 6
			result = "SACD gain: " + str(newValue) + " dB"
		elif response.startswith("ATO"):
			# Auto Sound Delay status update.
			state = "autoDelay"
			if response == "ATO0":
				newValue = False
				result = "Auto Sound Delay: off"
			elif response == "ATO1":
				newValue = True
				result = "Auto Sound Delay: on"
		elif response.startswith("ATP"):
			# Dolby Pro Logic II Music Center Width change.
			state = "pl2musicCenterWidth"
			newValue = int(response[3:])
			result = "Dolby Pro Logic II Music center width: " + str(newValue)
		elif response.startswith("ATQ"):
			# Dolby Pro Logic II Music Panorama status.
			state = "pl2musicPanorama"
			if response == "ATQ0":
				newValue = False
				result = "Dolby Pro Logic II Music panorama: off"
			elif response == "ATQ1":
				newValue = True
				result = "Dolby Pro Logic II Music panorama: on"
		elif response.startswith("ATR"):
			# Dolby Pro Logic II Music Dimension level change.
			state = "pl2musicDimension"
			newValue = (int(response[3:]) - 50)
			result = "Dolby Pro Logic II Music dimension: " + str(newValue)
		elif response.startswith("ATS"):
			# Neo:6 Center Image change.
			state = "neo6centerImage"
			newValue = (float(response[3:]) / 10.0)
			result = "Neo:6 center image: " + str(newValue)
		elif response.startswith("ATT"):
			# Effect amount change.
			state = "effectAmount"
			newValue = (int(response[3:]) * 10)
			result = "effect level: " + str(newValue)
		elif response.startswith("ATU"):
			# Dolby Pro Logic IIz Height Gain change.
			state = "pl2zHeightGain"
			if response == "ATU0":
				newValue = "LOW"
			elif response == "ATU1":
				newValue = "MID"
			elif response == "ATU2":
				newValue = "HIGH"
			result = "Dolby Pro Logic IIz height gain: " + newValue
		elif response.startswith("VTB"):
			# Video Converter update.
			state = "videoConverter"
			if response == "VTB0":
				# Video Converter Off.
				newValue = False
				result = "video converter: off"
			elif response == "VTB1":
				# Video Converter On.
				newValue = True
				result = "video converter: on"
		elif response.startswith("VTC"):
			# Video Resolution update.
			state = "videoResolution"
			newValue = videoResolutionPrefs[response[3:]]
			result = "preferred video resolution: " + newValue
		elif response.startswith("VTD"):
			# Video Pure Cinema mode update.
			state = "videoPureCinema"
			if response == "VTD0":
				# Pure Cinema Auto.
				newValue = "auto"
			elif response == "VTD1":
				# Pure Cinema On.
				newValue = "on"
			elif response == "VTD2":
				# Pure Cinema Off.
				newValue = "off"
			result = "Pure Cinema mode: " + newValue
		elif response.startswith("VTE"):
			# Video Progressive Motion Quality update.
			state = "videoProgressiveQuality"
			newValue = -4 + (int(response[3:]) - 46)
			result = "video progressive scan motion quality: " + str(newValue)
		elif response.startswith("VTG"):
			# Video Advanced Adjustment update.
			state = "videoAdvancedAdjust"
			if response == "VTG0":
				# PDP (Plasma Display Panel)
				newValue = "PDP (Plasma)"
			elif response == "VTG1":
				# LCD (Liquid Crystal Display)
				newValue = "LCD"
			elif response == "VTG2":
				# FPJ (Front Projection)
				newValue = "FPJ (Front Projection)"
			elif response == "VTG3":
				# Professional
				newValue = "Professional"
			elif response == "VTG4":
				# Memory
				newValue = "Memory"
			result = "Advanced Video Adjustment: " + newValue
		elif response.startswith("VTH"):
			# Video YNR (Luminance Noise Reduction) update.
			state = "videoYNR"
			newValue = int(response[3:]) - 50
			result = "video YNR: " + str(newValue)
		elif response.startswith("VTL"):
			# Video Detail Adjustment update.
			state = "videoDetail"
			newValue = 50 - int(response[3:])
			result = "video detail amount: " + str(newValue)
		elif response.startswith("AST"):
			# Audio Status information update.
			#   Multiple data are provided in this response (43 bytes, or 55 for VSX-1123-K).
			state = ""
			newValue = ""
			data = response[3:]				# strip the AST text.
			
			# == Data Common to All Models ==
			audioInputFormat = data[0:2]	# 2-byte signal format code.
			# Convert signal format code to a named format.
			audioInputFormat = audioInputFormats[audioInputFormat]
			state = "audioInputFormat"
			newValue = audioInputFormat
			self.updateDeviceState(device, state, newValue)
			
			audioInputFrequency = data[2:4]	# 2-byte sample frequency code.
			# Convert sample frequency code to a value.
			audioInputFrequency = audioInputFrequencies[audioInputFrequency]
			state = "audioInputFrequency"
			newValue = audioInputFrequency
			self.updateDeviceState(device, state, newValue)
			
			state = "inputChannels"
			newValue = ""
			# Convert data bytes 5-25 into an input channel format string.
			# Loop through data bytes and add channels that are enabled.
			state = "inputChannels"
			newValue = ""
			for i in range(5, 26):
				if data[(i - 1):i] == "1":
					# Add a comma if this is not the first item.
					if newValue is not "":
						newValue += ", "
					newValue += audioChannels[(i - 5)]
			self.updateDeviceState(device, state, newValue)
			
			# Convert data bytes 26-43 into an output channel format string.
			# Loop through data bytes and add channels that are enabled.
			state = "outputChannels"
			newValue = ""
			for i in range(26, 44):
				if data[(i - 1):i] == "1":
					# Add a comma if this is not the first item.
					if newValue is not "":
						newValue += ", "
					newValue += audioChannels[(i - 26)]
			self.updateDeviceState(device, state, newValue)
			
			# The VSX-1123-K responds with a 55 instead of 43 characters.
			#   These extra data represent features found only in this and other 2014 models.
			if device.deviceTypeId == "vsx1123k":
				audioOutputFrequency = data[43:45]	# 2-byte sample frequency code.
				# Convert sample frequency code to a value.
				audioOutputFrequency = audioOutputFrequencies[audioOutputFrequency]
				state = "audioOutputFrequency"
				newValue = audioOutputFrequency
				self.updateDeviceState(device, state, newValue)
				
				audioOutputBitDepth = data[45:47]	# 2-byte sample bit depth value.
				# Convert sample bit depth from a string to a number.
				audioOutputBitDepth = int(audioOutputBitDepth)
				state = "audioOutputBitDepth"
				newValue = audioOutputBitDepth
				self.updateDeviceState(device, state, newValue)
				
				# Bytes 48 through 51 are reserved.
				
				pqlsMode = data[51:52]	# 1-byte PQLS working mode code.
				# Convert PQLS code to working state.
				if pqlsMode == "0":
					pqlsMode = "off"
				elif pqlsMode == "1":
					pqlsMode = "2-channel"
				elif pqlsMode == "2":
					pqlsMode = "multi-channel"
				elif pqlsMode == "3":
					pqlsMode = "bitstream"
				state = "pqlsMode"
				newValue = pqlsMode
				self.updateDeviceState(device, state, newValue)
				
				phaseControlPlusWorkingDelay = data[52:54]	# 2-byte Phase Control Plus working delay (ms).
				# Convert Phase Control Plus string to number.
				phaseControlPlusWorkingDelay = int(phaseControlPlusWorkingDelay)
				state = "phaseControlPlusWorkingDelay"
				newValue = phaseControlPlusWorkingDelay
				self.updateDeviceState(device, state, newValue)
				
				phaseControlPlusReversed = data[54:55]	# 1-byte Phase Control Plus reversed phase.
				# Translate Phase Control Plus reversed state.
				if phaseControlPlusReversed == "0":
					phaseControlPlusReversed = True
				elif phaseControlPlusReversed == "1":
					phaseControlPlusReversed = False
				state = "phaseControlPlusReversed"
				newValue = phaseControlPlusReversed
				self.updateDeviceState(device, state, newValue)
				
			result = "audio input/output information updated"
			
		elif response.startswith("VST"):
			# Video Status information update.
			#   Multiple data are provided in this response.
			state = ""
			newValue = ""
			data = response[3:]	# Strip off the leading "VST".
			
			# Video Input Terminal
			state = "videoInputTerminal"
			newValue = int(data[0:1])
			if newValue == 0:
				newValue = ""
			elif newValue == 1:
				newValue = "Video"
			elif newValue == 2:
				newValue = "S-Video"
			elif newValue == 3:
				newValue = "Component"
			elif newValue == 4:
				newValue = "HDMI"
			elif newValue == 5:
				newValue = "Self (OSD/JPEG)"
			self.updateDeviceState(device, state, newValue)
			
			# Video Input Resolution
			state = "videoInputResolution"
			newValue = videoResolutions[data[1:3]]
			self.updateDeviceState(device, state, newValue)
			
			# Video Input Aspect Ratio
			state = "videoInputAspect"
			newValue = int(data[3:4])
			if newValue == 0:
				newValue = ""
			elif newValue == 1:
				newValue = "4:3"
			elif newValue == 2:
				newValue = "16:9"
			elif newValue == 3:
				newValue = "14:9"
			self.updateDeviceState(device, state, newValue)
			
			# Video Input Color Format
			state = "videoInputColorFormat"
			newValue = int(data[4:5])
			if newValue == 0:
				newValue = ""
			elif newValue == 1:
				newValue = "RGB Limited"
			elif newValue == 2:
				newValue = "RGB Full"
			elif newValue == 3:
				newValue = "YCbCr 4:4:4"
			elif newValue == 4:
				newValue = "YCbCr 4:2:2"
			self.updateDeviceState(device, state, newValue)
			
			# Video Input Bit Depth
			state = "videoInputBitDepth"
			newValue = int(data[5:6])
			if newValue == 0:
				newValue = ""
			elif newValue == 1:
				newValue = "24-bit (8-bit per pixel)"
			elif newValue == 2:
				newValue = "30-bit (10-bit per pixel)"
			elif newValue == 3:
				newValue = "36-bit (12-bit per pixel)"
			elif newValue == 4:
				newValue = "48-bit (16-bit per pixel)"
			self.updateDeviceState(device, state, newValue)
			
			# Video Input Color Space
			state = "videoInputColorSpace"
			newValue = int(data[6:7])
			if newValue == 0:
				newValue = ""
			elif newValue == 1:
				newValue = "Standard"
			elif newValue == 2:
				newValue = "xv.Color YCC 601"
			elif newValue == 3:
				newValue = "xv.Color YCC 709"
			elif newValue == 4:
				newValue = "sYCC"
			elif newValue == 5:
				newValue = "Adobe YCC 601"
			elif newValue == 6:
				newValue = "Adobe RGB"
			self.updateDeviceState(device, state, newValue)
			
			# Video Output Resolution
			state = "videoOutputResolution"
			newValue = videoResolutions[data[7:9]]
			self.updateDeviceState(device, state, newValue)
			
			# Video Output Aspect Ratio
			state = "videoOutputAspect"
			newValue = int(data[9:10])
			if newValue == 0:
				newValue = ""
			elif newValue == 1:
				newValue = "4:3"
			elif newValue == 2:
				newValue = "16:9"
			elif newValue == 3:
				newValue = "14:9"
			self.updateDeviceState(device, state, newValue)
			
			# Video Output Color Format
			state = "videoOutputColorFormat"
			newValue = int(data[10:11])
			if newValue == 0:
				newValue = ""
			elif newValue == 1:
				newValue = "RGB Limited"
			elif newValue == 2:
				newValue = "RGB Full"
			elif newValue == 3:
				newValue = "YCbCr 4:4:4"
			elif newValue == 4:
				newValue = "YCbCr 4:2:2"
			self.updateDeviceState(device, state, newValue)
			
			# Video Output Bit Depth
			state = "videoOutputBitDepth"
			newValue = int(data[11:12])
			if newValue == 0:
				newValue = ""
			elif newValue == 1:
				newValue = "24-bit (8-bit per pixel)"
			elif newValue == 2:
				newValue = "30-bit (10-bit per pixel)"
			elif newValue == 3:
				newValue = "36-bit (12-bit per pixel)"
			elif newValue == 4:
				newValue = "48-bit (16-bit per pixel)"
			self.updateDeviceState(device, state, newValue)
			
			# Video Output Color Space
			state = "videoOutputColorSpace"
			newValue = int(data[12:13])
			if newValue == 0:
				newValue = ""
			elif newValue == 1:
				newValue = "Standard"
			elif newValue == 2:
				newValue = "xv.Color YCC 601"
			elif newValue == 3:
				newValue = "xv.Color YCC 709"
			elif newValue == 4:
				newValue = "sYCC"
			elif newValue == 5:
				newValue = "Adobe YCC 601"
			elif newValue == 6:
				newValue = "Adobe RGB"
			self.updateDeviceState(device, state, newValue)
			
			# Monitor Recommended Resolution (HDMI 1)
			state = "monitorRecommendedResolution"
			newValue = videoResolutions[data[13:15]]
			self.updateDeviceState(device, state, newValue)
			
			# Monitor Bit Depth Support
			state = "monitorBitDepth"
			newValue = int(data[15:16])
			if newValue == 0:
				newValue = ""
			elif newValue == 1:
				newValue = "24-bit (8-bit per pixel)"
			elif newValue == 2:
				newValue = "30-bit (10-bit per pixel)"
			elif newValue == 3:
				newValue = "36-bit (12-bit per pixel)"
			elif newValue == 4:
				newValue = "48-bit (16-bit per pixel)"
			self.updateDeviceState(device, state, newValue)
			
			# Monitor Supported Color Spaces (HDMI 1)
			state = "monitorColorSpaces"
			newValue = ""
			colorSpaces = data[16:21]
			if colorSpaces[0:1] == "1":
				newValue += "xv.Color YCC 601"
			if colorSpaces[1:2] == "1":
				if len(newValue) > 0:
					newValue += ", "
				newValue += "xv.Color YCC 709"
			if colorSpaces[2:3] == "1":
				if len(newValue) > 0:
					newValue += ", "
				newValue += "xYCC"
			if colorSpaces[3:4] == "1":
				if len(newValue) > 0:
					newValue += ", "
				newValue += "Adobe YCC 601"
			if colorSpaces[4:5] == "1":
				if len(newValue) > 0:
					newValue += ", "
				newValue += "Adobe RGB"
			self.updateDeviceState(device, state, newValue)
			
			result = "video input/output information updated"
			
		else:
			# Unrecognized response received.
			self.debugLog("Unrecognized response received from " + device.name + ": " + response)
		
		getStatusUpdate = False		# Should we perform a full status update?
		
		# Only update the device if the state is not blank.
		if state != "":
			# If this is a zone power state change to True and the current
			#   zone power state is False, get more status information.
			if (state == "zone1power" and newValue == True and device.states['zone1power'] == False) or (state == "zone2power" and newValue == True and device.states['zone2power'] == False):
				getStatusUpdate = True
			
			# Update the state on the server.
			self.updateDeviceState(device, state, newValue)
		
		#
		# CHECK IF ADDITIONAL PROCESSING IS NEEDED
		#
		
		# If this is a zone source input change, request additional information.
		if state == "zone1source":
			# Get the specified input source name (just in case the user changed
			#   the input name since the last full status update).
			self.sendCommand(device, "?RGB" + response[2:])
			# Audio Status.
			self.getAudioInOutStatus(device)
			# If this is an input change to the Tuner, get the station preset info.
			if response == "FN02":
				self.getTunerPresetStatus(device)
			else:
				# Since zone 1 is not using the Tuner, as long as zone 2 isn't either,
				#   let's clear the Tuner statuses in the device.
				if device.states['zone2source'] != 2:
					self.debugLog("processResponse: Neither zone is using the tuner. Clearing frequency info.")
					self.updateDeviceState(device, 'tunerFrequency', 0)
					self.updateDeviceState(device, 'tunerFrequencyText', "")
					self.updateDeviceState(device, 'tunerPreset', "")
					self.updateDeviceState(device, 'tunerBand', "")
			
		elif state == "zone2source":
			# Get the specified input source name (just in case the user changed
			#   the input name since the last full status update).
			self.sendCommand(device, "?RGB" + response[3:])
			# Audio Status.
			self.getAudioInOutStatus(device)
			# If this is an input change to the Tuner, get the band, frequency, and preset info.
			if response == "Z2F02":
				self.getTunerPresetStatus(device)
			else:
				# Since zone 2 is not using the Tuner, as long as zone 1 isn't either,
				#   let's clear the Tuner statuses in the device.
				if device.states['zone1source'] != 2:
					self.debugLog("processResponse: Neither zone is using the tuner. Clearing frequency info.")
					self.updateDeviceState(device, 'tunerFrequency', 0)
					self.updateDeviceState(device, 'tunerFrequencyText', "")
					self.updateDeviceState(device, 'tunerPreset', "")
					self.updateDeviceState(device, 'tunerBand', "")
			
		elif state == "tunerPreset":
			# Tuner preset was changed. Get the new frequency.
			self.getTunerFrequency(device)
			
		elif state == "mcaccMemory":
			# MCACC Memory change. Set the mcaccMemory#label value.
			self.updateDeviceState(device, 'mcaccMemoryName', mcaccName)
			
		elif state == "tunerFrequency":
			# Also set the tunerFrequencyText.
			self.updateDeviceState(device, 'tunerFrequencyText', frequencyText)
		
		# If both zones are off, clear some states that should have no value when the unit is off.
		if device.states['zone1power'] == False and device.states['zone2power'] == False:
			self.updateDeviceState(device, "audioInputFormat", "")
			self.updateDeviceState(device, "audioInputFrequency", 0)
			self.updateDeviceState(device, "inputChannels", "")
			self.updateDeviceState(device, "outputChannels", "")
			self.updateDeviceState(device, "monitorBitDepth", "")
			self.updateDeviceState(device, "monitorColorSpaces", "")
			self.updateDeviceState(device, "monitorRecommendedResolution", "")
			self.updateDeviceState(device, "signalSource", "")
			self.updateDeviceState(device, "sleepMode", False)
			self.updateDeviceState(device, "sleepTime", 0)
			self.updateDeviceState(device, "tunerBand", "")
			self.updateDeviceState(device, "tunerFrequency", 0)
			self.updateDeviceState(device, "tunerFrequencyText", "")
			self.updateDeviceState(device, "tunerPreset", "")
			self.updateDeviceState(device, "videoInputAspect", "")
			self.updateDeviceState(device, "videoInputBitDepth", "")
			self.updateDeviceState(device, "videoInputColorFormat", "")
			self.updateDeviceState(device, "videoInputColorSpace", "")
			self.updateDeviceState(device, "videoInputResolution", "")
			self.updateDeviceState(device, "videoInputTerminal", "")
			self.updateDeviceState(device, "videoOutputAspect", "")
			self.updateDeviceState(device, "videoOutputBitDepth", "")
			self.updateDeviceState(device, "videoOutputColorFormat", "")
			self.updateDeviceState(device, "videoOutputColorSpace", "")
			self.updateDeviceState(device, "videoOutputResolution", "")
		
		# Now get the additional status info if needed.
		if getStatusUpdate:
			self.getReceiverStatus(device)
		
		return result
	
	
	#########################################
	# Information Gathering Methods
	#########################################
	#
	# Current Display Content
	#
	def getDisplayContent(self, device):
		self.debugLog("getDisplayContent: Getting " + device.name + " display content.")
		
		# Get th device type. Future versions of this plugin will support other receiver models.
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			self.sendCommand(device, "?FL")			# Display Content Query.
			self.sleep(0.1)							# Wait for responses to be processed.
	
	#
	# Power Status
	#
	def getPowerStatus(self, device):
		self.debugLog("getPowerStatus: Getting " + device.name + " power status.")
		
		# Get th device type. Future versions of this plugin will support other receiver models.
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			self.sendCommand(device, "?P")			# Power Query (Zone 1).
			self.sleep(0.1)							# Wait for responses to be processed.
			self.sendCommand(device, "?AP")			# Power Query (Zone 2).
			self.sleep(0.1)
			
			# It's important that we get the result of this status request before proceeding.
			response = self.readData(device)
			response = response.rstrip("\r\n")
			for responseLine in response.splitlines():
				result = self.processResponse(device, responseLine)
				if result != "":
					indigo.server.log(result, device.name)
					
	#
	# Input Source Names
	#
	def getInputSourceNames(self, device):
		self.debugLog("getInputSourceNames: Getting " + device.name + " input source names.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			# Get the names of all the input sources.
			for theNumber, theName in sourceNames.items():
				# Only ask for information on sources recognized by the device type.
				#   VSX-1021-K
				if devType is "vsk1021k":
					if theNumber not in vsx1021kSourceMask:
						self.sendCommand(device, "?RGB" + theNumber)
						self.sleep(0.1)		# Wait for responses to be processed.
				#   VSX-1022-K
				if devType is "vsk1022k":
					if theNumber not in vsx1022kSourceMask:
						self.sendCommand(device, "?RGB" + theNumber)
						self.sleep(0.1)		# Wait for responses to be processed.
				#   VSX-1122-K
				if devType is "vsk1122k":
					if theNumber not in vsx1122kSourceMask:
						self.sendCommand(device, "?RGB" + theNumber)
						self.sleep(0.1)		# Wait for responses to be processed.
				#   VSX-1123-K
				if devType is "vsk1123k":
					if theNumber not in vsx1123kSourceMask:
						self.sendCommand(device, "?RGB" + theNumber)
						self.sleep(0.1)		# Wait for responses to be processed.
				#   SC-75
				if devType is "sc75":
					if theNumber not in sc75SourceMask:
						self.sendCommand(device, "?RGB" + theNumber)
						self.sleep(0.1)		# Wait for responses to be processed.

	#
	# Tuner Preset Names
	#
	def getTunerPresetNames(self, device):
		self.debugLog("getTunerPresetNames: Getting " + device.name + " tuner preset station names.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			self.sendCommand(device, "?TQ")			# Tuner Preset label query.
			self.sleep(0.2)
			
	#
	# Tuner Band and Frequency
	#
	def getTunerFrequency(self, device):
		self.debugLog("getTunerFrequency: Getting " + device.name + " tuner band and frequency.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			self.sendCommand(device, "?FR")
			self.sleep(0.1)
			
	#
	# Tuner Preset Status
	#
	def getTunerPresetStatus(self, device):
		self.debugLog("getTunerPresetStatus: Getting " + device.name + " tuner preset status.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			self.sendCommand(device, "?PR")
			self.sleep(0.1)
			
	#
	# Volume Status (Zones 1 and 2)
	#
	def getVolumeStatus(self, device):
		self.debugLog("getVolumeStatus: Getting " + device.name + " volume status.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			self.sendCommand(device, "?V")			# Volume Query (Zone 1)
			self.sleep(0.1)
			self.sendCommand(device, "?ZV")			# Volume Query (Zone 2)
			self.sleep(0.1)
			
	#
	# Mute Status (Zones 1 and 2)
	#
	def getMuteStatus(self, device):
		self.debugLog("getMuteStatus: Getting " + device.name + " mute status.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			self.sendCommand(device, "?M")			# Mute Query (Zone 1)
			self.sleep(0.1)
			self.sendCommand(device, "?Z2M")		# Mute Query (Zone 2)
			self.sleep(0.1)
			
	#
	# Input Source Status (Zones 1 and 2)
	#
	def getInputSourceStatus(self, device):
		self.debugLog("getInputSourceStatus: Getting " + device.name + " input source status.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			self.sendCommand(device, "?F")			# Input Source Query (Zone 1)
			self.sleep(0.1)
			self.sendCommand(device, "?ZS")			# Input Source Query (Zone 2)
			self.sleep(0.1)
			
	#
	# Channel Volume Levels
	#
	def getChannelVolumeLevels(self, device):
		self.debugLog("getChannelVolumeLevels: Getting " + device.name + " individual channel volume levels.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			for theChannel, theState in channelVolumes.items():
				self.sendCommand(device, "?" + theChannel + "CLV")
				self.sleep(0.1)
				
	#
	# System Setup Status
	#
	def getSystemSetupStatus(self, device):
		self.debugLog("getSystemSetupStatus: Getting " + device.name + " system settings.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			self.sendCommand(device, "?SPK")		# Amp speaker setting.
			self.sleep(0.1)
			self.sendCommand(device, "?PKL")		# Panel Key Lock status.
			self.sleep(0.1)
			self.sendCommand(device, "?RML")		# Remote Lock status.
			self.sleep(0.1)
			self.sendCommand(device, "?SSA")		# Operating Mode status.
			self.sleep(0.1)
			self.sendCommand(device, "?SSE")		# OSD Language status.
			self.sleep(0.1)
			self.sendCommand(device, "?SSF")		# Speaker System status.
			self.sleep(0.1)
			self.sendCommand(device, "?SAB")		# Sleep timer time remaining.
			self.sleep(0.1)
			
	#
	# Audio DSP Settings
	#
	def getAudioDspSettings(self, device):
		self.debugLog("getAudioDspSettings: Getting " + device.name + " audio DSP settings.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			self.sendCommand(device, "?TO")			# Tone Control status.
			self.sleep(0.1)
			self.sendCommand(device, "?BA")			# Bass Tone Control level.
			self.sleep(0.1)
			self.sendCommand(device, "?TR")			# Treble Tone Control level.
			self.sleep(0.1)
			self.sendCommand(device, "?MC")			# MCACC Memory setting.
			self.sleep(0.1)
			self.sendCommand(device, "?IS")			# Phase Control setting.
			self.sleep(0.1)
			self.sendCommand(device, "?PQ")			# PQLS Auto status.
			self.sleep(0.1)
			self.sendCommand(device, "?VSB")		# Virtual Surround Back setting.
			self.sleep(0.1)
			self.sendCommand(device, "?VHT")		# Virtual Height setting.
			self.sleep(0.1)
			self.sendCommand(device, "?HA")			# HDMI Audio pass-through setting.
			self.sleep(0.1)
			self.sendCommand(device, "?L")			# Playback Listening Mode.
			self.sleep(0.1)
			self.sendCommand(device, "?S")			# Surround Listening Mode.
			self.sleep(0.1)
			self.sendCommand(device, "?SDA")		# Signal Source selection status.
			self.sleep(0.1)
			self.sendCommand(device, "?SDB")		# Analog Input Attenuator status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATA")		# Sound Retriever status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATC")		# Equalizer status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATD")		# Standing Wave compensation status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATE")		# Phase Control Plus delay (ms).
			self.sleep(0.1)
			self.sendCommand(device, "?ATF")		# Sound Delay (sample frames).
			self.sleep(0.1)
			self.sendCommand(device, "?ATG")		# Digital Noise Reduction status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATH")		# Dialog Enhancement status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATJ")		# Dual Mono processing status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATK")		# Fixed PCM processing status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATL")		# Dynamic Range Compression mode.
			self.sleep(0.1)
			self.sendCommand(device, "?ATM")		# LFE Attenuation status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATN")		# SACD Gain status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATO")		# Auto Sound Delay status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATP")		# Dolby Pro Logic II Music Center Width status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATQ")		# Dolby Pro Logic II Music Panorama status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATR")		# Dolby Pro Logic II Music Dimension status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATS")		# Neo:6 Center Image status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATT")		# Effect level status.
			self.sleep(0.1)
			self.sendCommand(device, "?ATU")		# Dolby Pro Logic IIz Height Gain status.
			self.sleep(0.1)
			
	#
	# Video DSP Settings
	#
	def getVideoDspSettings(self, device):
		self.debugLog("getVideoDspSettings: Getting " + device.name + " video DSP settings.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			self.sendCommand(device, "?VTB")		# Video Converter status.
			self.sleep(0.1)
			self.sendCommand(device, "?VTC")		# Resolution Preferences status.
			self.sleep(0.1)
			self.sendCommand(device, "?VTD")		# Pure Cinema Mode.
			self.sleep(0.1)
			self.sendCommand(device, "?VTE")		# Progressive Motion Quality.
			self.sleep(0.1)
			self.sendCommand(device, "?VTG")		# Advanced Video Adjustment mode.
			self.sleep(0.1)
			self.sendCommand(device, "?VTH")		# YNR amount.
			self.sleep(0.1)
			self.sendCommand(device, "?VTL")		# Video Detail adjustment.
			self.sleep(0.1)
			
	#
	# Audio I/O Status
	#
	def getAudioInOutStatus(self, device):
		self.debugLog("getAudioInOutStatus: Getting " + device.name + " audio I/O status.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			# Since this method is called just after an input source change, wait a bit
			#   for the system to finalize the change.
			self.sleep(1)
			self.sendCommand(device, "?AST")		# Audio Status.
			
	#
	# Video I/O Status
	#
	def getVideoInOutStatus(self, device):
		self.debugLog("getVideoInOutStatus: Getting " + device.name + " video I/O status.")
		
		devType = device.deviceTypeId
		
		# Make sure it's not a virtual volume device.
		if devType != "virtualVolume":
			# Since this method is called just after an input source change, wait half a second
			#   for the system to finalize the change.
			self.sleep(0.5)
			self.sendCommand(device, "?VST")		# Video Status.
			
	#
	# All Status Information
	#
	def getReceiverStatus(self, device):
		self.debugLog("getReceiverStatus: Getting all information for " + device.name + ".")
		self.debugLog("getReceiverStatus: List of device IDs being updated: " + str(self.devicesBeingUpdated))
		
		# Make sure we aren't already updating this device.
		if device.id not in self.devicesBeingUpdated:
			# Add it to the list of devices being updated.
			self.devicesBeingUpdated.append(device.id)
			
			# Now gather all receiver data.
			
			devType = device.deviceTypeId
			
			# Indicate in the log that we're going to be gathering all kinds of information.
			indigo.server.log("Gathering receiver system information.", device.name)
			
			# Make sure it's not a virtual volume device.
			if devType != "virtualVolume":
				# Get this information regardless of whether the receiver is on or off.
				self.getDisplayContent(device)			# Display Content Query.
				self.getPowerStatus(device)				# Power Status.
				self.getInputSourceNames(device)		# Input Source Names.
				
				# Information related to both zones...
				if device.states['zone1power'] == True or device.states['zone2power'] == True:
					self.getVolumeStatus(device)		# Volume Status.
					self.getMuteStatus(device)			# Mute Status
					self.getInputSourceStatus(device)	# Input Source Status.
					self.getAudioInOutStatus(device)	# Audio I/O Status.
					self.getVideoInOutStatus(device)	# Video I/O Status.
					self.getTunerPresetNames(device)	# Tuner Preset Names.
					self.getTunerPresetStatus(device)	# Tuner Preset Status.
					# self.getTunerFrequency(device)		# Tuner Band and Frequency.
					self.getSystemSetupStatus(device)	# System Setup Status.
				
				# Information relevant only to the main zone (1)...
				if device.states['zone1power'] == True:
					self.getAudioDspSettings(device)	# Audio DSP Settings.
					self.getVideoDspSettings(device)	# Video DSP Settings.
					self.getChannelVolumeLevels(device)	# Channel Volume Levels.
					
			self.sleep(0.5)								# Wait a bit for processing.
			
			# Now remove the device from the list of devices being updated.
			self.devicesBeingUpdated.remove(device.id)
	
	
	#########################################
	# ACTION METHODS
	#########################################
	#
	# Power On (Zone 1)
	#
	def zone1powerOn(self, action):
		# Turn on power (zone 1) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Turning on power (zone 1) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# For VSX-1021-K
		if device.deviceTypeId == "vsx1021k":
			command = "PO"	# Power On
			self.sendCommand(device, command)
			self.sleep(0.1)
		
		# For VSX-1022-K and later.
		if device.deviceTypeId == "vsx1022k" or device.deviceTypeId == "vsx1122k" or device.deviceTypeId == "vsx1123k" or device.deviceTypeId == "sc75":
			command = "PO"	# Power On
			self.sendCommand(device, command)
			self.sleep(0.1)
			# Pioneer suggests that for 2012 and later models, this command be sent twice.
			command = "PO"	# Power On
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Power Off (Zone 1)
	#
	def zone1powerOff(self, action):
		# Turn off power (zone 1) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Turning off power (zone 1) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "PF"	# Power Off
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Power Toggle (Zone 1)
	#
	def zone1powerToggle(self, action):
		# Toggle power (zone 1) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Toggling power (zone 1) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "?P"	# Query power status first to wake up 2012+ receiver CPUs.
			self.sendCommand(device, command)
			self.sleep(0.1)
			command = "PZ"	# Power Toggle
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Volume Up 0.5 dB (Zone 1)
	#
	def zone1volumeUp(self, action):
		# Increment volume (zone 1) by 0.5 dB for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Volume Up 0.5 dB (zone 1) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "VU"	# Volume Up
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Volume Down 0.5 dB (Zone 1)
	#
	def zone1volumeDown(self, action):
		# Decrement volume (zone 1) by 0.5 dB for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Volume Down 0.5 dB (zone 1) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "VD"	# Volume Down
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Set Volume in dB (Zone 1)
	#
	def zone1setVolume(self, action):
		# Set the volume (zone 1) for the device..
		device = indigo.devices[action.deviceId]
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		newValue = float(action.props.get('volume', "-90"))
		if newValue == -90.0:	# No value was provided.
			self.errorLog(u"No Zone 1 Vvolume was specified in the action for \"" + device.name + u"\"")
			return False
		
		self.debugLog("Set volume to " + str(newValue) + " dB (zone 1) for " + device.name)
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			newValue = 161 + int(newValue/0.5)
			if newValue < 10:
				newValue = "00" + str(newValue)
			elif newValue < 100:
				newValue = "0" + str(newValue)
			else:
				newValue = str(newValue)
			command = newValue + "VL"	# Set Volume.
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Mute On (Zone 1)
	#
	def zone1muteOn(self, action):
		# Turn on mute (zone 1) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Turning on mute (zone 1) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "MO"	# Mute On
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Mute Off (Zone 1)
	#
	def zone1muteOff(self, action):
		# Turn off (zone 1) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Turning off mute (zone 1) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "MF"	# Mute Off
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Mute Toggle (Zone 1)
	#
	def zone1muteToggle(self, action):
		# Toggle mute (zone 1) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Toggling mute (zone 1) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "MZ"	# Toggle Mute
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Select Next Source (Zone 1)
	#
	def zone1sourceUp(self, action):
		# Go to the next available input source.
		device = indigo.devices[action.deviceId]
		self.debugLog("Select Next Source (zone 1) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "FU"	# Source Up (Next)
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Select Previous Source (Zone 1)
	#
	def zone1sourceDown(self, action):
		# Go to the previous available input source.
		device = indigo.devices[action.deviceId]
		self.debugLog("Select Previous Source (zone 1) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "FD"	# Source Down (Previous)
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Set Input Source (Zone 1)
	#
	def zone1setSource(self, action):
		# Set the input source to something specific.
		device = indigo.devices[action.deviceId]
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		newValue = action.props.get('source', False)
		self.debugLog("zone1setSource called: source: " + str(newValue) + ", device: " + device.name)
		
		if not newValue:
			self.errorLog(u"No source selected for \"" + device.name + "\"")
			return False
		self.debugLog("(Source name: " + sourceNames[str(newValue)])
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = newValue + "FN"	# Set Source.
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Power On (Zone 2)
	#
	def zone2powerOn(self, action):
		# Turn on power (zone 2) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("zone2powerOn: Turning on power (zone 2) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "APO"	# Power On
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Power Off (Zone 2)
	#
	def zone2powerOff(self, action):
		# Turn off power (zone 2) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("zone2powerOff: Turning off power (zone 2) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "APF"	# Power Off
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Power Toggle (Zone 2)
	#
	def zone2powerToggle(self, action):
		# Toggle power (zone 2) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("zone2powerToggle: Toggling power (zone 2) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "APZ"	# Power Toggle
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Volume Up 1 dB (Zone 2)
	#
	def zone2volumeUp(self, action):
		# Increment volume (zone 2) by 1 dB for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Volume Up 1 dB (zone 2) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			# If the current speaker system setup is not "A + Zone 2",
			#   zone mute and volume commands will be ignored.
			if device.states['speakerSystem'] == "A + Zone 2":
				command = "ZU"	# Volume Up
				self.sendCommand(device, command)
				self.sleep(0.1)
			else:
				self.errorLog("Zone 2 mute and volume level contorl not supported with the " + device.states['speakerSystem'] + " speaker sytem layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > Speaker System setup menu.")
				
	#
	# Volume Down 1 dB (Zone 2)
	#
	def zone2volumeDown(self, action):
		# Decrement volume (zone 2) by 1 dB for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Volume Down 1 dB (zone 2) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			# If the current speaker system setup is not "A + Zone 2",
			#   zone mute and volume commands will be ignored.
			if device.states['speakerSystem'] == "A + Zone 2":
				command = "ZD"	# Volume Down
				self.sendCommand(device, command)
				self.sleep(0.1)
			else:
				self.errorLog("Zone 2 mute and volume level contorl not supported with the " + device.states['speakerSystem'] + " speaker sytem layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > Speaker System setup menu.")
				
	#
	# Set Volume in dB (Zone 2)
	#
	def zone2setVolume(self, action):
		# Set the volume (zone 2) for the device..
		device = indigo.devices[action.deviceId]
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		newValue = int(action.props.get('volume', "-90"))
		if newValue == -90:
			self.errorLog(u"No Zone 2 Volume was specified in action for \"" + device.name + "\"")
			return False
		
		self.debugLog("Set volume to " + str(newValue) + " dB (zone 2) for " + device.name)
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			# If the current speaker system setup is not "A + Zone 2",
			#   zone mute and volume commands will be ignored.
			if device.states['speakerSystem'] == "A + Zone 2":
				newValue = 81 + int(newValue)
				if newValue < 10:
					newValue = "0" + str(newValue)
				else:
					newValue = str(newValue)
				command = newValue + "ZV"	# Set Volume.
				self.sendCommand(device, command)
				self.sleep(0.1)
			else:
				self.errorLog("Zone 2 mute and volume level contorl not supported with the " + device.states['speakerSystem'] + " speaker sytem layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > Speaker System setup menu.")
				
	#
	# Mute On (Zone 2)
	#
	def zone2muteOn(self, action):
		# Turn on mute (zone 2) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Turning on mute (zone 2) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			# If the current speaker system setup is not "A + Zone 2",
			#   zone mute and volume commands will be ignored.
			if device.states['speakerSystem'] == "A + Zone 2":
				command = "Z2MO"	# Mute On
				self.sendCommand(device, command)
				self.sleep(0.1)
			else:
				self.errorLog("Zone 2 mute and volume level contorl not supported with the " + device.states['speakerSystem'] + " speaker sytem layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > Speaker System setup menu.")
				
	#
	# Mute Off (Zone 2)
	#
	def zone2muteOff(self, action):
		# Turn off (zone 2) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Turning off mute (zone 2) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			# If the current speaker system setup is not "A + Zone 2",
			#   zone mute and volume commands will be ignored.
			if device.states['speakerSystem'] == "A + Zone 2":
				command = "Z2MF"	# Mute Off
				self.sendCommand(device, command)
				self.sleep(0.1)
			else:
				self.errorLog("Zone 2 mute and volume level contorl not supported with the " + device.states['speakerSystem'] + " speaker sytem layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > Speaker System setup menu.")
				
	#
	# Mute Toggle (Zone 2)
	#
	def zone2muteToggle(self, action):
		# Toggle mute (zone 1) for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Toggling mute (zone 2) for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			# If the current speaker system setup is not "A + Zone 2",
			#   zone mute and volume commands will be ignored.
			if device.states['speakerSystem'] == "A + Zone 2":
				command = "Z2MZ"	# Toggle Mute
				self.sendCommand(device, command)
				self.sleep(0.1)
			else:
				self.errorLog("Zone 2 mute and volume level contorl not supported with the " + device.states['speakerSystem'] + " speaker sytem layout. The speaker system must be set to \"Zone 2\" in receiver's System Setup > Speaker System setup menu.")
				
	#
	# Set Input Source (Zone 2)
	#
	def zone2setSource(self, action):
		# Set the input source to something specific.
		device = indigo.devices[action.deviceId]
		self.debugLog("zone2setSource called.")
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		newValue = action.props['source']
		self.debugLog("Set input source to " + sourceNames[str(newValue)] + " (zone 2) for " + device.name)
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = newValue + "ZS"	# Set Source.
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Select Tuner Preset
	#
	def tunerPresetSelect(self, action):
		# Set the tuner preset to the specified preset.
		device = indigo.devices[action.deviceId]
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		newValue = action.props.get('tunerPreset', False)
		if not newValue:
			self.errorLog(u"No Tuner preset specified in action for \"" + device.name + "\"")
			return False
		
		# Define the tuner preset device property name based on the menu selection.
		propName = 'tunerPreset' + newValue.replace("0", "") + 'label'
		self.debugLog("tunerPresetSelect: Set tuner preset to " + device.pluginProps[propName] + " for " + device.name)
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			if (device.states['zone1source'] == 2) or (device.states['zone2source'] == 2):
				command = newValue + "PR"	# Select Tuner Preset.
				self.sendCommand(device, command)
				self.sleep(0.1)
			else:
				# Neither of zones 1 or 2 are using the Tuner.  Cannot set the preset.
				self.errorLog("Cannnot set tuner preset. The " + device.name + " zone 1 or 2 input source must be set to the tuner in order to set the tuner preset.")
				
	#
	# Set Tuner Frequency
	#
	def tunerFrequencySet(self, action):
		# Set the tuner band and frequency to the specified values.
		device = indigo.devices[action.deviceId]
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		frequency = action.props.get('frequency', False)
		band = action.props.get('band', False)
		if not band or not frequency:
			if not band:
				self.errorLog(u"A tuner Band must be selected for \"" + device.name + u"\"")
			if not frequency:
				self.errorLog(u"A tuner Frequency must be selected for \"" + device.name + u"\"")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			# Make sure we can actually change the frequency directly.
			if not device.states['zone1power']:
				# Zone 1 power is off.  Can't make any changes.
				self.errorLog("Cannot set tuner frequency. " + device.name + " zone 1 is currently turned off.")
			elif device.states['zone1source'] != 2:
				# Zone 1 source is not Tuner.  Cannot set frequency directly.
				self.errorLog("Cannnot set tuner frequency directly. " + device.name + " zone 1 input source must be set to the tuner in order to set the tuner frequency directly.")
			else:
				# Zone 1 power is on and input source is source 2. Send the commands.
				self.debugLog("tunerFrequencySet: Set tuner frequency to " + frequency + " " + band + " for " + device.name)
				# Define band change command and correct frequency character sequency.
				if band == "FM":
					bandCommand = "00TN"			# Command to set band to AM.
					frequency = frequency.replace(".", "")	# Remove the decimal.
					if len(frequency) < 3:
						frequency = frequency + "00"	# Add 2 trailing zeros.
					elif len(frequency) < 4:
						frequency = frequency + "0"	# Add 1 trailing zero.
					# Add another trailing zero if the frequency was 100 or higher.
					if frequency.startswith("1"):
						frequency = frequency + "0"
				elif band == "AM":
					bandCommand = "01TN"			# Command to set band to FM.
					if len(frequency) < 4:
						frequency = "0" + frequency	# Add a leading zero.
				
				# Start sending the command.
				self.sendCommand(device, bandCommand)	# Set the frequency band.
				self.sleep(0.1)						# Wait for the band to change.
				self.sendCommand(device, "TAC")		# Begin direct frequency entry.
				self.sleep(0.1)					
				for theChar in frequency:
					# Send each frequency number character individually.
					self.sendCommand(device, theChar + "TP")
					self.sleep(0.1)
				# Clear the device's preset state since entering a frequency directly.
				self.updateDeviceState(device, 'tunerPreset', "")
				
	#
	# Next Stereo Listening Mode
	#
	def listeningModeStereoNext(self, action):
		# Cycle through the next Stereo Listening Mode.
		device = indigo.devices[action.deviceId]
		self.debugLog("listeningModeStereoNext: Select next Stereo Listening Mode on " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "0001SR"
			self.sendCommand(device, command)
			self.sleep(0.1)
			# Wait a bit and get an update on the actual listening mode.
			self.sendCommand(device, "?S")
			self.sleep(0.1)
			
	#
	# Next Auto Surround/Stream Direct Listening Mode
	#
	def listeningModeAutoSurroundNext(self, action):
		# Cycle through the next Auto Surround Listening Mode.
		device = indigo.devices[action.deviceId]
		self.debugLog("listeningModeAutoSurroundNext: Select next Auto Surround Listening Mode on " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "0005SR"
			self.sendCommand(device, command)
			self.sleep(0.1)
			# Wait a bit and get an update on the actual listening mode.
			self.sendCommand(device, "?S")
			self.sleep(0.1)
			
	#
	# Next Advanced Surround Listening Mode
	#
	def listeningModeAdvancedSurroundNext(self, action):
		# Cycle through the next Advanced Surround Listening Mode.
		device = indigo.devices[action.deviceId]
		self.debugLog("listeningModeAdvancedSurroundNext: Select next Advanced Surround Listening Mode on " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			command = "0100SR"
			self.sendCommand(device, command)
			self.sleep(0.1)
			# Wait a bit and get an update on the actual listening mode.
			self.sendCommand(device, "?S")
			self.sleep(0.1)
			
	#
	# Select Listening Mode
	#
	def listeningModeSelect(self, action):
		# Set the Listening Mode setting to a specific setting.
		device = indigo.devices[action.deviceId]
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		command = action.props.get('listeningMode', False)
		if not command:
			self.errorLog(u"No Listening Mode selected in action for \"" + device.name + "\"")
			return False
		
		self.debugLog("listeningModeSelect: Select Listening Mode \"" + str(listeningModes[command]) + "\" on " + device.name)
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			# Make sure the listeningMode is valid.
			if listeningModes.get(command, None) == None:
				self.errorLog("Invalid listening mode ID \"" + command + "\" specified.")
				return
			
			# Add the proper characters to the listening mode ID to make it a valid command.
			command = command + "SR"
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Next MCACC Memory
	#
	def mcaccNext(self, action):
		# Select the next MCACC setting memory.
		device = indigo.devices[action.deviceId]
		self.debugLog("mcaccNext called for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			mcaccMemory = device.states['mcaccMemory']
			mcaccMemory += 1
			if mcaccMemory > 6:
				mcaccMemory = 1
			command = str(mcaccMemory) + "MC"
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Previous MCACC Memory
	#
	def mcaccPrevious(self, action):
		# Select the previous MCACC setting memory.
		device = indigo.devices[action.deviceId]
		self.debugLog("mcaccPrevious called for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			mcaccMemory = device.states['mcaccMemory']
			mcaccMemory -= 1
			if mcaccMemory < 1:
				mcaccMemory = 6
			command = str(mcaccMemory) + "MC"
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Select MCACC Memory
	#
	def mcaccSelect(self, action):
		# Set the MCACC Memory setting to something specific.
		device = indigo.devices[action.deviceId]
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		command = action.props.get('mcaccMemory', False)
		if not command:
			self.errorLog(u"No MCACC Memory selected in action for \"" + device.name + "\"")
			return False
		
		self.debugLog("mcaccSelect: Recall MCACC Memory number " + command[0:1] + " on " + device.name)
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Send Remote Control Button Press
	#
	def remoteButtonPress(self, action):
		# Send a remote control button press to the receiver.
		device = indigo.devices[action.deviceId]
		error = False		# Used to track if there was an error or not.
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		source = device.states['zone1source']
		command = action.props.get('remoteButton', False)
		if not command:
			self.errorLog(u"No Remote Button was specified in action for \"" + device.name + "\"")
			return False
		
		self.debugLog("remoteButtonPress called: command: " + command + " for " + device.name)
		
		# For VSX-1021-K
		if device.deviceTypeId == "vsx1021k":
			# Define the translation from submitted button command to correct
			#   source command.
			# 02 - Tuner
			# The below button maps work on the first button press, but don't for subsequent presses.
			# source2commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN", 'CRT':"CRT", 'STS':"06TN"}
			# The Pioneer VSX-1021-K Used to test this plugin exhibited a bug
			#   when using the "TFI" and "TFD" commands where the receiver would
			#   completely mute the tuner even across power cycles. The tuner could
			#   only be un-muted by pressing a tuner control button on the IR remote
			#   or on the receiver front panel.  For this reason, the "TFI" and "TFD"
			#   tuner frequency increment/decrement commands have been omitted.
			source2commandMap = {'CRI':"TPI", 'CLE':"TPD", 'CEN':"03TN", 'CRT':"04TN", 'STS':"06TN"}
			# 17 - iPod/USB
			# The below button maps work on the first button press, but don't for subsequent presses.
			# source17commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN", 'CRT':"CRT", 'STS':"09IP", '00IP':"00IP", '01IP':"01IP", '02IP':"02IP", '03IP':"03IP", '04IP':"04IP", '07IP':"07IP", '08IP':"08IP", '19SI':"19IP"}
			source17commandMap = {'CUP':"13IP", 'CDN':"14IP", 'CRI':"15IP", 'CLE':"16IP", 'CEN':"17IP", 'CRT':"18IP", 'STS':"09IP", '00IP':"00IP", '01IP':"01IP", '02IP':"02IP", '03IP':"03IP", '04IP':"04IP", '07IP':"07IP", '08IP':"08IP", '19SI':"19IP"}
			# 26 - HMG (Home Media Gallery/Internet Radio)
			# The below button maps work on the first button press, but don't for subsequent presses.
			# source26commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN", 'CRT':"CRT", 'STS':"18NW", '00IP':"10NW", '01IP':"11NW", '02IP':"20NW", '03IP':"12NW", '04IP':"12NW", '07IP':"34NW", '08IP':"35NW", '19SI':"36NW", '00SI':"00NW", '01SI':"01NW", '02SI':"02NW", '03SI':"03NW", '04SI':"04NW", '05SI':"04NW", '06SI':"05NW", '07SI':"07NW", '08SI':"08NW", '09SI':"09NW"}
			source26commandMap = {'CUP':"26NW", 'CDN':"27NW", 'CRI':"28NW", 'CLE':"29NW", 'CEN':"30NW", 'CRT':"31NW", 'STS':"18NW", '00IP':"10NW", '01IP':"11NW", '02IP':"20NW", '03IP':"12NW", '04IP':"12NW", '07IP':"34NW", '08IP':"35NW", '19SI':"36NW", '00SI':"00NW", '01SI':"01NW", '02SI':"02NW", '03SI':"03NW", '04SI':"04NW", '05SI':"04NW", '06SI':"05NW", '07SI':"07NW", '08SI':"08NW", '09SI':"09NW"}
			# 27 - Sirius
			# The below button maps work on the first button press, but don't for subsequent presses.
			# source27commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN", 'CRT':"CRT", 'STS':"14SI", '19SI':"19SI", '00SI':"00SI", '01SI':"01SI", '02SI':"02SI", '03SI':"03SI", '04SI':"04SI", '05SI':"04SI", '06SI':"05SI", '07SI':"07SI", '08SI':"08SI", '09SI':"09SI"}
			source27commandMap = {'CUP':"10SI", 'CDN':"11SI", 'CRI':"12SI", 'CLE':"13SI", 'CEN':"21SI", 'CRT':"22SI", 'STS':"14SI", '19SI':"19SI", '00SI':"00SI", '01SI':"01SI", '02SI':"02SI", '03SI':"03SI", '04SI':"04SI", '05SI':"04SI", '06SI':"05SI", '07SI':"07SI", '08SI':"08SI", '09SI':"09SI"}
			# 33 - Adapter Port
			# The below button maps work on the first button press, but don't for subsequent presses.
			# source33commandMap = {'HM':"HM", 'CUP':"CUP", 'CDN':"CDN", 'CRI':"CRI", 'CLE':"CLE", 'CEN':"CEN", 'CRT':"CRT", '00IP':"10BT", '01IP':"11BT", '02IP':"12BT", '03IP':"13BT", '04IP':"14BT"}
			source33commandMap = {'CRI':"23BT", 'CLE':"24BT", 'CEN':"25BT", 'CRT':"26BT", '00IP':"10BT", '01IP':"11BT", '02IP':"12BT", '03IP':"13BT", '04IP':"14BT"}
			# List of default cursor button commands to use if the above sources aren't the current input source.
			defaultCursorCommands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']
			
			# Translate the command based on the current zone 1 input source.
			if source == 2:
				# See if the requested command is compatible with this input source.
				command = source2commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 17:
				command = source17commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 26:
				command = source26commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 27:
				command = source27commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 33:
				command = source33commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			else:
				# Current zone 1 input source is something other than the special ones above.
				#   Make sure the command being sent is one of the standard commands.
				if command not in defaultCursorCommands:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			
			# Send the command if no errors.
			if not error:
				self.sendCommand(device, command)
				self.sleep(0.1)
		
		# For VSX-1022-K
		if device.deviceTypeId == "vsx1022k":
			# Define the translation from submitted button command to correct
			#   source command.
			#
			# THIS HAS NOT BEEN UPDATED FOR ALL VSX-1022-K SUPPORTED SOURCES.
			#
			# 02 - Tuner
			source2commandMap = {'CUP':"TFI", 'CDN':"TFD", 'CRI':"TPI", 'CLE':"TPD", 'CEN':"03TN", 'CRT':"04TN", 'STS':"06TN"}
			# 17 - iPod/USB
			source17commandMap = {'CUP':"13IP", 'CDN':"14IP", 'CRI':"15IP", 'CLE':"16IP", 'CEN':"17IP", 'CRT':"18IP", 'STS':"09IP", '00IP':"00IP", '01IP':"01IP", '02IP':"02IP", '03IP':"03IP", '04IP':"04IP", '07IP':"07IP", '08IP':"08IP", '19SI':"19IP"}
			# 26 - HMG (Home Media Gallery/Internet Radio)
			source26commandMap = {'CUP':"26NW", 'CDN':"27NW", 'CRI':"28NW", 'CLE':"29NW", 'CEN':"30NW", 'CRT':"31NW", 'STS':"18NW", '00IP':"10NW", '01IP':"11NW", '02IP':"20NW", '03IP':"12NW", '04IP':"12NW", '07IP':"34NW", '08IP':"35NW", '19SI':"36NW", '00SI':"00NW", '01SI':"01NW", '02SI':"02NW", '03SI':"03NW", '04SI':"04NW", '05SI':"04NW", '06SI':"05NW", '07SI':"07NW", '08SI':"08NW", '09SI':"09NW"}
			# 27 - Sirius
			source27commandMap = {'CUP':"10SI", 'CDN':"11SI", 'CRI':"12SI", 'CLE':"13SI", 'CEN':"21SI", 'CRT':"22SI", 'STS':"14SI", '19SI':"19SI", '00SI':"00SI", '01SI':"01SI", '02SI':"02SI", '03SI':"03SI", '04SI':"04SI", '05SI':"04SI", '06SI':"05SI", '07SI':"07SI", '08SI':"08SI", '09SI':"09SI"}
			# 33 - Adapter Port
			source33commandMap = {'CRI':"23BT", 'CLE':"24BT", 'CEN':"25BT", 'CRT':"26BT", '00IP':"10BT", '01IP':"11BT", '02IP':"12BT", '03IP':"13BT", '04IP':"14BT"}
			# List of default cursor button commands to use if the above sources aren't the current input source.
			defaultCursorCommands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']
			
			# Translate the command based on the current zone 1 input source.
			if source == 2:
				# See if the requested command is compatible with this input source.
				command = source2commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 17:
				command = source17commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 26:
				command = source26commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 27:
				command = source27commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 33:
				command = source33commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			else:
				# Current zone 1 input source is something other than the special ones above.
				#   Make sure the command being sent is one of the standard commands.
				if command not in defaultCursorCommands:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			
			# Send the command if no errors.
			if not error:
				self.sendCommand(device, command)
				self.sleep(0.1)
		
		# For VSX-1122-K
		if device.deviceTypeId == "vsx1122k":
			# Define the translation from submitted button command to correct
			#   source command.
			#
			# THIS HAS NOT BEEN UPDATED FOR ALL VSX-1122-K SUPPORTED SOURCES.
			#
			# 02 - Tuner
			source2commandMap = {'CUP':"TFI", 'CDN':"TFD", 'CRI':"TPI", 'CLE':"TPD", 'CEN':"03TN", 'CRT':"04TN", 'STS':"06TN"}
			# 17 - iPod/USB
			source17commandMap = {'CUP':"13IP", 'CDN':"14IP", 'CRI':"15IP", 'CLE':"16IP", 'CEN':"17IP", 'CRT':"18IP", 'STS':"09IP", '00IP':"00IP", '01IP':"01IP", '02IP':"02IP", '03IP':"03IP", '04IP':"04IP", '07IP':"07IP", '08IP':"08IP", '19SI':"19IP"}
			# 26 - HMG (Home Media Gallery/Internet Radio)
			source26commandMap = {'CUP':"26NW", 'CDN':"27NW", 'CRI':"28NW", 'CLE':"29NW", 'CEN':"30NW", 'CRT':"31NW", 'STS':"18NW", '00IP':"10NW", '01IP':"11NW", '02IP':"20NW", '03IP':"12NW", '04IP':"12NW", '07IP':"34NW", '08IP':"35NW", '19SI':"36NW", '00SI':"00NW", '01SI':"01NW", '02SI':"02NW", '03SI':"03NW", '04SI':"04NW", '05SI':"04NW", '06SI':"05NW", '07SI':"07NW", '08SI':"08NW", '09SI':"09NW"}
			# 27 - Sirius
			source27commandMap = {'CUP':"10SI", 'CDN':"11SI", 'CRI':"12SI", 'CLE':"13SI", 'CEN':"21SI", 'CRT':"22SI", 'STS':"14SI", '19SI':"19SI", '00SI':"00SI", '01SI':"01SI", '02SI':"02SI", '03SI':"03SI", '04SI':"04SI", '05SI':"04SI", '06SI':"05SI", '07SI':"07SI", '08SI':"08SI", '09SI':"09SI"}
			# 33 - Adapter Port
			source33commandMap = {'CRI':"23BT", 'CLE':"24BT", 'CEN':"25BT", 'CRT':"26BT", '00IP':"10BT", '01IP':"11BT", '02IP':"12BT", '03IP':"13BT", '04IP':"14BT"}
			# List of default cursor button commands to use if the above sources aren't the current input source.
			defaultCursorCommands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']
			
			# Translate the command based on the current zone 1 input source.
			if source == 2:
				# See if the requested command is compatible with this input source.
				command = source2commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 17:
				command = source17commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 26:
				command = source26commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 27:
				command = source27commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 33:
				command = source33commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			else:
				# Current zone 1 input source is something other than the special ones above.
				#   Make sure the command being sent is one of the standard commands.
				if command not in defaultCursorCommands:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			
			# Send the command if no errors.
			if not error:
				self.sendCommand(device, command)
				self.sleep(0.1)

		# For VSX-1123-K
		if device.deviceTypeId == "vsx1123k":
			# Define the translation from submitted button command to correct
			#   source command.
			#
			# THIS HAS NOT BEEN UPDATED FOR ALL VSX-1123-K SUPPORTED SOURCES.
			#
			# 02 - Tuner
			source2commandMap = {'CUP':"TFI", 'CDN':"TFD", 'CRI':"TPI", 'CLE':"TPD", 'CEN':"03TN", 'CRT':"04TN", 'STS':"06TN"}
			# 17 - iPod/USB
			source17commandMap = {'CUP':"13IP", 'CDN':"14IP", 'CRI':"15IP", 'CLE':"16IP", 'CEN':"17IP", 'CRT':"18IP", 'STS':"09IP", '00IP':"00IP", '01IP':"01IP", '02IP':"02IP", '03IP':"03IP", '04IP':"04IP", '07IP':"07IP", '08IP':"08IP", '19SI':"19IP"}
			# 26 - HMG (Home Media Gallery/Internet Radio)
			source26commandMap = {'CUP':"26NW", 'CDN':"27NW", 'CRI':"28NW", 'CLE':"29NW", 'CEN':"30NW", 'CRT':"31NW", 'STS':"18NW", '00IP':"10NW", '01IP':"11NW", '02IP':"20NW", '03IP':"12NW", '04IP':"12NW", '07IP':"34NW", '08IP':"35NW", '19SI':"36NW", '00SI':"00NW", '01SI':"01NW", '02SI':"02NW", '03SI':"03NW", '04SI':"04NW", '05SI':"04NW", '06SI':"05NW", '07SI':"07NW", '08SI':"08NW", '09SI':"09NW"}
			# 27 - Sirius
			source27commandMap = {'CUP':"10SI", 'CDN':"11SI", 'CRI':"12SI", 'CLE':"13SI", 'CEN':"21SI", 'CRT':"22SI", 'STS':"14SI", '19SI':"19SI", '00SI':"00SI", '01SI':"01SI", '02SI':"02SI", '03SI':"03SI", '04SI':"04SI", '05SI':"04SI", '06SI':"05SI", '07SI':"07SI", '08SI':"08SI", '09SI':"09SI"}
			# 33 - Adapter Port
			source33commandMap = {'CRI':"23BT", 'CLE':"24BT", 'CEN':"25BT", 'CRT':"26BT", '00IP':"10BT", '01IP':"11BT", '02IP':"12BT", '03IP':"13BT", '04IP':"14BT"}
			# List of default cursor button commands to use if the above sources aren't the current input source.
			defaultCursorCommands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']
			
			# Translate the command based on the current zone 1 input source.
			if source == 2:
				# See if the requested command is compatible with this input source.
				command = source2commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 17:
				command = source17commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 26:
				command = source26commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 27:
				command = source27commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 33:
				command = source33commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			else:
				# Current zone 1 input source is something other than the special ones above.
				#   Make sure the command being sent is one of the standard commands.
				if command not in defaultCursorCommands:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
		
		# For SC-75
		if device.deviceTypeId == "sc75":
			# Define the translation from submitted button command to correct
			#   source command.
			#
			# THIS HAS NOT BEEN UPDATED FOR ALL SC-75 SUPPORTED SOURCES.
			#
			# 02 - Tuner
			source2commandMap = {'CUP':"TFI", 'CDN':"TFD", 'CRI':"TPI", 'CLE':"TPD", 'CEN':"03TN", 'CRT':"04TN", 'STS':"06TN"}
			# 17 - iPod/USB
			source17commandMap = {'CUP':"13IP", 'CDN':"14IP", 'CRI':"15IP", 'CLE':"16IP", 'CEN':"17IP", 'CRT':"18IP", 'STS':"09IP", '00IP':"00IP", '01IP':"01IP", '02IP':"02IP", '03IP':"03IP", '04IP':"04IP", '07IP':"07IP", '08IP':"08IP", '19SI':"19IP"}
			# 26 - HMG (Home Media Gallery/Internet Radio)
			source26commandMap = {'CUP':"26NW", 'CDN':"27NW", 'CRI':"28NW", 'CLE':"29NW", 'CEN':"30NW", 'CRT':"31NW", 'STS':"18NW", '00IP':"10NW", '01IP':"11NW", '02IP':"20NW", '03IP':"12NW", '04IP':"12NW", '07IP':"34NW", '08IP':"35NW", '19SI':"36NW", '00SI':"00NW", '01SI':"01NW", '02SI':"02NW", '03SI':"03NW", '04SI':"04NW", '05SI':"04NW", '06SI':"05NW", '07SI':"07NW", '08SI':"08NW", '09SI':"09NW"}
			# 33 - Adapter Port
			source33commandMap = {'CRI':"23BT", 'CLE':"24BT", 'CEN':"25BT", 'CRT':"26BT", '00IP':"10BT", '01IP':"11BT", '02IP':"12BT", '03IP':"13BT", '04IP':"14BT"}
			# List of default cursor button commands to use if the above sources aren't the current input source.
			defaultCursorCommands = ['HM', 'CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', 'STS']
			
			# Translate the command based on the current zone 1 input source.
			if source == 2:
				# See if the requested command is compatible with this input source.
				command = source2commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 17:
				command = source17commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 26:
				command = source26commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 27:
				command = source27commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			elif source == 33:
				command = source33commandMap.get(command, "")
				if len(command) == 0:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
			else:
				# Current zone 1 input source is something other than the special ones above.
				#   Make sure the command being sent is one of the standard commands.
				if command not in defaultCursorCommands:
					self.errorLog(device.name + ": remote control button " + remoteButtonNames.get(action.props['remoteButton'], "") + " is not supported by the " + device.states['zone1sourceName'] + " input source. Action ignored.")
					error = True
					
			# Send the command if no errors.
			if not error:
				self.sendCommand(device, command)
				self.sleep(0.1)
	
	#
	# Set Display Brightness
	#
	def setDisplayBrightness(self, action):
		# Set the front display brightness.
		device = indigo.devices[action.deviceId]
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		command = action.props.get('displayBrightness', False)
		if not command:
			self.errorLog(u"No Display Brightness setting was specified in action for \"" + device.name + "\"")
			return False
		
		self.debugLog("setDisplayBrightness called: command: " + command + " for " + device.name)
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Set Sleep Timer
	#
	def setSleepTimer(self, action):
		# Set the sleep timer minutes (or off).
		device = indigo.devices[action.deviceId]
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		command = action.props.get('sleepTime', False)
		if not command:
			self.errorLog(u"No Sleep Time was specified in action for \"" + device.name + "\"")
			return False
		
		self.debugLog("setSleepTimer called: command: " + command + " for " + device.name)
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Send Raw Command
	#
	def sendRawCommand(self, action):
		# Send a command directly to the receiver.
		device = indigo.devices[action.deviceId]
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		command = action.props.get('command', False)
		if not command:
			self.errorLog(u"No Command was specified in action for \"" + device.name + "\"")
			return False
		
		self.debugLog("sendRawCommand called: command: " + command + " for " + device.name)
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			self.sendCommand(device, command)
			self.sleep(0.1)
			
	#
	# Refresh All States
	#
	def refreshAllStates(self, action):
		# Refresh all states for a device.
		device = indigo.devices[action.deviceId]
		self.debugLog("Refresh all states for " + device.name)
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return False
		
		# Make sure it's not a virtual volume device.
		if device.deviceTypeId != "virtualVolume":
			self.getReceiverStatus(device)
			
			
	########################################
	# Virtual Level Controller
	#   (Class-Supported)
	########################################
	def actionControlDimmerRelay(self, action, device):
		try:
			self.debugLog("actionControlDimmerRelay called for device " + device.name + ". action: " + str(action) + "\n\ndevice: " + str(device))
		except Exception, e:
			self.debugLog("actionControlDimmerRelay called for device " + device.name + ". (Unable to display action or device data due to error: " + str(e) + ")")
		receiverDeviceId = device.pluginProps.get('receiverDeviceId', "")
		controlDestination = device.pluginProps.get('controlDestination', "")
		# Get the current brightness and on-state of the device.
		currentBrightness = device.states['brightnessLevel']
		currentOnState = device.states['onOffState']
		# Verify the validity of the data.
		if len(receiverDeviceId) < 1:
			self.errorLog(device.name + " is not set to control any receiver device. Double-click the " + device.name + " device in Indigo to select a receiver to control.")
			self.updateDeviceState(device, 'onOffState', currentOnState)
			self.updateDeviceState(device, 'brightnessLevel', 0)
			return
		if int(receiverDeviceId) not in self.deviceList:
			self.errorLog(device.name + " is configured to control a receiver device that no longer exists. Double-click the " + device.name + " device in Indigo to select a receiver to control.")
			self.updateDeviceState(device, 'onOffState', currentOnState)
			self.updateDeviceState(device, 'brightnessLevel', 0)
			return
		# Get the receiver device object.
		receiverDeviceId = int(receiverDeviceId)
		receiver = indigo.devices[receiverDeviceId]
		
		###### TURN ON ######
		if action.deviceAction == indigo.kDeviceAction.TurnOn:
			try:
				self.debugLog("device on:\n%s" % action)
			except Exception, e:
				self.debugLog("device on: (Unable to display action data due to error: " + str(e) + ")")
			# Select the proper action based on the controlDestination value.
			# VOLUME / MUTE
			if controlDestination == "zone1volume" or controlDestination == "zone2volume":
				try:
					# Turn off the select zone's mute.
					if controlDestination == "zone1volume":
						# Execute the action.
						self.sendCommand(receiver, "MF")
					if controlDestination == "zone2volume":
						# Execute the action.
						self.sendCommand(receiver, "Z2MF")
				except Exception, e:
					self.errorLog(device.name + ": Error executing Mute Off action for receiver device " + receiver.name + ". " + str(e))
			
		###### TURN OFF ######
		elif action.deviceAction == indigo.kDeviceAction.TurnOff:
			try:
				self.debugLog("device off:\n%s" % action)
			except Exception, e:
				self.debugLog("device off: (Unable to display action due to error: " + str(e) + ")")
			# Select the proper action based on the controlDestination value.
			# VOLUME / MUTE
			if controlDestination == "zone1volume" or controlDestination == "zone2volume":
				try:
					# Turn on the select zone's mute.
					if controlDestination == "zone1volume":
						self.sendCommand(receiver, "MO")
					if controlDestination == "zone2volume":
						self.sendCommand(receiver, "Z2MO")
				except Exception, e:
					self.errorLog(device.name + ": Error executing Mute On action for receiver device " + receiver.name + ". " + str(e))
			
		###### TOGGLE ######
		elif action.deviceAction == indigo.kDeviceAction.Toggle:
			try:
				self.debugLog("device toggle:\n%s" % action)
			except Exception, e:
				self.debugLog("device toggle: (Unable to display action due to error: " + str(e) + ")")
			# Select the proper action based on the controlDestination value.
			# VOLUME / MUTE
			if controlDestination == "zone1volume" or controlDestination == "zone2volume":
				# Turn off or on the select zone's mute, depending on current state.
				try:
					# Turn on mute if toggling device to "Off". Turn off mute if
					#   toggling the device to "On".
					if device.states['onOffState'] == True:
						if controlDestination == "zone1volume":
							self.sendCommand(receiver, "MO")	# Zone 1 Mute On
						if controlDestination == "zone2volume":
							self.sendCommand(receiver, "Z2MO")	# Zone 2 Mute On
						# device.updateStateOnServer('onOffState', False)
					else:
						if controlDestination == "zone1volume":
							self.sendCommand(receiver, "MF")	# Zone 1 Mute Off
						if controlDestination == "zone2volume":
							self.sendCommand(receiver, "Z2MF")	# Zone 2 Mute Off
				except Exception, e:
					self.errorLog(device.name + ": Error executing Mute On action for receiver device " + receiver.name + ". " + str(e))

		###### SET BRIGHTNESS ######
		elif action.deviceAction == indigo.kDeviceAction.SetBrightness:
			try:
				self.debugLog("device set brightness:\n%s" % action)
			except Exception, e:
				self.debugLog("device set brightness: (Unable to display action due to error: " + str(e) + ")")
			# Select the proper action based on the controlDestination value.
			# VOLUME / MUTE
			if controlDestination == "zone1volume" or controlDestination == "zone2volume":
				try:
					brightnessLevel = action.actionValue
					# Convert the brightness level to a valid volume command.
					if controlDestination == "zone1volume":
						# This formula converts from the 100 unit scale to the 161 unit
						#   scale used by the receiver's zone 1 volume commands.
						theVolume = int(round(161*0.01*brightnessLevel, 0))
						if theVolume < 10:
							theVolume = "00" + str(theVolume)
						elif theVolume < 100:
							theVolume = "0" + str(theVolume)
						else:
							theVolume = str(theVolume)
						# Turn mute off if it's on.
						if receiver.states['zone1mute']:
							self.sendCommand(receiver, "MF")
						# Now send the volume command.
						command = theVolume + "VL"	# Set Volume.
						self.sendCommand(receiver, command)
						self.debugLog("actionControlDimmerRelay: brightnessLevel: " + str(brightnessLevel) + ", theVolume: " + theVolume)
					elif controlDestination == "zone2volume":
						# This formula converts from the 100 unit scale to the 81 unit
						#   scale used by the receiver's zone 2 volume commands.
						theVolume = int(round(81*0.01*brightnessLevel, 0))
						if theVolume < 10:
							theVolume = "0" + str(theVolume)
						else:
							theVolume = str(theVolume)
						# Turn mute off if it's on.
						if receiver.states['zone2mute']:
							self.sendCommand(receiver, "Z2MF")
						# Now send the volume command.
						command = theVolume + "ZV"	# Set Volume.
						self.sendCommand(receiver, command)
						self.debugLog("actionControlDimmerRelay: brightnessLevel: " + str(brightnessLevel) + ", theVolume: " + theVolume)
				except Exception, e:
					self.errorLog(device.name + ": Error executing Set Volume action for receiver device " + receiver.name + ". " + str(e))
		
		###### BRIGHTEN BY ######
		elif action.deviceAction == indigo.kDeviceAction.BrightenBy:
			try:
				self.debugLog("device brighten by:\n%s" % action)
			except Exception, e:
				self.debugLog("device brighten by: (Unable to display action due to error: " + str(e) + ")")
			# Select the proper action based on the controlDestination value.
			# VOLUME / MUTE
			if controlDestination == "zone1volume" or controlDestination == "zone2volume":
				try:
					# Convert the brightness level to a valid volume command.
					if controlDestination == "zone1volume":
						# Set the currentBrightness to the current receiver volume.
						#   We're doing this because if the receiver is muted, this
						#   virtual device will have a brightness of 0 and brightening
						#   by any thing will set brightness to 0 plus the brighten amount.
						currentBrightness = int(100-round(float(receiver.states['zone1volume'])/-80.5*100, 0))
						brightnessLevel = currentBrightness + int(action.actionValue)
						# Sanity check...
						if brightnessLevel > 100:
							brightnessLevel = 100
						self.debugLog("   set brightness of " + device.name + " to " + str(brightnessLevel))
						# This formula converts from the 100 unit scale to the 161 unit
						#   scale used by the receiver's zone 1 volume commands.
						theVolume = int(round(161*0.01*brightnessLevel, 0))
						if theVolume < 10:
							theVolume = "00" + str(theVolume)
						elif theVolume < 100:
							theVolume = "0" + str(theVolume)
						else:
							theVolume = str(theVolume)
						# Turn mute off if it's on.
						if receiver.states['zone1mute']:
							self.sendCommand(receiver, "MF")
						# Now send the volume command.
						command = theVolume + "VL"	# Set Volume.
						self.sendCommand(receiver, command)
						self.debugLog("actionControlDimmerRelay: brightnessLevel: " + str(brightnessLevel) + ", theVolume: " + theVolume)
					elif controlDestination == "zone2volume":
						# Set the currentBrightness to the current receiver volume.
						#   We're doing this because if the receiver is muted, this
						#   virtual device will have a brightness of 0 and brightening
						#   by any thing will set brightness to 0 plus the brighten amount.
						currentBrightness = int(100-round(float(receiver.states['zone2volume'])/-81*100, 0))
						brightnessLevel = currentBrightness + int(action.actionValue)
						# Sanity check...
						if brightnessLevel > 100:
							brightnessLevel = 100
						self.debugLog("   set brightness of " + device.name + " to " + str(brightnessLevel))
						# This formula converts from the 100 unit scale to the 81 unit
						#   scale used by the receiver's zone 2 volume commands.
						theVolume = int(round(81*0.01*brightnessLevel, 0))
						if theVolume < 10:
							theVolume = "0" + str(theVolume)
						else:
							theVolume = str(theVolume)
						# Turn mute off if it's on.
						if receiver.states['zone2mute']:
							self.sendCommand(receiver, "Z2MF")
						# Now send the volume command.
						command = theVolume + "ZV"	# Set Volume.
						self.sendCommand(receiver, command)
						self.debugLog("actionControlDimmerRelay: brightnessLevel: " + str(brightnessLevel) + ", theVolume: " + theVolume)
				except Exception, e:
					self.errorLog(device.name + ": Error executing Set Volume action for receiver device " + receiver.name + ". " + str(e))
		
		###### DIM BY ######
		elif action.deviceAction == indigo.kDeviceAction.DimBy:
			try:
				self.debugLog("device dim by:\n%s" % action)
			except Exception, e:
				self.debugLog("device dim by: (Unable to display action due to error: " + str(e) + ")")
			brightnessLevel = currentBrightness - int(action.actionValue)
			# Sanity check...
			if brightnessLevel < 0:
				brightnessLevel = 0
			self.debugLog("   set brightness of " + device.name + " to " + str(brightnessLevel))
			# Select the proper action based on the controlDestination value.
			# VOLUME / MUTE
			if controlDestination == "zone1volume" or controlDestination == "zone2volume":
				try:
					# Convert the brightness level to a valid volume command.
					if controlDestination == "zone1volume":
						# This formula converts from the 100 unit scale to the 161 unit
						#   scale used by the receiver's zone 1 volume commands.
						theVolume = int(round(161*0.01*brightnessLevel, 0))
						if theVolume < 10:
							theVolume = "00" + str(theVolume)
						elif theVolume < 100:
							theVolume = "0" + str(theVolume)
						else:
							theVolume = str(theVolume)
						# Turn mute off if it's on.
						if receiver.states['zone1mute']:
							self.sendCommand(receiver, "MF")
						# Now send the volume command.
						command = theVolume + "VL"	# Set Volume.
						self.sendCommand(receiver, command)
						self.debugLog("actionControlDimmerRelay: brightnessLevel: " + str(brightnessLevel) + ", theVolume: " + theVolume)
					elif controlDestination == "zone2volume":
						# This formula converts from the 100 unit scale to the 81 unit
						#   scale used by the receiver's zone 2 volume commands.
						theVolume = int(round(81*0.01*brightnessLevel, 0))
						if theVolume < 10:
							theVolume = "0" + str(theVolume)
						else:
							theVolume = str(theVolume)
						# Turn mute off if it's on.
						if receiver.states['zone2mute']:
							self.sendCommand(receiver, "Z2MF")
						# Now send the volume command.
						command = theVolume + "ZV"	# Set Volume.
						self.sendCommand(receiver, command)
						self.debugLog("actionControlDimmerRelay: brightnessLevel: " + str(brightnessLevel) + ", theVolume: " + theVolume)
				except Exception, e:
					self.errorLog(device.name + ": Error executing Set Volume action for receiver device " + receiver.name + ". " + str(e))
	
	
	########################################
	# UI Interaction Methods
	#   (Class-Supported)
	########################################
	
	# Actions Dialog
	########################################
	def validateActionConfigUi(self, valuesDict, typeId, deviceId):
		self.debugLog("validateActionConfigUi called.")
		self.debugLog("typeId: " + str(typeId) + u", deviceId: " + str(deviceId))
		try:
			self.debugLog("valuesDict: " + str(valuesDict))
		except Exception, e:
			self.debugLog("(Unable to display valuesDict due to error: " + str(e) + ")")
		
		device = indigo.devices[deviceId]
		errorMsgDict = indigo.Dict()
		descString = u""
		
		#
		# Set Volume dB (Zone 1)
		#
		if typeId == "zone1setVolume":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['volume'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['volume']
				return (False, valuesDict, errorMsgDict)
			
			try:
				theNumber = float(valuesDict.get('volume', "-90"))
			except ValueError:
				errorMsgDict['volume'] = u"The volume must be a number between -80.5 and 12 dB."
				errorMsgDict['showAlertText'] = errorMsgDict['volume']
				return (False, valuesDict, errorMsgDict)
			
			if (theNumber < -80.5) or (theNumber > 12.0):
				errorMsgDict['volume'] = u"The volume must be a number between -80.5 and 12 dB."
				errorMsgDict['showAlertText'] = errorMsgDict['volume']
				return (False, valuesDict, errorMsgDict)
				
			if theNumber%0.5 != 0:
				errorMsgDict['volume'] = u"The volume must be evenly divisible by 0.5 dB."
				errorMsgDict['showAlertText'] = errorMsgDict['volume']
				return (False, valuesDict, errorMsgDict)
				
			descString += u"set volume (zone 1) to " + str(theNumber)
		
		#
		# Set Source (Zone 1)
		#
		if typeId == "zone1setSource":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['source'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['source']
				return (False, valuesDict, errorMsgDict)
			
			theSource = valuesDict['source']
			propName = "source" + theSource + "label"
			theName = device.pluginProps.get(propName, "")
			if len(theName) < 1:
				errorMsgDict['source'] = u"Please select an Input Soure."
				errorMsgDict['showAlertText'] = errorMsgDict['source']
				return (False, valuesDict, errorMsgDict)
				
			if device.deviceTypeId == "vsx1021k":
				if theSource in vsx1021kSourceMask:
					errorMsgDict['source'] = u"The selected source is not available on this receiver. Choose a different source."
					errorMsgDict['showAlertText'] = errorMsgDict['source']
					return (False, valuesDict, errorMsgDict)
			elif device.deviceTypeId == "vsx1022k":
				if theSource in vsx1022kSourceMask:
					errorMsgDict['source'] = u"The selected source is not available on this receiver. Choose a different source."
					errorMsgDict['showAlertText'] = errorMsgDict['source']
					return (False, valuesDict, errorMsgDict)
			elif device.deviceTypeId == "vsx1122k":
				if theSource in vsx1122kSourceMask:
					errorMsgDict['source'] = u"The selected source is not available on this receiver. Choose a different source."
					errorMsgDict['showAlertText'] = errorMsgDict['source']
					return (False, valuesDict, errorMsgDict)
			elif device.deviceTypeId == "vsx1123k":
				if theSource in vsx1123kSourceMask:
					errorMsgDict['source'] = u"The selected source is not available on this receiver. Choose a different source."
					errorMsgDict['showAlertText'] = errorMsgDict['source']
					return (False, valuesDict, errorMsgDict)
			elif device.deviceTypeId == "sc75":
				if theSource in sc75SourceMask:
					errorMsgDict['source'] = u"The selected source is not available on this receiver. Choose a different source."
					errorMsgDict['showAlertText'] = errorMsgDict['source']
					return (False, valuesDict, errorMsgDict)
			
			descString += u"set input source (zone 1) to " + str(theName)
		
		#
		# Set Volume dB (Zone 2)
		#
		if typeId == "zone2setVolume":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['volume'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['volume']
				return (False, valuesDict, errorMsgDict)
			
			try:
				theNumber = int(valuesDict.get('volume', "-90"))
			except ValueError:
				errorMsgDict['volume'] = u"The volume must be a whole number between -81 and 0 dB."
				errorMsgDict['showAlertText'] = errorMsgDict['volume']
				return (False, valuesDict, errorMsgDict)
			
			if (theNumber < -81) or (theNumber > 0):
				errorMsgDict['volume'] = u"The volume must be a whole number between -81 and 0 dB."
				errorMsgDict['showAlertText'] = errorMsgDict['volume']
				return (False, valuesDict, errorMsgDict)
			
			descString += u"set volume (zone 2) to " + str(theNumber)
		
		#
		# Set Source (Zone 2)
		#
		if typeId == "zone2setSource":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['source'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['source']
				return (False, valuesDict, errorMsgDict)
			
			theSource = valuesDict['source']
			propName = "source" + theSource + "label"
			theName = device.pluginProps.get(propName, "")
			if len(theName) < 1:
				errorMsgDict['source'] = u"Please select an Input Soure."
				errorMsgDict['showAlertText'] = errorMsgDict['source']
				return (False, valuesDict, errorMsgDict)
				
			if device.deviceTypeId == "vsx1021k":
				if theSource in vsx1021kZone2SourceMask:
					errorMsgDict['source'] = u"The selected source is not available for this zone on this receiver. Choose a different source."
					errorMsgDict['showAlertText'] = errorMsgDict['source']
					return (False, valuesDict, errorMsgDict)
			elif device.deviceTypeId == "vsx1022k":
				if theSource in vsx1022kZone2SourceMask:
					errorMsgDict['source'] = u"The selected source is not available for this zone on this receiver. Choose a different source."
					errorMsgDict['showAlertText'] = errorMsgDict['source']
					return (False, valuesDict, errorMsgDict)
			elif device.deviceTypeId == "vsx1122k":
				if theSource in vsx1122kZone2SourceMask:
					errorMsgDict['source'] = u"The selected source is not available for this zone on this receiver. Choose a different source."
					errorMsgDict['showAlertText'] = errorMsgDict['source']
					return (False, valuesDict, errorMsgDict)
			elif device.deviceTypeId == "vsx1123k":
				if theSource in vsx1123kZone2SourceMask:
					errorMsgDict['source'] = u"The selected source is not available for this zone on this receiver. Choose a different source."
					errorMsgDict['showAlertText'] = errorMsgDict['source']
					return (False, valuesDict, errorMsgDict)
			elif device.deviceTypeId == "sc75":
				if theSource in sc75Zone2SourceMask:
					errorMsgDict['source'] = u"The selected source is not available for this zone on this receiver. Choose a different source."
					errorMsgDict['showAlertText'] = errorMsgDict['source']
					return (False, valuesDict, errorMsgDict)
			
			descString += u"set input source (zone 2) to " + str(theName)
		
		#
		# Select Tuner Preset
		#
		if typeId == "tunerPresetSelect":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['tunerPreset'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['tunerPreset']
				return (False, valuesDict, errorMsgDict)
			
			thePreset = valuesDict['tunerPreset']
			propName = "tunerPreset" + thePreset.replace("0","") + "label"
			theName = device.pluginProps.get(propName, "")
			if len(theName) < 1:
				errorMsgDict['tunerPreset'] = u"Please select a Tuner Preset."
				errorMsgDict['showAlertText'] = errorMsgDict['tunerPreset']
				return (False, valuesDict, errorMsgDict)
			
			descString += u"select tuner preset " + thePreset.replace("0", "") + u": " + theName
		
		#
		# Set Tuner Frequency
		#
		if typeId == "tunerFrequencySet":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['band'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['frequency'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['band']
				return (False, valuesDict, errorMsgDict)
			
			# Make sure a tuner band was selected.
			band = valuesDict.get('band', "")
			if len(band) < 2:
				errorMsgDict['band'] = u"Please select a Tuner Band."
			
			# Make sure a frequency value was entered.
			frequency = valuesDict.get('frequency', "")
			if len(frequency) == 0:
				errorMsgDict['frequency'] = u"A Tuner Frequency value is required."
			else:
				# A tuner frequency was entered, now make sure it's realistic.
				try:
					frequency = float(valuesDict['frequency'])
					# Make sure the frequency is a sane value based on band.
					if band == "AM":
						if (frequency < 530) or (frequency > 1700):
							errorMsgDict['frequency'] = u"AM frequencies must be a whole number between 530 and 1700 in increments of 10 kHz."
						if frequency%10 != 0:
							errorMsgDict['frequency'] = u"AM frequencies must be a whole number between 530 and 1700 in increments of 10 kHz."
						# Convert the frequency to an integer.
						frequency = int(frequency)
					elif band == "FM":
						if (frequency < 87.5) or (frequency > 108):
							errorMsgDict['frequency'] = u"FM frequencies must be between 87.5 and 108 in increments of 0.1 MHz."
						if int(frequency*10) != frequency*10:	# Makes sure the number contains at most 0.1 precission.
							errorMsgDict['frequency'] = u"FM frequencies must be between 87.5 and 108 in increments of 0.1 MHz."
				except ValueError:
					errorMsgDict['frequency'] = u"The Tuner Frequency field can only contain numbers."
			
			# If there were errors, return them now.
			if len(errorMsgDict) > 0:
				errorMsgDict['showAlertText'] = errorMsgDict['band'] + "\r\r" + errorMsgDict['frequency']
				return (False, valuesDict, errorMsgDict)
			
			descString += u"set tuner frequency to " + str(frequency) + " " + band
		
		#
		# Select Listening Mode
		#
		if typeId == "listeningModeSelect":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['listeningMode'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['listeningMode']
				return (False, valuesDict, errorMsgDict)
			
			listeningMode = valuesDict.get('listeningMode', "")
			if len(listeningMode) < 1:
				errorMsgDict['listeningMode'] = u"Please select a Listening Mode."
				errorMsgDict['showAlertText'] = errorMsgDict['listeningMode']
				return (False, valuesDict, errorMsgDict)
			else:
				descString += u"set listening mode to \"" + listeningModes[listeningMode] + "\""
		
		#
		# Set Display Brightness
		#
		if typeId == "setDisplayBrightness":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['displayBrightness'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['displayBrightness']
				return (False, valuesDict, errorMsgDict)
			
			displayBrightness = valuesDict.get('displayBrightness', "")
			if len(displayBrightness) < 1:
				errorMsgDict['displayBrightness'] = u"Please select a value for Display Brightness."
				errorMsgDict['showAlertText'] = errorMsgDict['displayBrightness']
				return (False, valuesDict, errorMsgDict)
			else:
				descString += u"set display brightness to "
				# Translate the displayBrightness value into something readable for the description.
				if displayBrightness == "3SAA":
					descString = u"turn off display"
				elif displayBrightness == "2SAA":
					descString += u"dim"
				elif displayBrightness == "1SAA":
					descString += u"medium"
				elif displayBrightness == "0SAA":
					descString += u"bright"
		
		#
		# Set Sleep Timer
		#
		if typeId == "setSleepTimer":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['sleepTime'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['sleepTime']
				return (False, valuesDict, errorMsgDict)
			
			sleepTime = valuesDict.get('sleepTime', "")
			if len(sleepTime) < 1:
				errorMsgDict['sleepTime'] = u"Please select a value for Sleep Time Minutes."
				errorMsgDict['showAlertText'] = errorMsgDict['sleepTime']
				return (False, valuesDict, errorMsgDict)
			else:
				descString += u"set sleep timer to "
				# Translate the sleepTime value into something readable for the description.
				sleepTime = int(sleepTime[1:3])
				if sleepTime == 0:
					descString += u"off"
				else:
					descString += unicode(sleepTime) + u" min"
		
		#
		# Select MCACC Memory
		#
		if typeId == "mcaccSelect":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['mcaccMemory'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['mcaccMemory']
				return (False, valuesDict, errorMsgDict)
			
			# Make sure a MCACC memory was selected.
			mcaccMemory = valuesDict.get('mcaccMemory', "")
			if len(mcaccMemory) < 1:
				errorMsgDict['mcaccMemory'] = u"Please select a MCACC Memory item."
				errorMsgDict['showAlertText'] = errorMsgDict['mcaccMemory']
				return (False, valuesDict, errorMsgDict)
			else:
				devProps = device.pluginProps
				propName = 'mcaccMemory' + mcaccMemory[0:1] + 'label'
				mcaccMemoryName = devProps[propName]
				descString += u"set mcacc memeory to " + mcaccMemory[0:1] + ": " + mcaccMemoryName
		
		#
		# Send Remote Button Press
		#
		if typeId == "remoteButtonPress":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['remoteButton'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['remoteButton']
				return (False, valuesDict, errorMsgDict)
			
			command = valuesDict.get('remoteButton', "")
			# Make sure they selected a button to send.
			if len(command) == 0:
				errorMsgDict['remoteButton'] = u"Please select a Button press to send to the receiver."
				errorMsgDict['showAlertText'] = errorMsgDict['remoteButton']
				return (False, valuesDict, errorMsgDict)
			
			descString += u"press remote control button \"" + remoteButtonNames.get(command, "") + u"\""

		#
		# Send a Raw Command
		#
		if typeId == "sendRawCommand":
			# Catch attempts to send a command to a Virtual Volume Controller device,
			#   which is not possible (but because it's not currently possible to prevent
			#   the user from selecting it as a destination device in the Indigo UI, we
			#   must check for it).
			if device.deviceTypeId == "virtualVolume":
				errorMsgDict['command'] = u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device."
				errorMsgDict['showAlertText'] = errorMsgDict['command']
				return (False, valuesDict, errorMsgDict)
			
			command = valuesDict['command']
			# Attempt to encode the command as ASCII.  If this fails.
			try:
				command = command.encode("ascii")
			except UnicodeEncodeError:
				errorMsgDict['command'] = u"Commands can only contain standard ASCII characters. Extended characters are not supported."
				errorMsgDict['showAlertText'] = errorMsgDict['command']
				return (False, valuesDict, errorMsgDict)
			# Make sure the command isn't blank.
			if len(command) == 0:
				errorMsgDict['command'] = u"Nothing was entered for the Command. Please enter a text command to send to the receiver."
				errorMsgDict['showAlertText'] = errorMsgDict['command']
				return (False, valuesDict, errorMsgDict)
			
			descString += u"send raw command \"" + command + "\""
		
		valuesDict['description'] = descString
		return (True, valuesDict)
	
	# Device Configuration Dialog
	########################################
	def validateDeviceConfigUi(self, valuesDict, typeId=0, deviceId=0):
		try:
			self.debugLog("validateDeviceConfig called. valuesDict: " + str(valuesDict) + " typeId: " + str(typeId) + ", deviceId: " + str(deviceId) + ".")
		except Exception, e:
			self.debugLog("validateDeviceConfig called. typeId: " + str(typeId) + " deviceId: " + str(deviceId) + " (Unable to display valuesDict due to error: " + str(e) + ")")
		
		error = False		# To flag if any errors were found.
		errorMsgDict = indigo.Dict()
		
		#
		# VSX-1021-K Device
		#
		if typeId == "vsx1021k":
			address = valuesDict.get('address', "")
			
			# Make sure a value was entered for the address.
			if len(address) < 1:
				errorMsgDict['address'] = u"Please enter an IP address for the receiver."
				errorMsgDict['showAlertText'] = errorMsgDict['address']
				return (False, valuesDict, errorMsgDict)
			
			# Make sure the address entered is in the correct IP address format.
			addressParts = address.split(".")
			# (This is easier than using Regular Expressions.  :-) )
			for part in addressParts:
				try:
					part = int(part)
					if part < 0 or part > 255:
						errorMsgDict['address'] = u"Please enter a valid IP address for the receiver."
						errorMsgDict['showAlertText'] = errorMsgDict['address']
						return (False, valuesDict, errorMsgDict)
				except ValueError:
					errorMsgDict['address'] = u"Please enter a valid IP address for the receiver."
					errorMsgDict['showAlertText'] = errorMsgDict['address']
					return (False, valuesDict, errorMsgDict)
			
			# For newly created devices, the deviceId won't be in the device list.
			if deviceId > 0:
				device = indigo.devices[deviceId]
				devProps = device.pluginProps
				
				# See if any other devices are using the same address by going through all devices for this plugin.
				for d in self.deviceList:
					a = indigo.devices[d].pluginProps['address']
					# If the address found is the same as this device's address
					#   (and the matching address is not for this device), generate an error.
					if (a == address) and (d != deviceId):
						error = True
						errorMsgDict['address'] = u"This address is already being used by the device \"" + indigo.devices[d].name + "\". Only one device at a time can connect to a receiver."
						errorMsgDict['showAlertText'] = errorMsgDict['address']
						
				# Make sure the MCACC Memory Label properties are created, even if they aren't specified.
				for mcmccMemory in range(1,7):
					propName = 'mcmccMemory' + str(mcmccMemory) + 'label'
					if valuesDict.get(propName, "") == "":
						devProps.update({propName:""})
						self.updateDeviceProps(device, devProps)
		
		#
		# VSX-1022-K Device
		#
		if typeId == "vsx1022k":
			address = valuesDict.get('address', "")
			
			# Make sure a value was entered for the address.
			if len(address) < 1:
				errorMsgDict['address'] = u"Please enter an IP address for the receiver."
				errorMsgDict['showAlertText'] = errorMsgDict['address']
				return (False, valuesDict, errorMsgDict)
			
			# Make sure the address entered is in the correct IP address format.
			addressParts = address.split(".")
			# (This is easier than using Regular Expressions.  :-) )
			for part in addressParts:
				try:
					part = int(part)
					if part < 0 or part > 255:
						errorMsgDict['address'] = u"Please enter a valid IP address for the receiver."
						errorMsgDict['showAlertText'] = errorMsgDict['address']
						return (False, valuesDict, errorMsgDict)
				except ValueError:
					errorMsgDict['address'] = u"Please enter a valid IP address for the receiver."
					errorMsgDict['showAlertText'] = errorMsgDict['address']
					return (False, valuesDict, errorMsgDict)
			
			# For newly created devices, the deviceId won't be in the device list.
			if deviceId > 0:
				device = indigo.devices[deviceId]
				devProps = device.pluginProps
				
				# See if any other devices are using the same address by going through all devices for this plugin.
				for d in self.deviceList:
					a = indigo.devices[d].pluginProps['address']
					# If the address found is the same as this device's address
					#   (and the matching address is not for this device), generate an error.
					if (a == address) and (d != deviceId):
						error = True
						errorMsgDict['address'] = u"This address is already being used by the device \"" + indigo.devices[d].name + "\". Only one device at a time can connect to a receiver."
						errorMsgDict['showAlertText'] = errorMsgDict['address']
						
				# Make sure the MCACC Memory Label properties are created, even if they aren't specified.
				for mcmccMemory in range(1,7):
					propName = 'mcmccMemory' + str(mcmccMemory) + 'label'
					if valuesDict.get(propName, "") == "":
						devProps.update({propName:""})
						self.updateDeviceProps(device, devProps)
		
		#
		# VSX-1122-K Device
		#
		if typeId == "vsx1122k":
			address = valuesDict.get('address', "")
			
			# Make sure a value was entered for the address.
			if len(address) < 1:
				errorMsgDict['address'] = u"Please enter an IP address for the receiver."
				errorMsgDict['showAlertText'] = errorMsgDict['address']
				return (False, valuesDict, errorMsgDict)
			
			# Make sure the address entered is in the correct IP address format.
			addressParts = address.split(".")
			# (This is easier than using Regular Expressions.  :-) )
			for part in addressParts:
				try:
					part = int(part)
					if part < 0 or part > 255:
						errorMsgDict['address'] = u"Please enter a valid IP address for the receiver."
						errorMsgDict['showAlertText'] = errorMsgDict['address']
						return (False, valuesDict, errorMsgDict)
				except ValueError:
					errorMsgDict['address'] = u"Please enter a valid IP address for the receiver."
					errorMsgDict['showAlertText'] = errorMsgDict['address']
					return (False, valuesDict, errorMsgDict)
			
			# For newly created devices, the deviceId won't be in the device list.
			if deviceId > 0:
				device = indigo.devices[deviceId]
				devProps = device.pluginProps
				
				# See if any other devices are using the same address by going through all devices for this plugin.
				for d in self.deviceList:
					a = indigo.devices[d].pluginProps['address']
					# If the address found is the same as this device's address
					#   (and the matching address is not for this device), generate an error.
					if (a == address) and (d != deviceId):
						error = True
						errorMsgDict['address'] = u"This address is already being used by the device \"" + indigo.devices[d].name + "\". Only one device at a time can connect to a receiver."
						errorMsgDict['showAlertText'] = errorMsgDict['address']
						
				# Make sure the MCACC Memory Label properties are created, even if they aren't specified.
				for mcmccMemory in range(1,7):
					propName = 'mcmccMemory' + str(mcmccMemory) + 'label'
					if valuesDict.get(propName, "") == "":
						devProps.update({propName:""})
						self.updateDeviceProps(device, devProps)
		
		#
		# VSX-1123-K Device
		#
		if typeId == "vsx1123k":
			address = valuesDict.get('address', "")
			
			# Make sure a value was entered for the address.
			if len(address) < 1:
				errorMsgDict['address'] = u"Please enter an IP address for the receiver."
				errorMsgDict['showAlertText'] = errorMsgDict['address']
				return (False, valuesDict, errorMsgDict)
			
			# Make sure the address entered is in the correct IP address format.
			addressParts = address.split(".")
			# (This is easier than using Regular Expressions.  :-) )
			for part in addressParts:
				try:
					part = int(part)
					if part < 0 or part > 255:
						errorMsgDict['address'] = u"Please enter a valid IP address for the receiver."
						errorMsgDict['showAlertText'] = errorMsgDict['address']
						return (False, valuesDict, errorMsgDict)
				except ValueError:
					errorMsgDict['address'] = u"Please enter a valid IP address for the receiver."
					errorMsgDict['showAlertText'] = errorMsgDict['address']
					return (False, valuesDict, errorMsgDict)
			
			# For newly created devices, the deviceId won't be in the device list.
			if deviceId > 0:
				device = indigo.devices[deviceId]
				devProps = device.pluginProps
				
				# See if any other devices are using the same address by going through all devices for this plugin.
				for d in self.deviceList:
					a = indigo.devices[d].pluginProps['address']
					# If the address found is the same as this device's address
					#   (and the matching address is not for this device), generate an error.
					if (a == address) and (d != deviceId):
						error = True
						errorMsgDict['address'] = u"This address is already being used by the device \"" + indigo.devices[d].name + "\". Only one device at a time can connect to a receiver."
						errorMsgDict['showAlertText'] = errorMsgDict['address']
						
				# Make sure the MCACC Memory Label properties are created, even if they aren't specified.
				for mcmccMemory in range(1,7):
					propName = 'mcmccMemory' + str(mcmccMemory) + 'label'
					if valuesDict.get(propName, "") == "":
						devProps.update({propName:""})
						self.updateDeviceProps(device, devProps)
						
		#
		# SC-75 Device
		#
		if typeId == "sc75":
			address = valuesDict.get('address', "")
			
			# Make sure a value was entered for the address.
			if len(address) < 1:
				errorMsgDict['address'] = u"Please enter an IP address for the receiver."
				errorMsgDict['showAlertText'] = errorMsgDict['address']
				return (False, valuesDict, errorMsgDict)
			
			# Make sure the address entered is in the correct IP address format.
			addressParts = address.split(".")
			# (This is easier than using Regular Expressions.  :-) )
			for part in addressParts:
				try:
					part = int(part)
					if part < 0 or part > 255:
						errorMsgDict['address'] = u"Please enter a valid IP address for the receiver."
						errorMsgDict['showAlertText'] = errorMsgDict['address']
						return (False, valuesDict, errorMsgDict)
				except ValueError:
					errorMsgDict['address'] = u"Please enter a valid IP address for the receiver."
					errorMsgDict['showAlertText'] = errorMsgDict['address']
					return (False, valuesDict, errorMsgDict)
			
			# For newly created devices, the deviceId won't be in the device list.
			if deviceId > 0:
				device = indigo.devices[deviceId]
				devProps = device.pluginProps
				
				# See if any other devices are using the same address by going through all devices for this plugin.
				for d in self.deviceList:
					a = indigo.devices[d].pluginProps['address']
					# If the address found is the same as this device's address
					#   (and the matching address is not for this device), generate an error.
					if (a == address) and (d != deviceId):
						error = True
						errorMsgDict['address'] = u"This address is already being used by the device \"" + indigo.devices[d].name + "\". Only one device at a time can connect to a receiver."
						errorMsgDict['showAlertText'] = errorMsgDict['address']
						
				# Make sure the MCACC Memory Label properties are created, even if they aren't specified.
				for mcmccMemory in range(1,7):
					propName = 'mcmccMemory' + str(mcmccMemory) + 'label'
					if valuesDict.get(propName, "") == "":
						devProps.update({propName:""})
						self.updateDeviceProps(device, devProps)
		
		#
		# Virtual Level Control Device
		#
		elif typeId == "virtualVolume":
			receiverDeviceId = valuesDict.get('receiverDeviceId', 0)
			controlDestination = valuesDict.get('controlDestination', "")
			if len(receiverDeviceId) < 1:
				errorMsgDict['receiverDeviceId'] = u"Please select a Pioneer Receiver device."
				errorMsgDict['showAlertText'] = errorMsgDict['receiverDeviceId']
				error = True
			elif int(receiverDeviceId) in self.volumeDeviceList:
				errorMsgDict['receiverDeviceId'] = u"The selected device is another Virtual Volume Controller. Only receiver devices can be controlled with this Virtual Volume Controller."
				errorMsgDict['showAlertText'] = errorMsgDict['receiverDeviceId']
				error = True
			elif int(receiverDeviceId) not in self.deviceList:
				errorMsgDict['receiverDeviceId'] = u"The selected device no longer exists. Please click Cancel then click on Edit Device Settings again."
				errorMsgDict['showAlertText'] = errorMsgDict['receiverDeviceId']
				error = True
			if len(controlDestination) < 1:
				errorMsgDict['controlDestination'] = u"Please select a Control Destination."
				errorMsgDict['showAlertText'] = errorMsgDict['controlDestination']
				error = True
		
		# Return errors if there were any.
		if error:
			return (False, valuesDict, errorMsgDict)
		
		return (True, valuesDict)
	
	# Plugin Configuration Dialog
	########################################
	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		self.debugLog("closedPrefsConfigUi called.")
		
		if not userCancelled:
			self.debug = valuesDict.get("showDebugInfo", False)
			if self.debug:
				indigo.server.log("Debug logging enabled")
			else:
				indigo.server.log("Debug logging disabled")
	
	
	########################################
	# UI Interaction Methods
	#   (Custom)
	########################################
	
	# Get Source List for Use in UI.
	########################################
	def uiSourceList(self, filter="", valuesDict=None, typeId="", deviceId=0):
		self.debugLog("uiSourceList called. typeId: " + str(typeId) + ", targetId: " + str(deviceId))
		
		theList = list()	# Menu item list.
		device = indigo.devices[deviceId]	# The device whose action is being configured.
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return []
		
		# Go through the defined sources to decide which to add to the list.
		for thisNumber, thisName in sourceNames.items():
			# Create the list based on which zone for which this is being compiled.
			if typeId == "zone1setSource":
				# If this source ID is not masked (i.e. is available) on this model, add it.
				if device.deviceTypeId == "vsx1021k":
					if thisNumber not in vsx1021kSourceMask:
						propName = "source" + str(thisNumber) + "label"
						thisName = device.pluginProps[propName]
						theList.append((thisNumber, thisName))
				elif device.deviceTypeId == "vsx1022k":
					if thisNumber not in vsx1022kSourceMask and thisNumber not in ['46', '47']:
						# Source 46 (AirPlay) and 47 (DMR) are not selectable, but
						#   are valid sources, so they're not in the mask array.
						propName = "source" + str(thisNumber) + "label"
						thisName = device.pluginProps[propName]
						theList.append((thisNumber, thisName))
				elif device.deviceTypeId == "vsx1122k":
					if thisNumber not in vsx1122kSourceMask:
						propName = "source" + str(thisNumber) + "label"
						thisName = device.pluginProps[propName]
						theList.append((thisNumber, thisName))
				elif device.deviceTypeId == "vsx1123k":
					if thisNumber not in vsx1123kSourceMask:
						propName = "source" + str(thisNumber) + "label"
						thisName = device.pluginProps[propName]
						theList.append((thisNumber, thisName))
				elif device.deviceTypeId == "sc75":
					if thisNumber not in sc75SourceMask:
						propName = "source" + str(thisNumber) + "label"
						thisName = device.pluginProps[propName]
						theList.append((thisNumber, thisName))
			elif typeId == "zone2setSource":
				# If this source ID is not masked (i.e. is available) on this model, add it.
				if device.deviceTypeId == "vsx1021k":
					if thisNumber not in vsx1021kZone2SourceMask:
						propName = "source" + str(thisNumber) + "label"
						thisName = device.pluginProps[propName]
						theList.append((thisNumber, thisName))
				elif device.deviceTypeId == "vsx1022k":
					if thisNumber not in vsx1022kZone2SourceMask and thisNumber not in ['46', '47']:
						# Source 46 (AirPlay) and 47 (DMR) are not selectable, but
						#   are valid sources, so they're not in the mask array.
						propName = "source" + str(thisNumber) + "label"
						thisName = device.pluginProps[propName]
						theList.append((thisNumber, thisName))
				elif device.deviceTypeId == "vsx1122k":
					if thisNumber not in vsx1122kZone2SourceMask:
						propName = "source" + str(thisNumber) + "label"
						thisName = device.pluginProps[propName]
						theList.append((thisNumber, thisName))
				elif device.deviceTypeId == "vsx1123k":
					if thisNumber not in vsx1123kZone2SourceMask:
						propName = "source" + str(thisNumber) + "label"
						thisName = device.pluginProps[propName]
						theList.append((thisNumber, thisName))
				elif device.deviceTypeId == "sc75":
					if thisNumber not in sc75Zone2SourceMask:
						propName = "source" + str(thisNumber) + "label"
						thisName = device.pluginProps[propName]
						theList.append((thisNumber, thisName))
		
		return theList
	
	# Get Tuner Preset List for Use in UI.
	########################################
	def uiTunerPresetList(self, filter="", valuesDict=None, typeId="", deviceId=0):
		self.debugLog("uiTunerPresetList called. typeId: " + str(typeId) + ", targetId: " + str(deviceId))
		
		theList = list()	# Menu item list.
		device = indigo.devices[deviceId]	# The device whose action is being configured.
		propName = ""		# Device property name to be queried.
		presetName = ""		# Tuner Preset name to be listed.
		presetNumber = ""	# Tuner Preset number to be returned in the list selection.
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return []
		
		# Define the tuner preset "classes" (groups).
		presetClasses = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
		# Go through the preset classes and numbers 1 through 9 to get the preset names.
		for theClass in presetClasses:
			for thePreset in range(1,9):
				propName = 'tunerPreset' + theClass + str(thePreset) + 'label'
				presetName = theClass + str(thePreset) + ": " + device.pluginProps[propName]
				presetNumber = theClass + "0" + str(thePreset)
				theList.append((presetNumber, presetName))
		
		return theList
	
	# Get MCACC Label List for Use in UI.
	########################################
	def uiMcaccLabelList(self, filter="", valuesDict=None, typeId="", deviceId=0):
		self.debugLog("uiMcaccLabelList called. typeId: " + str(typeId) + ", targetId: " + str(deviceId))
		
		theList = list()		# Menu item list.
		device = indigo.devices[deviceId]	# The device whose action is being configured.
		propName = ""			# Device property name to be queried.
		mcaccMemoryName = ""	# MCACC Memory lable (name) to be listed.
		mcaccMemory = ""		# MCACC Memory number to be returned in the list selection.
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return []
		
		# Go through the MCACC memory numbers 1 through 6 to get the labels/names.
		for mcaccMemory in range(1,7):
			propName = 'mcaccMemory' + str(mcaccMemory) + 'label'
			mcaccMemoryName = str(mcaccMemory) + ": " + device.pluginProps[propName]
			# Conver the mcaccMemory number into a command.
			mcaccMemory = str(mcaccMemory) + "MC"
			theList.append((mcaccMemory, mcaccMemoryName))
		
		return theList
	
	# Get Remote Control Button Names
	########################################
	def uiButtonNames(self, filter="", valuesDict=None, typeId="", deviceId=0):
		self.debugLog("uiButtonNames called. typeId: " + str(typeId) + ", targetId: " + str(deviceId))
		
		theList = list()	# Menu item list.
		device = indigo.devices[deviceId]	# The device whose action is being configured.
		command    = ""		# The button press command.
		buttonName = ""		# The name of the button to list in the menu.
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return []
		
		# Go through the remoteButtonNames dictionary items to create the list.
		for command in remoteButtonNamesOrder:
			buttonName = remoteButtonNames.get(command, "")
			theList.append((command, buttonName))
		
		return theList
	
	# Get List of Listening Modes.
	########################################
	def uiListeningModeList(self, filter="", valuesDict=None, typeId="", deviceId=0):
		self.debugLog("uiListeningModeList called. typeId: " + str(typeId) + ", targetId: " + str(deviceId))
		
		theList = list()	# Menu item list.
		theNumber = ""		# The listening mode ID number
		theName = ""		# The listening mode name.
		device = indigo.devices[deviceId]	# The device whose action is being configured.
		
		# Catch attempts to send a command to a Virtual Volume Controller device,
		#   which is not possible (but because it's not currently possible to prevent
		#   the user from selecting it as a destination device in the Indigo UI, we
		#   must check for it).
		if device.deviceTypeId == "virtualVolume":
			self.errorLog(u"Device \"" + device.name + "\" is a Virtual Volume Controller, not a Pioneer receiver. Modify the Indigo action to send the command to a Pioneer receiver instead of this device.")
			return []
		
		# Create a list of listeningModes keys sorted by listeningModes values.
		items = listeningModes.items()
		reverseItems = [ [v[1],v[0]] for v in items]
		reverseItems.sort()
		sortedlist = [ reverseItems[i][1] for i in range(0,len(reverseItems))]
		
		for theNumber in sortedlist:
			theName = listeningModes[theNumber]
			# Show only items related to the device type passed in
			#   the "filter" variable.
			if filter == "vsx1021k":
				if theNumber not in vsx1021kListeningModeMask:
					# Don't list modes with "(cyclic)" in the name.
					if "(cyclic)" not in theName:
						theList.append((theNumber, theName))
			elif filter == "vsx1022k":
				if theNumber not in vsx1022kListeningModeMask:
					# Don't list modes with "(cyclic)" in the name.
					if "(cyclic)" not in theName:
						theList.append((theNumber, theName))
			elif filter == "vsx1122k":
				if theNumber not in vsx1122kListeningModeMask:
					# Don't list modes with "(cyclic)" in the name.
					if "(cyclic)" not in theName:
						theList.append((theNumber, theName))
			elif filter == "vsx1123k":
				if theNumber not in vsx1123kListeningModeMask:
					# Don't list modes with "(cyclic)" in the name.
					if "(cyclic)" not in theName:
						theList.append((theNumber, theName))
			elif filter == "sc75":
				if theNumber not in sc75ListeningModeMask:
					# Don't list modes with "(cyclic)" in the name.
					if "(cyclic)" not in theName:
						theList.append((theNumber, theName))
		
		return theList
	
	# Get List of Pioneer Receiver Devices.
	########################################
	# (This method is deprecated as of 0.9.6, but kept for possible future referecnce.
	def uiReceiverDevices(self, filter="", valuesDict=None, typeId="", targetId=0):
		self.debugLog("uiReceiverDevices called. typeId: " + str(typeId) + ", targetId: " + str(targetId))
		
		theList = list()	# Menu item list.
		deviceId = ""		# The device ID of the Poineer Receiver listed.
		deviceName = ""		# The name of the Poneer Receiver device listed.
		
		# Go through the deviceList and list the devices.
		for deviceId in self.deviceList:
			deviceName = indigo.devices[deviceId].name
			theList.append((deviceId, deviceName))
		
		return theList

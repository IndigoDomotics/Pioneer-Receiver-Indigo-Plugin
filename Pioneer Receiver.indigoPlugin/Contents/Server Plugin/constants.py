"""
Repository of application constants

The constants.py file contains all application constants and is imported as a library. References are denoted as
constants by the use of all caps.
"""


def __init__():
    pass


# Special display character number mapping dictionary.
CHARACTER_MAP = {0: "", 1: "rpt+shfl ", 2: "rpt ", 3: "shfl ", 4: "◊ ", 5: "[)", 6: "(]", 7: "I", 8: "II", 9: "<",
                 10: ">", 11: "\\^^/", 12: ".", 13: ".0", 14: ".5", 15: "Ω", 16: "0", 17: "1", 18: "2", 19: "3",
                 20: "4", 21: "5", 22: "6", 23: "7", 24: "8", 25: "9", 26: "A", 27: "B", 28: "C", 29: "F", 30: "M",
                 31: "¯", 127: "◊", 128: "Œ", 129: "œ", 130: "IJ", 131: "ij", 132: "π", 133: "±", 134: "", 135: "",
                 136: "", 137: "", 138: "", 139: "", 140: "<-", 141: "^", 142: "->", 143: "v", 144: "+", 145: "√",
                 146: "ƒ", 147: "", 148: "", 149: "", 150: "", 151: "", 152: "", 153: "", 154: "", 155: "", 156: "",
                 157: "", 158: "", 159: "", 160: "", 161: "¡", 162: "¢", 163: "£", 164: "Ø", 165: "¥", 166: "|",
                 167: "§", 168: "¨", 169: "©", 170: "a", 171: "«", 172: "¬", 173: "-", 174: "®", 175: "¯", 176: "°",
                 177: "±", 178: "2", 179: "3", 180: "’", 181: "µ", 182: "¶", 183: "·", 184: "‚", 185: "1", 186: "0",
                 187: "»", 188: "1/4", 189: "1/2", 190: "3/4", 191: "¿", 192: "À", 193: "Á", 194: "Â", 195: "Ã",
                 196: "Ä", 197: "Å", 198: "Æ", 199: "Ç", 200: "È", 201: "É", 202: "Ê", 203: "Ë", 204: "Ì", 205: "Í",
                 206: "Î", 207: "Ï", 208: "D", 209: "Ñ", 210: "Ò", 211: "Ó", 212: "Ô", 213: "Õ", 214: "Ö", 215: "x",
                 216: "Ø", 217: "Ù", 218: "Ú", 219: "Û", 220: "Ü", 221: "Y", 222: "p", 223: "ß", 224: "à", 225: "á",
                 226: "â", 227: "ã", 228: "ä", 229: "å", 230: "æ", 231: "ç", 232: "è", 233: "é", 234: "ê", 235: "ë",
                 236: "ì", 237: "í", 238: "î", 239: "ï", 240: "∂", 241: "ñ", 242: "ò", 243: "ó", 244: "ô", 245: "õ",
                 246: "ö", 247: "÷", 248: "ø", 249: "ù", 250: "ú", 251: "û", 252: "ü", 253: "y", 254: "p", 255: "ÿ"}

# Channel volume receiver responses to device states map.
CHANNEL_VOLUMES = {"L__": 'channelVolumeL', "R__": 'channelVolumeR', "C__": 'channelVolumeC', "SL_": 'channelVolumeSL',
                  "SR_": 'channelVolumeSR', "SBL": 'channelVolumeSBL', "SBR": 'channelVolumeSBR',
                  "SW_": 'channelVolumeSW', "LH_": 'channelVolumeLH', "RH_": 'channelVolumeRH',
                  "LW_": 'channelVolumeLW', "RW_": 'channelVolumeRW'}

# Input source IDs to default names map.
SOURCE_NAMES = {'00': "PHONO", '01': "CD", '02': "TUNER", '03': "CD-R/TAPE", '04': "DVD", '05': "TV", '06': "SAT/CBL",
               '10': "VIDEO 1 (VIDEO)", '12': "MULTI CH IN", '13': "USB-DAC", '14': "VIDEO 2", '15': "DVR/BDR",
               '17': "iPod/USB", '19': "HDMI 1", '20': "HDMI 2", '21': "HDMI 3", '22': "HDMI 4", '23': "HDMI 5",
               '24': "HDMI 6", '25': "BD", '26': "NETWORK", '27': "SIRIUS", '31': "HDMI (cyclic)", '33': "ADAPTER PORT",
               '34': "HDMI 7", '35': "HDMI 8", '38': "INTERNET RADIO", '40': "SiriusXM", '41': "PANDORA",
               '44': "MEDIA SERVER", '45': "FAVORITES", '46': "AirPlay", '47': "DMR", '48': "MHL"}

# VSX-1021-K source mask.
VSX1021k_SOURCE_MASK = ['00', '06', '12', '13', '20', '21', '22', '23', '24', '31', '34', '35', '38', '40', '41', '44',
                        '45', '46', '47', '48']

# VSX-1021-K zone 2 source mask.
VSX1021K_ZONE2_SOURCE_MASK = ['00', '06', '12', '13', '19', '20', '21', '22', '23', '24', '25', '31', '34', '35', '38',
                              '40', '41', '44', '45', '46', '47', '48']

# VSX-1022-K source mask.
VSX1022K_SOURCE_MASK = ['00', '03', '12', '13', '14', '19', '20', '21', '22', '23', '24', '26', '27', '31', '34', '35',
                        '40', '48']

# VSX-1022-K zone 2 source mask.
VSX1022K_ZONE2_SOURCE_MASK = ['00', '03', '12', '13', '14', '19', '20', '21', '22', '23', '24', '25', '26', '27', '31',
                              '34', '35', '40', '48']

# VSX-1122-K source mask.
VSX1122K_SOURCE_MASK = ['03', '10', '12', '13', '14', '26', '27', '31', '34', '35', '46', '47', '48']

# VSX-1122-K zone 2 source mask.
VSX1122K_ZONE2_SOURCE_MASK = ['03', '10', '12', '13', '14', '19', '25', '26', '27', '31', '34', '35', '46', '47', '48']

# VSX-1123-K source mask.
VSX1123K_SOURCE_MASK = ['03', '10', '12', '13', '14', '26', '27', '31', '35', '46', '47', '48']

# VSX-1123-K zone 2 source mask.
VSX1123k_ZONE2_SOURCE_MASK = ['03', '10', '12', '13', '14', '19', '25', '26', '27', '31', '35', '46', '47', '48']

# SC-75 source mask.
SC75_SOURCE_MASK = ['00', '03', '12', '13', '14', '27', '46', '47']

# SC-75 zone 2 source mask.
SC75_ZONE2_SOURCE_MASK = ['00', '03', '12', '13', '14', '27', '46', '47']

# Listening Mode IDs to names map.
LISTENING_MODES = {'0001': "Stereo (cyclic)", '0003': "Front Stage Surround Advance Focus",
                   '0004': "Front Stage Surround Advance Wide", '0005': "Auto Surround/Stream Direct (cyclic)",
                   '0006': "Auto Surround", '0007': "Direct", '0008': "Pure Direct", '0009': "Stereo",
                   '0010': "Standard (cyclic)", '0011': "2-ch Source", '0012': "Dolby Pro Logic",
                   '0013': "Dolby Pro Logic II Movie", '0014': "Dolby Pro Logic II Music",
                   '0015': "Dolby Pro Logic II Game", '0016': "DTS Neo:6 Cinema", '0017': "DTS Neo:6 Music",
                   '0018': "Dolby Pro Logic IIx Movie", '0019': "Dolby Pro Logic IIx Music",
                   '0020': "Dolby Pro Logic IIx Game", '0021': "Multi-ch Source", '0022': "Dolby EX (Multi-ch Source)",
                   '0023': "Dolby Pro Logic IIx Movie (Multi-ch Source)",
                   '0024': "Dolby Pro Logic IIx Music (Multi-ch Source)", '0025': "DTS-ES Neo:6 (Multi-ch Source)",
                   '0026': "DTS-ES Matrix (Multi-ch Source)", '0027': "DTS-ES Discrete (Multi-ch Source)",
                   '0028': "XM HD Surround", '0029': "Neural Surround", '0030': "DTS-ES 8-ch Discrete (Multi-ch Source)",
                   '0031': "Dolby Pro Logic IIz Height", '0032': "Wide Surround Movie", '0033': "Wide Surround Music",
                   '0034': "Dolby Pro Logic IIz Height (Multi-ch Source)",
                   '0035': "Wide Surround Movie (Multi-ch Source)", '0036': "Wide Surround Music (Multi-ch Source)",
                   '0037': "DTS Neo:X Cinema", '0038': "DTS Neo:X Music", '0039': "DTS Neo:X Game",
                   '0040': "Neural Surround + DTS Neo:X Cinema", '0041': "Neural Surround + DTS Neo:X Music",
                   '0042': "Neural Surround + DTS Neo:X Game", '0043': "DTS-ES Neo:X (Multi-ch Source)",
                   '0050': "THX (cyclic)", '0051': "Dolby Pro Logic + THX Cinema",
                   '0052': "Dolby Pro Logic II Movie + THX Cinema", '0053': "DTS Neo:6 Cinema + THX Cinema",
                   '0054': "Dolby Pro Logic IIx Movie + THX Cinema", '0055': "THX Select 2 Games",
                   '0056': "THX Cinema (Multi-ch Source)", '0057': "THX Surround EX (Multi-ch Source)",
                   '0058': "Dolby Pro Logic IIx Movie + THX Cinema (Multi-ch Source)",
                   '0059': "DTS-ES Neo:6 + THX Cinema (Multi-ch Source)",
                   '0060': "DTS-ES Matrix + THX Cinema (Multi-ch Source)",
                   '0061': "DTS-ES Discrete + THX Cinema (Multi-ch Source)",
                   '0062': "THX Select 2 Cinema (Multi-ch Source)", '0063': "THX Select 2 Music (Multi-ch Source)",
                   '0064': "THX Select 2 Games (Multi-ch Source)", '0065': "THX Ultra 2 Cinema (Multi-ch Source)",
                   '0066': "THX Ultra 2 Music (Multi-ch Source)",
                   '0067': "DTS-ES 8-ch Discrete + THX Cinema (Multi-ch Source)", '0068': "THX Cinema (2-ch)",
                   '0069': "THX Music (2-ch)", '0070': "THX Games (2-ch)",
                   '0071': "Dolby Pro Logic II Music + THX Music", '0072': "Dolby Pro Logic IIx Music + THX Music",
                   '0073': "DTS Neo:6 Music + THX Music", '0074': "Dolby Pro Logic II Game + THX Games",
                   '0075': "Dolby Pro Logic IIx Game + THX Games", '0076': "THX Ultra 2 Games",
                   '0077': "Dolby Pro Logic + THX Music", '0078': "Dolby Pro Logic + THX Games",
                   '0079': "THX Ultra 2 Games (Multi-ch Source)", '0080': "THX Music (Multi-ch Source)",
                   '0081': "THX Games (Multi-ch Source)",
                   '0082': "Dolby Pro Logic IIx Music + THX Music (Multi-ch Source)",
                   '0083': "Dolby Digital EX + THX Games (Multi-ch Source)",
                   '0084': "DTS Neo:6 + THX Music (Multi-ch Source)", '0085': "DTS Neo:6 + THX Games (Multi-ch Source)",
                   '0086': "Dolby Digital ES Matrix + THX Music (Multi-ch Source)",
                   '0087': "Dolby Digital ES Matrix + THX Games (Multi-ch Source)",
                   '0088': "Dolby Digital ES Discrete + THX Music (Multi-ch Source)",
                   '0089': "Dolby Digital ES Discrete + THX Games (Multi-ch Source)",
                   '0090': "Dolby Digital ES 8-ch Discrete + THX Music (Multi-ch Source)",
                   '0091': "Dolby Digital ES 8-ch Discrete + THX Games (Multi-ch Source)",
                   '0092': "Dolby Pro Logic IIz Height + THX Cinema",
                   '0093': "Dolby Digital Pro Logic IIz Height + THX Music",
                   '0094': "Dolby Pro Logic IIz Height + THX Games",
                   '0095': "Dolby Pro Logic IIz Height + THX Cinema (Multi-ch Source)",
                   '0096': "Dolby Pro Logic IIz Height + THX Music (Multi-ch Source)",
                   '0097': "Dolby Pro Logic IIz Height + THX Games (Multi-ch Source)",
                   '0100': "Advanced Surround (cyclic)", '0101': "Action", '0102': "Sci-Fi", '0103': "Drama",
                   '0104': "Entertainment Show", '0105': "Mono Film", '0106': "Expanded Theater", '0107': "Classical",
                   '0109': "Unplugged", '0110': "Rock/Pop", '0112': "Extended Stereo", '0113': "Phones Surround",
                   '0116': "TV Surround", '0117': "Sports", '0118': "Advanced Games",
                   '0151': "Auto Level Control (A.L.C.)", '0152': "Optimum Surround", '0153': "Retriever Air",
                   '0200': "ECO Mode (cyclic)", '0201': "DTS Neo:X Cinema + THX Cinema",
                   '0202': "DTS Neo:X Music + THX Music", '0203': "DTS Neo:X Game + THX Games",
                   '0204': "DTS Neo:X + THX Cinema (Multi-ch Source)", '0205': "DTS Neo:X + THX Music (Multi-ch Source)",
                   '0206': "DTS Neo:X + THX Games (Multi-ch Source)", '0212': "ECO Mode 1", '0213': "ECO Mode 2"}

# VSX-1021-K Surround Listening Mode ID mask.
VSX1021K_LISTENING_MODE_MASK = ['0011', '0028', '0037', '0038', '0039', '0040', '0041', '0042', '0043', '0050', '0051',
                                '0052', '0053', '0054', '0055', '0056', '0057', '0058', '0059', '0060', '0061', '0062',
                                '0063', '0064', '0065', '0066', '0067', '0068', '0069', '0070', '0071', '0072', '0073',
                                '0074', '0075', '0076', '0077', '0078', '0079', '0080', '0081', '0082', '0083', '0084',
                                '0085', '0086', '0087', '0088', '0089', '0090', '0091', '0092', '0093', '0094', '0095',
                                '0096', '0097', '0152', '0200', '0201', '0202', '0203', '0204', '0205', '0206', '0212',
                                '0213']

# VSX-1022-K Surround Listening Mode ID mask.
VSX1022K_LISTENING_MODE_MASK = ['0011', '0028', '0037', '0038', '0039', '0040', '0041', '0042', '0043', '0050', '0051',
                                '0052', '0053', '0054', '0055', '0056', '0057', '0058', '0059', '0060', '0061', '0062',
                                '0063', '0064', '0065', '0066', '0067', '0068', '0069', '0070', '0071', '0072', '0073',
                                '0074', '0075', '0076', '0077', '0078', '0079', '0080', '0081', '0082', '0083', '0084',
                                '0085', '0086', '0087', '0088', '0089', '0090', '0091', '0092', '0093', '0094', '0095',
                                '0096', '0097', '0152', '0200', '0201', '0202', '0203', '0204', '0205', '0206', '0212',
                                '0213']

# VSX-1122-K Surround Listening Mode ID mask.
VSX1122K_LISTENING_MODE_MASK = ['0011', '0028', '0029', '0037', '0038', '0039', '0040', '0041', '0042', '0043', '0044',
                                '0045', '0050', '0051', '0052', '0053', '0054', '0055', '0056', '0057', '0058', '0059',
                                '0060', '0061', '0062', '0063', '0064', '0065', '0066', '0067', '0068', '0069', '0070',
                                '0071', '0072', '0073', '0074', '0075', '0076', '0077', '0078', '0079', '0080', '0081',
                                '0082', '0083', '0084', '0085', '0086', '0087', '0088', '0089', '0090', '0091', '0092',
                                '0093', '0094', '0095', '0096', '0097', '0152', '0200', '0201', '0202', '0203', '0204',
                                '0205', '0206', '0212', '0213']

# VSX-1123-K Surround Listening Mode ID mask.
VSX1123K_LISTENING_MODE_MASK = ['0011', '0016', '0017', '0025', '0028', '0029', '0037', '0038', '0039', '0040', '0041',
                                '0042', '0043', '0044', '0045', '0050', '0051', '0052', '0053', '0054', '0055', '0059',
                                '0060', '0061', '0062', '0063', '0064', '0065', '0066', '0067', '0068', '0069', '0070',
                                '0071', '0072', '0073', '0074', '0075', '0076', '0077', '0078', '0079', '0080', '0081',
                                '0082', '0083', '0084', '0085', '0086', '0087', '0088', '0089', '0090', '0091', '0092',
                                '0093', '0094', '0095', '0096', '0097', '0152', '0201', '0202', '0203', '0204', '0205',
                                '0206']

# SC-75 Surround Listening Mode ID mask.
SC75_LISTENING_MODE_MASK = ['0011', '0016', '0017', '0025', '0028', '0029', '0037', '0038', '0039', '0040', '0041',
                            '0042', '0043', '0044', '0045', '0053', '0055', '0057', '0058', '0059', '0062', '0063',
                            '0064', '0065', '0066', '0073', '0076', '0077', '0078', '0079', '0083', '0084', '0085']

# Display Listening Mode IDs to names map.
DISPLAY_LISTENING_MODES = {'0101': "[)(]PLIIx MOVIE", '0102': "[)(]PLII MOVIE", '0103': "[)(]PLIIx MUSIC",
                           '0104': "[)(]PLII MUSIC", '0105': "[)(]PLIIx GAME", '0106': "[)(]PLII GAME",
                           '0107': "[)(]PROLOGIC", '0108': "Neo:6 CINEMA", '0109': "Neo:6 MUSIC",
                           '010a': "XM HD Surround", '010b': "NEURAL SURR", '010c': "2ch Straight Decode",
                           '010d': "[)(]PLIIz HEIGHT", '010e': "WIDE SURR MOVIE", '010f': "WIDE SURR MUSIC",
                           '0110': "STEREO", '0111': "Neo:X CINEMA", '0112': "Neo:X MUSIC", '0113': "Neo:X GAME",
                           '0114': "NEURAL SURROUND+Neo:X CINEMA", '0115': "NEURAL SURROUND+Neo:X MUSIC",
                           '0116': "NEURAL SURROUND+Neo:X GAMES", '1101': "[)(]PLIIx MOVIE", '1102': "[)(]PLIIx MUSIC",
                           '1103': "[)(]DIGITAL EX", '1104': "DTS + Neo:6 / DTS-HD + Neo:6", '1105': "ES MATRIX",
                           '1106': "ES DISCRETE", '1107': "DTS-ES 8ch", '1108': "multi ch Straight Decode",
                           '1109': "[)(]PLIIz HEIGHT", '110a': "WIDE SURR MOVIE", '110b': "WIDE SURR MUSIC",
                           '110c': "ES Neo:X", '0201': "ACTION", '0202': "DRAMA", '0203': "SCI-FI", '0204': "MONO FILM",
                           '0205': "ENT.SHOW", '0206': "EXPANDED", '0207': "TV SURROUND", '0208': "ADVANCED GAME",
                           '0209': "SPORTS", '020a': "CLASSICAL", '020b': "ROCK/POP", '020c': "UNPLUGGED",
                           '020d': "EXT.STEREO", '020e': "PHONES SURR.", '020f': "FRONT STAGE SURROUND ADVANCE FOCUS",
                           '0210': "FRONT STAGE SURROUND ADVANCE WIDE", '0211': "SOUND RETRIEVER AIR",
                           '0212': "ECO MODE 1", '0213': "ECO MODE 2", '0301': "[)(]PLIIx MOVIE + THX",
                           '0302': "[)(]PLII MOVIE + THX", '0303': "[)(]PL + THX CINEMA", '0304': "Neo:6 CINEMA + THX",
                           '0305': "THX CINEMA", '0306': "[)(]PLIIx MUSIC + THX", '0307': "[)(]PLII MUSIC + THX",
                           '0308': "[)(]PL + THX MUSIC", '0309': "Neo:6 MUSIC + THX", '030a': "THX MUSIC",
                           '030b': "[)(]PLIIx GAME + THX", '030c': "[)(]PLII GAME + THX", '030d': "[)(]PL + THX GAMES",
                           '030e': "THX ULTRA2 GAMES", '030f': "THX SELECT2 GAMES", '0310': "THX GAMES",
                           '0311': "[)(]PLIIz + THX CINEMA", '0312': "[)(]PLIIz + THX MUSIC",
                           '0313': "[)(]PLIIz + THX GAMES", '0314': "Neo:X CINEMA + THX CINEMA",
                           '0315': "Neo:X MUSIC + THX MUSIC", '0316': "Neo:X GAMES + THX GAMES", '1301': "THX Surr EX",
                           '1302': "Neo:6 + THX CINEMA", '1303': "ES MTRX + THX CINEMA", '1304': "ES DISC + THX CINEMA",
                           '1305': "ES 8ch + THX CINEMA", '1306': "[)(]PLIIx MOVIE + THX", '1307': "THX ULTRA2 CINEMA",
                           '1308': "THX SELECT2 CINEMA", '1309': "THX CINEMA", '130a': "Neo:6 + THX MUSIC",
                           '130b': "ES MTRX + THX MUSIC", '130c': "ES DISC + THX MUSIC", '130d': "ES 8ch + THX MUSIC",
                           '130e': "[)(]PLIIx MUSIC + THX", '130f': "THX ULTRA2 MUSIC", '1310': "THX SELECT2 MUSIC",
                           '1311': "THX MUSIC", '1312': "Neo:6 + THX GAMES", '1313': "ES MTRX + THX GAMES",
                           '1314': "ES DISC + THX GAMES", '1315': "ES 8ch + THX GAMES", '1316': "[)(]EX + THX GAMES",
                           '1317': "THX ULTRA2 GAMES", '1318': "THX SELECT2 GAMES", '1319': "THX GAMES",
                           '131a': "[)(]PLIIz + THX CINEMA", '131b': "[)(]PLIIz + THX MUSIC",
                           '131c': "[)(]PLIIz + THX GAMES", '131d': "Neo:X + THX CINEMA", '131e': "Neo:X + THX MUSIC",
                           '131f': "Neo:X + THX GAMES", '0401': "STEREO", '0402': "[)(]PLII MOVIE",
                           '0403': "[)(]PLIIx MOVIE", '0404': "Neo:6 CINEMA", '0405': "AUTO SURROUND Straight Decode",
                           '0406': "[)(]DIGITAL EX", '0407': "[)(]PLIIx MOVIE", '0408': "DTS + Neo:6",
                           '0409': "ES MATRIX", '040a': "ES DISCRETE", '040b': "DTS-ES 8ch", '040c': "XM HD Surround",
                           '040d': "NEURAL SURR", '040e': "RETRIEVER AIR", '040f': "Neo:X CINEMA", '0410': "ES Neo:X",
                           '0501': "STEREO", '0502': "[)(]PLII MOVIE", '0503': "[)(]PLIIx MOVIE",
                           '0504': "Neo:6 CINEMA", '0505': "ALC Straight Decode", '0506': "[)(]DIGITAL EX",
                           '0507': "[)(]PLIIx MOVIE", '0508': "DTS + Neo:6", '0509': "ES MATRIX", '050a': "ES DISCRETE",
                           '050b': "DTS-ES 8ch", '050c': "XM HD Surround", '050d': "NEURAL SURR",
                           '050e': "RETRIEVER AIR", '050f': "Neo:X CINEMA", '0510': "ES Neo:X", '0601': "STEREO",
                           '0602': "[)(]PLII MOVIE", '0603': "[)(]PLIIx MOVIE", '0604': "Neo:6 CINEMA",
                           '0605': "STREAM DIRECT NORMAL Straight Decode", '0606': "[)(]DIGITAL EX",
                           '0607': "[)(]PLIIx MOVIE", '0608': "(nothing)", '0609': "ES MATRIX", '060a': "ES DISCRETE",
                           '060b': "DTS-ES 8ch", '060c': "Neo:X CINEMA", '060d': "ES Neo:X",
                           '0701': "STREAM DIRECT PURE 2ch", '0702': "[)(]PLII MOVIE", '0703': "[)(]PLIIx MOVIE",
                           '0704': "Neo:6 CINEMA", '0705': "STREAM DIRECT PURE Straight Decode",
                           '0706': "[)(]DIGITAL EX", '0707': "[)(]PLIIx MOVIE", '0708': "(nothing)",
                           '0709': "ES MATRIX", '070a': "ES DISCRETE", '070b': "DTS-ES 8ch", '070c': "Neo:X CINEMA",
                           '070d': "ES Neo:X", '0881': "OPTIMUM", '0e01': "HDMI THROUGH", '0f01': "MULTI CH IN"}

# (This version expands the abbreviated text descriptions of the original version). displayListeningModes = {
# '0101':"Dolby Pro Logic IIx Movie", '0102':"Dolby Pro Logic II Movie", '0103':"Dolby Pro Logic IIx Music",
# '0104':"Dolby Pro Logic II Music", '0105':"Dolby Pro Logic IIx Game", '0106':"Dolby Pro Logic II Game",
# '0107':"Dolby Pro Logic", '0108':"DTS Neo:6 Cinema", '0109':"DTS Neo:6 Music", '010a':"XM HD Surround",
# '010b':"Neural Surround", '010c':"2-ch Straight Decode", '010d':"Dolby Pro Logic IIz Height", '010e':"Wide Surround
# Movie", '010f':"Wide Surround Music", '0110':"Stereo", '0111':"DTS Neo:X Cinema", '0112':"DTS Neo:X Music",
# '0113':"DTS Neo:X Game", '0114':"Neural Surround + DTS Neo:X Cinema", '0115':"Neural Surround + DTS Neo:X Music",
# '0116':"Neural Surround + DTS Neo:X Games", '0201':"Action", '0202':"Drama", '0203':"Sci-Fi", '0204':"Mono Film",
# '0205':"Entertainment Show", '0206':"Expanded", '0207':"TV Surround", '0208':"Advanced Game", '0209':"Sports",
# '020a':"Classical", '020b':"Rock/Pop", '020c':"Unplugged", '020d':"Extended Stereo", '020e':"Phones Surround",
# '020f':"Front Stage Surround Advanced Focus", '0210':"Front Stage Surround Advanced Wide", '0211':"Sound Retriever
# Air", '0301':"Dolby Pro Logic IIx Movie + THX", '0302':"Dolby Pro Logic II Movie + THX", '0303':"Dolby Pro Logic +
# THX Cinema", '0304':"DTS Neo:6 Cinema + THX", '0305':"THX Cinema", '0306':"Dolby Pro Logic IIx Music + THX",
# '0307':"Dolby Pro Logic II Music + THX", '0308':"Dolby Pro Logic + THX Music", '0309':"DTS Neo:6 Music + THX",
# '030a':"THX Music", '030b':"Dolby Pro Logic IIx Game + THX", '030c':"Dolby Pro Logic II Game + THX", '030d':"Dolby
# Pro Logic + THX Games", '030e':"THX Ultra 2 Games", '030f':"THX Select 2 Games", '0310':"THX Games", '0311':"Dolby
# Pro Logic IIz + THX Cinema", '0312':"Dolby Pro Logic IIz + THX Music", '0313':"Dolby Pro Logic IIz + THX Games",
# '0314':"DTS Neo:X Cinema + THX Cinema", '0315':"DTS Neo:X Music + THX Music", '0316':"DTS Neo:X Games + THX Games",
# '0401':"Stereo", '0402':"Dolby Pro Logic II Movie", '0403':"Dolby Pro Logic IIx Movie", '0404':"DTS Neo:6 Cinema",
# '0405':"Auto Surround Straight Decode", '0406':"Dolby Digital EX", '0407':"Dolby Pro Logic IIx Movie", '0408':"DTS
# Neo:6", '0409':"DTS-ES Matrix", '040a':"DTS-ES Discrete", '040b':"DTS-ES 8-ch", '040c':"XM HD Surround",
# '040d':"Neural Surround", '040e':"Retriever Air", '040f':"DTS Neo:X Cinema", '0410':"DTS-ES Neo:X",
# '0501':"Stereo", '0502':"Dolby Pro Logic II Movie", '0503':"Dolby Pro Logic IIx Movie", '0504':"DTS Neo:6 Cinema",
# '0505':"Auto Level Control (A.L.C.) Straight Decode", '0506':"Dolby Digital EX", '0507':"Dolby Pro Logic IIx
# Movie", '0508':"DTS Neo:6", '0509':"DTS-ES Matrix", '050a':"DTS-ES Discrete", '050b':"DTS-ES 8-ch", '050c':"XM HD
# Surround", '050d':"Neural Surround", '050e':"Retriever Air", '050f':"DTS Neo:X Cinema", '0510':"DTS-ES Neo:X",
# '0601':"Stereo", '0602':"Dolby Pro Logic II Movie", '0603':"Dolby Pro Logic IIx Movie", '0604':"DTS Neo:6 Cinema",
# '0605':"Stream Direct Normal Straight Decode", '0606':"Dolby Digital EX", '0607':"Dolby Pro Logic IIx Movie",
# '0608':"(nothing)", '0609':"DTS-ES Matrix", '060a':"DTS-ES Discrete", '060b':"DTS-ES 8-ch", '060c':"DTS Neo:X
# Cinema", '060d':"DTS-ES Neo:X", '0701':"Stream Direct Pure 2-ch", '0702':"Dolby Pro Logic II Movie", '0703':"Dolby
# Pro Logic IIx Movie", '0704':"DTS Neo:6 Cinema", '0705':"Stream Direct Pure Straight Decode", '0706':"Dolby Digital
# EX", '0707':"Dolby Pro Logic IIx Movie", '0708':"(nothing)", '0709':"DTS-ES Matrix", '070a':"DTS-ES Discrete",
# '070b':"DTS-ES 8-ch", '070c':"DTS Neo:X Cinema", '070d':"DTS-ES Neo:X", '0881':"Optimum", '0e01':"HDMI Through",
# '0f01':"Multi-ch In", '1101':"Dolby Pro Logic IIx Movie", '1102':"Dolby Pro Logic IIx Music", '1103':"Dolby Digital
# EX", '1104':"DTS Neo:6/DTS-HD Neo:6", '1105':"DTS-ES Matrix", '1106':"DTS-ES Discrete", '1107':"DTS-ES 8-ch",
# '1108':"Multi-ch Straight Decode", '1109':"Dolby Pro Logic IIz Height", '110a':"Wide Surround Movie", '110b':"Wide
# Surround Music", '110c':"DTS-ES Neo:X", '1301':"THX Surround EX", '1302':"DTS Neo:6 THX Cinema", '1303':"DTS-ES
# Matrix + THX Cinema", '1304':"DTS-ES Discrete + THX Cinema", '1305':"DTS-ES 8-ch + THX Cinema", '1306':"Dolby Pro
# Logic IIx Movie + THX", '1307':"THX Ultra 2 Cinema", '1308':"THX Select 2 Cinema", '1309':"THX Cinema", '130a':"DTS
# Neo:6 + THX Music", '130b':"DTS-ES Matrix + THX Music", '130c':"DTS-ES Discrete + THX Music", '130d':"DTS-ES 8-ch +
# THX Music", '130e':"Dolby Pro Logic IIx Music + THX", '130f':"THX Ultra 2 Music", '1310':"THX Select 2 Music",
# '1311':"THX Music", '1312':"DTS Neo:6 + THX Games", '1313':"DTS-ES Matrix + THX Games", '1314':"DTS-ES Discrete +
# THX Games", '1315':"DTS-ES 8-ch + THX Games", '1316':"Dolby Digital EX + THX Games", '1317':"THX Ultra 2 Games",
# '1318':"THX Select 2 Games", '1319':"THX Games", '131a':"Dolby Pro Logic IIz + THX Cinema", '131b':"Dolby Pro Logic
# IIz + THX Music", '131c':"Dolby Pro Logic IIz + THX Games", '131d':"DTS Neo:X + THX Cinema", '131e':"DTS Neo:X +
# THX Music", '131f':"DTS Neo:X + THX Games"} VSX-1021-K Playback Listening Mode mask.

VSX1021K_DISPLAY_LISTENING_MODE_MASK = ['010a', '0108', '0109', '0111', '0112', '0113', '0114', '0115', '0116', '1104',
                                        '110c', '0301', '0302', '0303', '0304', '0305', '0306', '0307', '0308', '0309',
                                        '030a', '030b', '030c', '030d', '030e', '030f', '0310', '0311', '0312', '0313',
                                        '0314', '0315', '0316', '1301', '1302', '1303', '1304', '1305', '1306', '1307',
                                        '1308', '1309', '130a', '130b', '130c', '130d', '130e', '130f', '1310', '1311',
                                        '1312', '1313', '1314', '1315', '1316', '1317', '1318', '1319', '131a', '131b',
                                        '131c', '131d', '131e', '131f', '040c', '040f', '0410', '050c', '050f', '0510',
                                        '0608', '060c', '060d', '0708', '070c', '070d', '0881', '0f01']

# VSX-1022-K Playback Listening Mode mask.
VSX1022K_DISPLAY_LISTENING_MODE_MASK = ['010a', '0108', '0109', '0111', '0112', '0113', '0114', '0115', '0116', '1104',
                                        '110c', '0301', '0302', '0303', '0304', '0305', '0306', '0307', '0308', '0309',
                                        '030a', '030b', '030c', '030d', '030e', '030f', '0310', '0311', '0312', '0313',
                                        '0314', '0315', '0316', '1301', '1302', '1303', '1304', '1305', '1306', '1307',
                                        '1308', '1309', '130a', '130b', '130c', '130d', '130e', '130f', '1310', '1311',
                                        '1312', '1313', '1314', '1315', '1316', '1317', '1318', '1319', '131a', '131b',
                                        '131c', '131d', '131e', '131f', '040c', '040f', '0410', '050c', '050f', '0510',
                                        '0608', '060c', '060d', '0708', '070c', '070d', '0881', '0f01']

# VSX-1122-K Playback Listening Mode mask.
VSX1122K_DISPLAY_LISTENING_MODE_MASK = ['010a', '010b', '010c', '0108', '0109', '0111', '0112', '0113', '0114', '0115',
                                        '0116', '1104', '110c', '110d', '110e', '0301', '0302', '0303', '0304', '0305',
                                        '0306', '0307', '0308', '0309', '030a', '030b', '030c', '030d', '030e', '030f',
                                        '0310', '0311', '0312', '0313', '0314', '0315', '0316', '1301', '1302', '1303',
                                        '1304', '1305', '1306', '1307', '1308', '1309', '130a', '130b', '130c', '130d',
                                        '130e', '130f', '1310', '1311', '1312', '1313', '1314', '1315', '1316', '1317',
                                        '1318', '1319', '131a', '131b', '131c', '131d', '131e', '131f', '040c', '040d',
                                        '040f', '0410', '050c', '050d', '050f', '0510', '0608', '060c', '060d', '0708',
                                        '070c', '070d', '0881', '0f01']

# VSX-1123-K Playback Listening Mode mask.
VSX1123K_DISPLAY_LISTENING_MODE_MASK = ['010a', '010b', '010c', '0108', '0109', '0111', '0112', '0113', '0114', '0115',
                                        '0116', '1104', '110c', '110d', '110e', '0301', '0302', '0303', '0304', '0305',
                                        '0306', '0307', '0308', '0309', '030a', '030b', '030c', '030d', '030e', '030f',
                                        '0310', '0311', '0312', '0313', '0314', '0315', '0316', '1301', '1302', '1303',
                                        '1304', '1305', '1306', '1307', '1308', '1309', '130a', '130b', '130c', '130d',
                                        '130e', '130f', '1310', '1311', '1312', '1313', '1314', '1315', '1316', '1317',
                                        '1318', '1319', '131a', '131b', '131c', '131d', '131e', '131f', '040c', '040d',
                                        '040f', '0410', '050c', '050d', '050f', '0510', '0608', '060c', '060d', '0708',
                                        '070c', '070d', '0881', '0f01']

# SC-75 Playback Listening Mode mask.
SC75_DISPLAY_LISTENING_MODE_MASK = ['010a', '010b', '010c', '0108', '0109', '0111', '0112', '0113', '0114', '0115',
                                    '0116', '1104', '110c', '110d', '110e', '0301', '0302', '0303', '0304', '0305',
                                    '0306', '0307', '0308', '0309', '030a', '030b', '030c', '030d', '030e', '030f',
                                    '0310', '0311', '0312', '0313', '0314', '0315', '0316', '1301', '1302', '1303',
                                    '1304', '1305', '1306', '1307', '1308', '1309', '130a', '130b', '130c', '130d',
                                    '130e', '130f', '1310', '1311', '1312', '1313', '1314', '1315', '1316', '1317',
                                    '1318', '1319', '131a', '131b', '131c', '131d', '131e', '131f', '040c', '040d',
                                    '040f', '0410', '050c', '050d', '050f', '0510', '0608', '060c', '060d', '0708',
                                    '070c', '070d', '0881', '0f01']

# Preferred Video Resolution ID to name map.
VIDEO_RESOLUTION_PREFS = {'00': "AUTO", '01': "PURE", '02': "Reserved", '03': "480/576p", '04': "720p", '05': "1080i",
                          '06': "1080p", '07': "1080/24p"}

# Video Resolution ID to name map.
VIDEO_RESOLUTIONS = {'00': "", '01': "480/60i", '02': "576/50i", '03': "480/60p", '04': "576/50p", '05': "720/60p",
                     '06': "720/50p", '07': "1080/60i", '08': "1080/50i", '09': "1080/60p", '10': "1080/50p",
                     '11': "1080/24p", '12': "4Kx2K/24Hz", '13': "4Kx2K/25Hz", '14': "4Kx2K/30Hz",
                     '15': "4Kx2K/24Hz (SMPTE)"}

# Audio Input Signal ID to name map.
AUDIO_INPUT_FORMATS = {'00': "ANALOG", '01': "ANALOG", '02': "ANALOG", '03': "PCM", '04': "PCM", '05': "DOLBY DIGITAL",
                       '06': "DTS", '07': "DTS-ES Matrix", '08': "DTS-ES Discrete", '09': "DTS 96/24",
                       '10': "DTS 96/24 ES Matrix", '11': "DTS 96/24 ES Discrete", '12': "MPEG-2 AAC", '13': "WMA9 Pro",
                       '14': "DSD->PCM", '15': "HDMI THROUGH", '16': "DOLBY DIGITAL PLUS", '17': "DOLBY TrueHD",
                       '18': "DTS EXPRESS", '19': "DTS-HD Master Audio", '20': "DTS-HD High Resolution",
                       '21': "DTS-HD High Resolution", '22': "DTS-HD High Resolution", '23': "DTS-HD High Resolution",
                       '24': "DTS-HD High Resolution", '25': "DTS-HD High Resolution", '26': "DTS-HD High Resolution",
                       '27': "DTS-HD Master Audio", '28': "DSD (HDMI/File)", '64': "MP3", '65': "WAV", '66': "WMA",
                       '67': "MPEG4-AAC", '68': "FLAC", '69': "ALAC (Apple Lossless)", '70': "AIFF", '71': "DSD (USB)"}

# Audio Input Frequency ID to frequency (in kHz) map.
AUDIO_INPUT_FREQUENCIES = {'00': "32 kHz", '01': "44.1 kHz", '02': "48 kHz", '03': "88.2 kHz", '04': "96 kHz",
                           '05': "176.4 kHz", '06': "192 kHz", '07': "-", '32': "2.8 MHz", '33': "5.6 MHz"}

AUDIO_OUTPUT_FREQUENCIES = {'00': "32 kHz", '01': "44.1 kHz", '02': "48 kHz", '03': "88.2 kHz", '04': "96 kHz",
                            '05': "176.4 kHz", '06': "192 kHz", '07': "-", '32': "2.8 MHz", '33': "5.6 MHz"}

# Audio Channel list.
AUDIO_CHANNELS = ['L', 'C', 'R', 'SL', 'SR', 'SBL', 'S', 'SBR', 'LFE', 'FHL', 'FHR', 'FWL', 'FWR', 'XL', 'XC', 'XR',
                  '(future)', '(future)', '(future)', '(future)', '(future)']

# Map button commands for Indigo actions to actual button names for display.
REMOTE_BUTTON_NAMES = {'CUP': "Cursor UP", 'CDN': "Cursor DOWN", 'CRI': "Cursor RIGHT", 'CLE': "Cursor LEFT",
                       'CEN': "ENTER", 'CRT': "RETURN", '33NW': "CLEAR", 'HM': "HOME", 'STS': "DISPLAY", '00IP': "PLAY",
                       '01IP': "PAUSE", '02IP': "STOP", '03IP': "PREVIOUS", '04IP': "NEXT", '07IP': "REPEAT",
                       '08IP': "SHUFFLE", '19SI': "MENU", '00SI': "0", '01SI': "1", '02SI': "2", '03SI': "3",
                       '04SI': "4", '05SI': "5", '06SI': "6", '07SI': "7", '08SI': "8", '09SI': "9"}

# Specify the order in which button names should appear in the UI menu. This is necessary because, until Python 2.7
# (Indigo uses version 2.5), Python dictionaries (like remoteButtonNames) cannot be iterated through in a set order.
REMOTE_BUTTON_NAMES_ORDER = ['CUP', 'CDN', 'CRI', 'CLE', 'CEN', 'CRT', '33NW', 'HM', 'STS', '00IP', '01IP', '02IP',
                             '03IP', '04IP', '07IP', '08IP', '19SI', '00SI', '01SI', '02SI', '03SI', '04SI', '05SI',
                             '06SI', '07SI', '08SI', '09SI']

# Connection retry delay (in approximately 1/10th second increments).
CONNECTION_RETRY_DELAY = 300

import sys
import codecs
import re

from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QAction, QComboBox, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTextBrowser, QSpacerItem, QSizePolicy, QPushButton, QFileDialog, QMenu, QMessageBox,
                             QToolButton, QSplitter, QCompleter, QDialog, QDialogButtonBox, QGridLayout, QCheckBox, QColorDialog,
                             QTableWidget, QTableWidgetItem, QAbstractItemView)

from PyQt5.QtGui import QIcon,QColor,QFont,QCursor,QPixmap,QClipboard
from PyQt5.QtCore import QSize, Qt, QTimer, QEvent

from PersistenceUtils import *

FLAT = '\u266D'
SHARP = '\u266F'

DRAWBEND1 = '\u0438'
DRAWBEND2 = '\u0439'
DRAWBEND3 = '\u043A'

BLOWBEND1 = '\u043C'
BLOWBEND2 = '\u043D'

OVERBLOW = '\u043B'
OVERDRAW = '\u0440'

DRAW = '\u043E'
BLOW = '\u043F'

DEFAULT_PLACEMENT = 'below'  # 'below' or 'above'
PREFER_FLAT = False
PREFER_SHARP = False

SUMMARY_ROWS = 10  # amount of (title,value) rows reserved for the summary

HARMONICA_MODES = (1, 2, 3, 4)  # the text modes that get the semitones shifts table
SEMITONES_SHIFTS = list(range(-12, 13))  # the shifts calculated for that table
SUMMARY_COLUMN_WIDTH = 42   # width of one semitones shift column of that table
SUMMARY_HEADER_WIDTH = 160  # width of the counter names column of that table
HIGHLIGHT_COLOR = (255, 243, 176)  # background of the column of the selected semitones shift

APP_ICON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
APP_ID = 'KobyGold.MusicXMLAnnotator'  # needed by Windows to show the app icon on the taskbar


last_pressed = False


def warndlg(title,mssg):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)

    msg.setText(mssg)
    #msg.setInformativeText("This is additional information")
    msg.setWindowTitle(title)
    #msg.setDetailedText(details)
    msg.setStandardButtons(QMessageBox.Ok)  # msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

    retval = msg.exec_()
    #print("value of pressed warning dialog button:", retval)
    return retval


def get_label(string, label):
    pattern = fr'.*<{label}>\s*(.+)\s*</{label}>.*'
    m = re.search(pattern, string)
    if m != None:
        value = m.group(1)
        return value
    else:
        return ''


def replace_text(string, text):
    pattern = r'(.*<text>\s*)(.+)(\s*</text>.*)'
    new = fr'\1 {text}\3'
    output = re.sub(pattern, new, string)
    output = output.replace('<text> ','<text>')
    output = output.replace('<text>','<text font-family="KobyMusic">')
    return output


def note_semitones(full_note):
    # full_note is NOTE + OCTAVE + <optional: #/b>
    # example: 'C4', 'B5b', 'F6#'
    steps_dct = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    alter_dct = {'': 0, '#': 1, 'b': -1}

    step = full_note[0]
    octave = int(full_note[1])
    if len(full_note) > 2:
        alter = full_note[2]
    else:
        alter = ''

    alter = alter_dct[alter]

    semitones = octave*12 + steps_dct[step] + alter
    return semitones


def semitones_to_note(semitones):
    # full_note is STEP + OCTAVE + <optional: #/b>
    # example: 'C4', 'B5b', 'F6#'
    steps_dct = {0: 'C', 2: 'D', 4: 'E', 5: 'F', 7: 'G', 9: 'A', 11: 'B'}
    alter_dct = {0: '', 1: '#', -1: 'b'}

    clean_notes = list(steps_dct.keys())

    octave = semitones // 12
    inside_octave = semitones - octave*12
    if inside_octave in clean_notes:
        alter = 0
    else:
        alter = 1
        inside_octave -= 1

    full_note = steps_dct[inside_octave] + str(octave) + alter_dct[alter]
    return full_note


def soa_to_semitones(soa):
    # soa = (step, octave, alter)
    # example: 'B5b' = ('B', '5', '-1')
    steps_dct = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

    step = soa[0]
    octave = int(soa[1])
    if soa[2]:
        alter = int(soa[2])
    else:
        alter = 0

    semitones = octave*12 + steps_dct[step] + alter
    return semitones


def semitones_to_soa(semitones):
    # full_note is STEP + OCTAVE + <optional: #/b>
    # example: 'C4', 'B5b', 'F6#'
    steps_dct = {0: 'C', 2: 'D', 4: 'E', 5: 'F', 7: 'G', 9: 'A', 11: 'B'}
    alter_dct = {0: '', 1: '1', -1: '-1'}

    clean_notes = list(steps_dct.keys())

    octave = semitones // 12
    inside_octave = semitones - octave*12
    if inside_octave in clean_notes:
        alter = 0
    else:
        alter = 1
        inside_octave -= 1

    step = steps_dct[inside_octave]
    octave = str(octave)
    alter = alter_dct[alter]
    return (step, octave, alter)


def note_to_text_ChromaticHarmonica16(step, octave, alter, returnAllOptions=False):
    global last_pressed
    extra = {'': '', '1': '#', '-1': 'b'}
    note = step + octave + extra[alter]
    dct = {'C3': 'L1',             'D3': '(L1)','E3':'L2', 'F3': ['(L2)','#L2'], 'G3': 'L3', 'A3': '(L3)', 'B3': '(L4)',
           'C4': '1',              'D4': '(1)', 'E4':'2',  'F4': ['(2)','#2'],   'G4': '3',  'A4': '(3)',  'B4': '(4)',
           'C5': ['4','5','(#4)'], 'D5': '(5)', 'E5':'6',  'F5': ['(6)','#6'],   'G5': '7',  'A5': '(7)',  'B5': '(8)',
           'C6': ['8','9','(#8)'], 'D6': '(9)', 'E6':'10', 'F6': ['(10)','#10'], 'G6': '11', 'A6': '(11)', 'B6': '(12)',
           'C7': ['12','(#12)'],

           'D3b': '#L1',       'E3b': '(#L1)', 'F3b': 'L2',            'G3b': '(#L2)', 'A3b': '#L3', 'B3b': '(#L3)',
           'C3#': '#L1',       'D3#': '(#L1)', 'E3#': ['(L2)', '#L2'], 'F3#': '(#L2)', 'G3#': '#L3', 'A3#': '(#L3)',

           'D4b': '#1',        'E4b': '(#1)', 'F4b': '2',            'G4b': '(#2)',  'A4b': '#3',  'B4b': '(#3)',
           'C4#': '#1',        'D4#': '(#1)', 'E4#': ['(2)','#2'],   'F4#': '(#2)',  'G4#': '#3',  'A4#': '(#3)',

           'D5b': ['#4','#5'], 'E5b': '(#5)', 'F5b': '6',            'G5b': '(#6)',  'A5b': '#7',  'B5b': '(#7)',
           'C5#': ['#4','#5'], 'D5#': '(#5)', 'E5#': ['(6)','#6'],   'F5#': '(#6)',  'G5#': '#7',  'A5#': '(#7)',

           'D6b': ['#8','#9'], 'E6b': '(#9)', 'F6b': '10',           'G6b': '(#10)', 'A6b': '#11', 'B6b': '(#11)',
           'C6#': ['#8','#9'], 'D6#': '(#9)', 'E6#': ['(10)','#10'], 'F6#': '(#10)', 'G6#': '#11', 'A6#': '(#11)',
           }

    name = dct.get(note, '?')

    if returnAllOptions == False:
        if type(name) == list:
            if last_pressed:  # prefer pressed '#'
                for opt in name:
                    if '#' in opt:
                        name = opt
                        break
            else:  # prefer not pressed '#'
                for opt in name:
                    if '#' not in opt:
                        name = opt
                        break
            if type(name) == list:
                name = name[-1]
        if type(name) == list:
            name = '\n'.join(name)
    else:  # returnAllOptions == True
        if type(name) == list:
            name = '\n'.join(name)

    if '#' in name:
        last_pressed = True
    else:
        last_pressed = False

    # if name.startswith('('):
    #     name += '\n\u2193'
    # else:
    #     name += '\n\u2191'

    return name


def note_to_text_ChromaticHarmonica12(step, octave, alter, returnAllOptions=False):
    global last_pressed
    extra = {'': '', '1': '#', '-1': 'b'}
    note = step + octave + extra[alter]
    dct = {'C4': '1',              'D4': '(1)', 'E4':'2',  'F4': ['(2)','#2'],   'G4': '3',  'A4': '(3)',  'B4': '(4)',
           'C5': ['4','5','(#4)'], 'D5': '(5)', 'E5':'6',  'F5': ['(6)','#6'],   'G5': '7',  'A5': '(7)',  'B5': '(8)',
           'C6': ['8','9','(#8)'], 'D6': '(9)', 'E6':'10', 'F6': ['(10)','#10'], 'G6': '11', 'A6': '(11)', 'B6': '(12)',
           'C7': ['12','(#12)'],

           'D4b': '#1',        'E4b': '(#1)', 'F4b': '2',            'G4b': '(#2)',  'A4b': '#3',  'B4b': '(#3)',
           'C4#': '#1',        'D4#': '(#1)', 'E4#': ['(2)','#2'],   'F4#': '(#2)',  'G4#': '#3',  'A4#': '(#3)',

           'D5b': ['#4','#5'], 'E5b': '(#5)', 'F5b': '6',            'G5b': '(#6)',  'A5b': '#7',  'B5b': '(#7)',
           'C5#': ['#4','#5'], 'D5#': '(#5)', 'E5#': ['(6)','#6'],   'F5#': '(#6)',  'G5#': '#7',  'A5#': '(#7)',

           'D6b': ['#8','#9'], 'E6b': '(#9)', 'F6b': '10',           'G6b': '(#10)', 'A6b': '#11', 'B6b': '(#11)',
           'C6#': ['#8','#9'], 'D6#': '(#9)', 'E6#': ['(10)','#10'], 'F6#': '(#10)', 'G6#': '#11', 'A6#': '(#11)',
           }

    name = dct.get(note, '?')

    if returnAllOptions == False:
        if type(name) == list:
            if last_pressed:  # prefer pressed '#'
                for opt in name:
                    if '#' in opt:
                        name = opt
                        break
            else:  # prefer not pressed '#'
                for opt in name:
                    if '#' not in opt:
                        name = opt
                        break
            if type(name) == list:
                name = name[-1]
        if type(name) == list:
            name = '\n'.join(name)
    else:  # returnAllOptions == True
        if type(name) == list:
            name = '\n'.join(name)

    if '#' in name:
        last_pressed = True
    else:
        last_pressed = False

    # if name.startswith('('):
    #     name += '\n\u2193'
    # else:
    #     name += '\n\u2191'

    return name

#dct = create_chromatic_harmonica_notes_dictionary(harmonica_key, harmonica_holes)
def note_to_text_ChromaticHarmonica(dct, step, octave, alter, returnAllOptions=False):
    global last_pressed
    extra = {'': '', '1': '#', '-1': 'b'}
    note = step + octave + extra[alter]

    name = dct.get(note, '?')

    if returnAllOptions == False:
        if type(name) == list:
            if last_pressed:  # prefer pressed '#'
                for opt in name:
                    if '#' in opt:
                        name = opt
                        break
            else:  # prefer not pressed '#'
                for opt in name:
                    if '#' not in opt:
                        name = opt
                        break
            if type(name) == list:
                name = name[-1]
        if type(name) == list:
            name = '\n'.join(name)
    else:  # returnAllOptions == True
        if type(name) == list:
            name = '\n'.join(name)

    if '#' in name:
        last_pressed = True
    else:
        last_pressed = False

    # if name.startswith('('):
    #     name += '\n\u2193'
    # else:
    #     name += '\n\u2191'

    return name


def note_to_text_ChromaticHarmonica10(step, octave, alter, returnAllOptions=False):
    global last_pressed
    extra = {'': '', '1': '#', '-1': 'b'}
    note = step + octave + extra[alter]
    dct = {'C4': '1',              'D4': '(1)', 'E4':'2',  'F4': ['(2)','#2'],   'G4': '3',  'A4': '(3)',  'B4': '(4)',
           'C5': ['4','5','(#4)'], 'D5': '(5)', 'E5':'6',  'F5': ['(6)','#6'],   'G5': '7',  'A5': '(7)',  'B5': '(8)',
           'C6': ['8','(#8)'],     'D6': '(9)', 'E6':'9',  'F6': ['(10)','#9'],  'G6': '10',
           'C7': ['12','(#12)'],

           'D4b': '#1',        'E4b': '(#1)', 'F4b': '2',            'G4b': '(#2)',  'A4b': '#3',  'B4b': '(#3)',
           'C4#': '#1',        'D4#': '(#1)', 'E4#': ['(2)','#2'],   'F4#': '(#2)',  'G4#': '#3',  'A4#': '(#3)',

           'D5b': ['#4','#5'], 'E5b': '(#5)', 'F5b': '6',            'G5b': '(#6)',  'A5b': '#7',  'B5b': '(#7)',
           'C5#': ['#4','#5'], 'D5#': '(#5)', 'E5#': ['(6)','#6'],   'F5#': '(#6)',  'G5#': '#7',  'A5#': '(#7)',

           'D6b': ['#8'],      'E6b': '(#9)', 'F6b': '9',            'G6b': '(#10)', 'A6b': '#10',
           'C6#': ['#8'],      'D6#': '(#9)', 'E6#': ['(10)','#9'],  'F6#': '(#10)', 'G6#': '#10',
           }

    name = dct.get(note, '?')

    if returnAllOptions == False:
        if type(name) == list:
            if last_pressed:  # prefer pressed '#'
                for opt in name:
                    if '#' in opt:
                        name = opt
                        break
            else:  # prefer not pressed '#'
                for opt in name:
                    if '#' not in opt:
                        name = opt
                        break
            if type(name) == list:
                name = name[-1]
        if type(name) == list:
            name = '\n'.join(name)
    else:  # returnAllOptions == True
        if type(name) == list:
            name = '\n'.join(name)

    if '#' in name:
        last_pressed = True
    else:
        last_pressed = False

    # if name.startswith('('):
    #     name += '\n\u2193'
    # else:
    #     name += '\n\u2191'

    return name


def get_note_name(index, octave):
    all_notes_s = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']  # with sharp (#-diez)
    all_notes_b = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']  # with flat (b-bemol)
    note = all_notes_s[index % len(all_notes_s)]
    octave += index // len(all_notes_s)
    if note.endswith('#'):
        out = f'{note[0]}{octave}#'
    else:
        out = f'{note[0]}{octave}'
    return out


def invert_dict(dictionary):
    inverted_dict = {}
    for key, value in dictionary.items():
        if value not in inverted_dict:
            inverted_dict[value] = key
        else:
            existing_value = inverted_dict[value]
            if isinstance(existing_value, list):
                existing_value.append(key)
            else:
                inverted_dict[value] = [existing_value, key]
    return inverted_dict


def create_chromatic_harmonica_notes_dictionary(hormonica_key, amount_oh_holes=12):
    # key should include both key and octave,
    # e.g: C4 (standard key of C)
    #      G3 (standard key of G, i.e. one lower octave)
    #      B3b (standard key of Bb)
    # support for 16 holes is not perfect, because its numbering is different: L1,L2,L3,L4,1,2,3,4,5,6,...,12
    key = hormonica_key[0] + hormonica_key[2:]
    base_octave = int(hormonica_key[1])
    all_notes_s = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']  # with sharp (#-diez)
    all_notes_b = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']  # with flat (b-bemol)
    if key.endswith('b'):
        key_index = all_notes_b.index(key)
    else:
        key_index = all_notes_s.index(key)
    dct = dict()
    semi_tone_offset = [0, 2, 4, 5, 7, 9, 11, 12]
    note_format_std = ['{}', '({})', '{}', '({})', '{}', '({})', '({})', '{}']
    note_format_sharp = ['#{}', '(#{})', '#{}', '(#{})', '#{}', '(#{})', '(#{})', '#{}']
    for i in range(0, amount_oh_holes//4):
        for j in range(8):
            hole_int = 1 + (j//2) + 4*i
            st_offset = key_index + semi_tone_offset[j]
            # clear notes (not sharp/flat)
            hole_str = note_format_std[j].format(hole_int)
            note_name = get_note_name(st_offset, base_octave + i)
            dct[hole_str] = note_name
            # sharp notes - button press, add 1 semi-tone
            hole_str = note_format_sharp[j].format(hole_int)
            note_name = get_note_name(st_offset + 1, base_octave + i)
            dct[hole_str] = note_name
    inv_dct = invert_dict(dct)
    #print(inv_dct)
    return inv_dct


def note_to_text_DiatonicHarmonicaC(step, octave, alter, octaveShift=0):
    global last_pressed
    extra = {'': '', '1': '#', '-1': 'b'}
    note = step + octave + extra[alter]
    note = step + str(int(octave)+octaveShift) + extra[alter]
    dct = {"C4": "1", "D4": "(1)", "E4":"2", "F4": "(2'')", "G4": "3",          "A4": "(3'')", "B4": "(3)",  # "G4": ["(2)","3"]
           "C5": "4", "D5": "(4)", "E5":"5", "F5": "(5)",   "G5": "6",          "A5": "(6)",   "B5": "(7)",
           "C6": "7", "D6": "(8)", "E6":"8", "F6": "(9)",   "G6": "9",          "A6": "(10)",  "B6": "10'",
           "C7": "10",

           "D4b": "(1')",  "E4b": "1@", "F4b": "2",                  "G4b": "(2')",  "A4b": "(3''')",  "B4b": "(3')", "C5b": "(4)",
           "C4#": "(1')",  "D4#": "1@",              "E4#": "(2'')", "F4#": "(2')",  "G4#": "(3''')",  "A4#": "(3')", "B4#": "4",

           "D5b": "(4')",  "E5b": "4@", "F5b": "5",                  "G5b": "5@",    "A5b": "(6')",  "B5b": "6@",
           "C5#": "(4')",  "D5#": "4@",              "E5#": "(5)",   "F5#": "5@",    "G5#": "(6')",  "A5#": "6@",

           "D6b": "(7@)",  "E6b": "8'", "F6b": "8",                  "G6b": "9'",    "A6b": "(9@)",  "B6b": "10''",
           "C6#": "(7@)",  "D6#": "8'",              "E6#": "(9)",   "F6#": "9'",    "G6#": "(9@)",  "A6#": "10''",

           "D7b": "(10@)",
           "C7#": "(10@)",
           }

    name = dct.get(note, '?')
    if name == "?":
        return name

    if type(name) == list:
        #name = name[0]
        name = '\n'.join(name)

    if name.startswith('('):  # draw notes
        direction = 'draw'
    else:
        direction = 'blow'

    bends = name.count("'")
    overblowdraw = name.count("@")

    name = name.replace("'", "")
    name = name.replace("@", "")
    name = name.replace("(", "")
    name = name.replace(")", "")

    draw_arrows = [DRAW, DRAWBEND1, DRAWBEND2, DRAWBEND3]
    blow_arrows = [BLOW, BLOWBEND1, BLOWBEND2]

    if overblowdraw > 0:
        if direction == 'draw':
            arrow = OVERDRAW
        else:
            arrow = OVERBLOW
    else:
        if direction == 'draw':
            arrow = draw_arrows[bends]
        else:
            arrow = blow_arrows[bends]

    name = arrow + '\n' + name

    return name


def note_to_text_Recorder(step, octave, alter, octaveShift=0, addHebrew=False):
    notes = ['לה', 'סי', 'דו', 'רה', 'מי', 'פה', 'סול']
    octaveShift -= 1  #  by default Recorder sheet is displayed at a lower octave, e.g. C5 on XML file is displayed as C4 on page
    step_index = ord(step) - ord('A')
    if addHebrew:
        name = notes[step_index]
        if alter == '1':
            name = '#' + name
            #name = name + '#'
        elif alter == '-1':
            name = 'b' + name
            #name = name + 'b'
    else:
        name = ''

    extra = {'': '', '1': '#', '-1': 'b'}
    note = step + octave + extra[alter]
    note = step + str(int(octave)+octaveShift) + extra[alter]
    dct = {"C4": "11111133", "D4": "11111130", "E4": "11111100", "F4": "11111033", "G4": "11110000",          "A4": "11100000", "B4": "11000000",
           "C5": "10100000", "D5": "00100000", "E5": "21111100", "F5": "21111030", "G5": "21110000",          "A5": "21100000", "B5": "21101100",
           "C6": "21001100", "D6": "21011030",

           "D4b": "11111131",  "E4b": "11111110", "F4b": "11111100",              "G4b": "11110130",  "A4b": "11101130",  "B4b": "11011000", "C5b": "11000000",
           "C4#": "11111131",  "D4#": "11111110",              "E4#": "11111033", "F4#": "11110130",  "G4#": "11101130",  "A4#": "11011000",                    "B4#": "10100000",

           "D5b": "01100000",  "E5b": "00111130", "F5b": "21111100",               "G5b": "21110100",    "A5b": "21101000",  "B5b": "21101130", "C6b": "21101100",
           "C5#": "01100000",  "D5#": "00111130",             "E5#": "21111030",   "F5#": "21110100",    "G5#": "21101000",  "A5#": "21101130",                 "B5#": "21001100",

           "D6b": "21211233",  "E6b": "20110130", "F6b": "?",               "G6b": "?",    "A6b": "?",  "B6b": "?",
           "C6#": "21211233",  "D6#": "20110130",             "E6#": "?",   "F6#": "?",    "G6#": "?",  "A6#": "?",
           }

    holes_ids = dct.get(note, '?')

    BG = '\u045D\n'
    TABLE = [['\u0456', '\u0457', '\u0458', 'x'],
             ['\u0453', '\u0454', '\u0455', 'x'],
             ['\u0453', '\u0454', '\u0455', 'x'],
             ['\u0456', '\u0457', '\u0458', 'x'],
             ['\u0453', '\u0454', '\u0455', 'x'],
             ['\u0453', '\u0454', '\u0455', 'x'],
             ['\u0459', '\u045A', '\u045B', '\u045C'],
             ['\u0459', '\u045A', '\u045B', '\u045C']]

    if holes_ids == '?':
        return '?'

    ids = list(map(int, list(holes_ids)))

    output = ''
    for k in range(len(ids)):
        LUT = TABLE[k]
        i = ids[k]
        char = LUT[i]
        output += char + '\n'

    name = name + '\n' + BG + output
    name = name.replace('b',FLAT)
    name = name.replace('#',SHARP)
    if name.startswith('\n'):
        name = name[1:]

    return name


def note_to_text_trumpet(step, octave, alter, addHebrew=False):
    notes = ['לה', 'סי', 'דו', 'רה', 'מי', 'פה', 'סול']
    step_index = ord(step) - ord('A')
    if addHebrew:
        name = notes[step_index]
        if alter == '1':
            name = '#' + name
            #name = name + '#'
        elif alter == '-1':
            name = 'b' + name
            #name = name + 'b'
        elif alter == '':
            pass
        else:
            warndlg('ERROR',f'note alteration of "{alter}" is not supported!')
    else:
        name = ''

    extra = {'': '', '1': '#', '-1': 'b'}
    note = step + octave + extra[alter]
    dct = {                                                                            'F3#': 7, 'G3b': 7, 'G3': 5, 'G3#': 3, 'A3b': 3, 'A3': 6, 'A3#': 4, 'B3b': 4, 'B3': 2,
           'C4': 0, 'C4#': 7, 'D4b': 7, 'D4': 5, 'D4#': 3, 'E4b': 3, 'E4': 6, 'F4': 4, 'F4#': 2, 'G4b': 2, 'G4': 0, 'G4#': 3, 'A4b': 3, 'A4': 6, 'A4#': 4, 'B4b': 4, 'B4': 2,
           'C5': 0, 'C5#': 6, 'D5b': 6, 'D5': 4, 'D5#': 2, 'E5b': 2, 'E5': 0, 'F5': 4, 'F5#': 2, 'G5b': 2, 'G5': 0, 'G5#': 3, 'A5b': 3, 'A5': 6, 'A5#': 4, 'B5b': 4, 'B5': 2,
           'C6': 0, 'C6#': 6, 'D6b': 6, 'D6': 4, 'D6#': 2, 'E6b': 2, 'E6': 0, 'F6': 4, 'F6#': 2, 'G6b': 2, 'G6': 0,
           }
    # signs3 = ['\n\u0470', '\n\u0473']  # on my font
    # signs2 = ['\n\u046F', '\n\u0472']
    # signs1 = ['\n\u046E', '\n\u0471']
    signs3 = ['\n\u2462', '\n\u2778']
    signs2 = ['\n\u2461', '\n\u2777']
    signs1 = ['\n\u2460', '\n\u2776']
    code = dct.get(note, None)
    if code is not None:
        bit2 = (code >> 2) & 0x1
        bit1 = (code >> 1) & 0x1
        bit0 = code & 0x1
        chars = signs3[bit0] + signs2[bit1] + signs1[bit2]
        name += chars
    else:
        name += '\n' + note + '\n?'

    name = name.replace('b',FLAT)
    name = name.replace('#',SHARP)
    if name.startswith('\n'):
        name = name[1:]
    return name


def note_to_text_baritone(step, octave, alter, addHebrew=False):
    notes = ['לה', 'סי', 'דו', 'רה', 'מי', 'פה', 'סול']
    step_index = ord(step) - ord('A')
    if addHebrew:
        name = notes[step_index]
        if alter == '1':
            name = '#' + name
            #name = name + '#'
        elif alter == '-1':
            name = 'b' + name
            #name = name + 'b'
    else:
        name = ''

    extra = {'': '', '1': '#', '-1': 'b'}
    note = step + octave + extra[alter]
    dct = {
                                                                     'E2': 7, 'F2': 5, 'F2#': 3, 'G2b': 3, 'G2': 6, 'G2#': 4, 'A2b': 4, 'A2': 2, 'A2#': 0, 'B2b': 0, 'B2': 7,
           'C3': 5, 'C3#': 3, 'D3b': 3, 'D3': 6, 'D3#': 4, 'E3b': 4, 'E3': 2, 'F3': 0, 'F3#': 3, 'G3b': 3, 'G3': 6, 'G3#': 4, 'A3b': 4, 'A3': 2, 'A3#': 0, 'B3b': 0, 'B3': 6,
           'C4': 4, 'C4#': 2, 'D4b': 2, 'D4': 0, 'D4#': 4, 'E4b': 4, 'E4': 2, 'F4': 0, 'F4#': 3, 'G4b': 3, 'G4': 6, 'G4#': 4, 'A4b': 4, 'A4': 2, 'A4#': 0, 'B4b': 0,
           }
    # signs3 = ['\n\u0470', '\n\u0473']  # on my font
    # signs2 = ['\n\u046F', '\n\u0472']
    # signs1 = ['\n\u046E', '\n\u0471']
    signs3 = ['\n\u2462', '\n\u2778']
    signs2 = ['\n\u2461', '\n\u2777']
    signs1 = ['\n\u2460', '\n\u2776']
    code = dct.get(note, None)
    if code is not None:
        bit2 = (code >> 2) & 0x1
        bit1 = (code >> 1) & 0x1
        bit0 = code & 0x1
        chars = signs3[bit0] + signs2[bit1] + signs1[bit2]
        name += chars
    else:
        name += '\n' + note + '\n?'

    name = name.replace('b',FLAT)
    name = name.replace('#',SHARP)
    if name.startswith('\n'):
        name = name[1:]

    return name


def change_notes_according_to_preference(step, alter):
    if PREFER_FLAT == True and PREFER_SHARP == True:
        warndlg('ERROR', 'Both PREFER_FLAT and PREFER_SHARP are True! Change at least one of them to False')

    if PREFER_FLAT:
        # prefer Bb instead of A#
        if step == 'A' and alter == '1':
            (step, alter) = ('B', '-1')

        # prefer Ab instead of G#
        if step == 'G' and alter == '1':
            (step, alter) = ('A', '-1')

        # prefer Gb instead of F#
        if step == 'F' and alter == '1':
            (step, alter) = ('G', '-1')

        # prefer Eb instead of D#
        if step == 'D' and alter == '1':
            (step, alter) = ('E', '-1')

        # prefer Db instead of C#
        if step == 'C' and alter == '1':
            (step, alter) = ('D', '-1')

    if PREFER_SHARP:
        # prefer C# instead of Db
        if step == 'D' and alter == '-1':
            (step, alter) = ('C', '1')

        # prefer D# instead of Eb
        if step == 'E' and alter == '-1':
            (step, alter) = ('D', '1')

        # prefer F# instead of Gb
        if step == 'G' and alter == '-1':
            (step, alter) = ('F', '1')

        # prefer G# instead of Ab
        if step == 'A' and alter == '-1':
            (step, alter) = ('G', '1')

        # prefer A# instead of Bb
        if step == 'B' and alter == '-1':
            (step, alter) = ('A', '1')

    return (step, alter)


def note_to_text_tuba(step, octave, alter, addHebrew=False):
    notes = ['לה', 'סי', 'דו', 'רה', 'מי', 'פה', 'סול']
    step_index = ord(step) - ord('A')
    if addHebrew:
        name = notes[step_index]
        if alter == '1':
            name = '#' + name
            #name = name + '#'
        elif alter == '-1':
            name = 'b' + name
            #name = name + 'b'
    else:
        name = ''

    extra = {'': '', '1': '#', '-1': 'b'}
    note = step + octave + extra[alter]
    dct = {
                                                                     'E1': 7, 'F1': 5, 'F1#': 3, 'G1b': 3, 'G1': 6, 'G1#': 4, 'A1b': 4, 'A1': 2, 'A1#': 0, 'B1b': 0, 'B1': 7,
           'C2': 5, 'C2#': 3, 'D2b': 3, 'D2': 6, 'D2#': 4, 'E2b': 4, 'E2': 2, 'F2': 0, 'F2#': 3, 'G2b': 3, 'G2': 6, 'G2#': 4, 'A2b': 4, 'A2': 2, 'A2#': 0, 'B2b': 0, 'B2': 6,
           'C3': 4, 'C3#': 2, 'D3b': 2, 'D3': 0, 'D3#': 4, 'E3b': 4, 'E3': 2, 'F3': 0, 'F3#': 3, 'G3b': 3, 'G3': 6, 'G3#': 4, 'A3b': 4, 'A3': 2, 'A3#': 0, 'B3b': 0,
           }
    # signs3 = ['\n\u0470', '\n\u0473']  # on my font
    # signs2 = ['\n\u046F', '\n\u0472']
    # signs1 = ['\n\u046E', '\n\u0471']
    signs3 = ['\n\u2462', '\n\u2778']
    signs2 = ['\n\u2461', '\n\u2777']
    signs1 = ['\n\u2460', '\n\u2776']
    code = dct.get(note, None)
    if code is not None:
        bit2 = (code >> 2) & 0x1
        bit1 = (code >> 1) & 0x1
        bit0 = code & 0x1
        chars = signs3[bit0] + signs2[bit1] + signs1[bit2]
        name += chars
    else:
        name += '\n' + note + '\n?'

    name = name.replace('b',FLAT)
    name = name.replace('#',SHARP)
    if name.startswith('\n'):
        name = name[1:]

    return name


def note_to_text_english(step, octave, alter):
    notes = ['לה', 'סי', 'דו', 'רה', 'מי', 'פה', 'סול']
    step_index = ord(step) - ord('A')
    name = notes[step_index]
    if alter == '1':
        name = '#' + name
        #name = name + '#'
    elif alter == '-1':
        name = 'b' + name
        #name = name + 'b'

    extra = {'': '', '1': '#', '-1': 'b'}
    note = step + octave + extra[alter]
    dct = {
           }
    #signs = ['\n\u26AA', '\n\u26AB']
    signs3 = ['\n\u2462', '\n\u2778']
    signs2 = ['\n\u2461', '\n\u2777']
    signs1 = ['\n\u2460', '\n\u2776']
    code = dct.get(note, None)
    if code is not None:
        bit2 = (code >> 2) & 0x1
        bit1 = (code >> 1) & 0x1
        bit0 = code & 0x1
        chars = signs3[bit0] + signs2[bit1] + signs1[bit2]
        name += chars
    else:
        name += '\n' + note

    name = name.replace('b',FLAT)
    name = name.replace('#',SHARP)

    return name



def note_to_text_heb(step, octave, alter):
    notes = ['לה', 'סי' ,'דו', 'רה', 'מי', 'פה', 'סול']
    step_index = ord(step) - ord('A')
    name = notes[step_index]
    if alter == '1':
        name = '#' + name
    elif alter == '-1':
        name = 'b' + name

    name = name.replace('b', FLAT)
    name = name.replace('#', SHARP)

    return name



def test_semitones_conversion():
    notes1 = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4']
    notes2 = ['C4#', 'D4#', 'E4#', 'F4#', 'G4#', 'A4#', 'B4#']
    notes3 = ['C4b', 'D4b', 'E4b', 'F4b', 'G4b', 'A4b', 'B4b']
    notes = notes1 + notes2 + notes3
    for note in notes:
        semitones = note_semitones(note)
        note_new = semitones_to_note(semitones)
        if note_new != note:
            print(f'ERROR: {note_new} != {note}, semitones = {semitones}')


def soa_shift(soa, semitonesOffset):
    step, octave, alter = soa
    if semitonesOffset != 0:
        semitones = soa_to_semitones(soa)
        semitones += semitonesOffset
        soa = semitones_to_soa(semitones)
    if semitonesOffset == 12:
        soa = (step, str(int(octave)+1), alter)
    if semitonesOffset == 24:
        soa = (step, str(int(octave)+2), alter)
    if semitonesOffset == -12:
        soa = (step, str(int(octave)-1), alter)
    if semitonesOffset == -24:
        soa = (step, str(int(octave)-2), alter)

    return soa


# every Diatonic Harmonica annotation starts with one arrow character, which tells exactly how the
# note is played, so the alterations can be counted one by one
DIATONIC_ARROWS = {'drawbend05': DRAWBEND1, 'drawbend10': DRAWBEND2, 'drawbend15': DRAWBEND3,
                   'blowbend05': BLOWBEND1, 'blowbend10': BLOWBEND2,
                   'overblow': OVERBLOW, 'overdraw': OVERDRAW}

COUNT_KEYS = ['total', 'button', 'impossible'] + list(DIATONIC_ARROWS.keys())


def count_alterations(all_text):
    # count the alterations of the annotated notes, per alteration type
    counts = dict.fromkeys(COUNT_KEYS, 0)
    counts['total'] = len(all_text)
    for text in all_text:
        if '#' in text:
            counts['button'] += 1
        if '?' in text:
            counts['impossible'] += 1
        for (key, arrow) in DIATONIC_ARROWS.items():
            if arrow in text:
                counts[key] += 1
    return counts


def empty_alterations():
    # the same counters, with no value yet (before the first Calc)
    return dict.fromkeys(COUNT_KEYS, '')


# how hard each way of playing a note is on a diatonic harmonica, from 0 (a plain blow or draw
# note, nothing to do) to 10 (the note is simply not on the harmonica). the draw bends come first
# because they are the ones every player learns, the blow bends live in the high register and need
# another embouchure, and the overbends need a well gapped harmonica on top of the technique.
# tune these values to your own playing if you disagree with them
DIATONIC_DIFFICULTY = {'drawbend05': 1,   # half step draw bend, the first bend one learns
                       'drawbend10': 2,   # whole step draw bend
                       'drawbend15': 3,   # 1.5 step draw bend, hole 3 only, hard to keep in tune
                       'blowbend05': 3,   # half step blow bend, high register
                       'blowbend10': 4,   # whole step blow bend, hole 10
                       'overblow': 5,     # overblow, needs a gapped harmonica
                       'overdraw': 6,     # overdraw, the hardest one to control
                       'impossible': 10}  # not playable at all on this harmonica


def diatonic_difficulty(counts):
    # average difficulty of a note, over all the counted notes.
    # the plain blow and draw notes are worth 0, so only the altered ones are summed here
    if not counts['total']:
        return ''  # no Calc yet, or no note at all

    score = 0
    for (key, weight) in DIATONIC_DIFFICULTY.items():
        score += counts[key] * weight
    return score / counts['total']


def summary_value_text(value):
    # the counters are whole numbers, the average difficulty is not
    if value == '':
        return ''
    if isinstance(value, float):
        return f'{value:.2f}'
    return str(value)


def fix_notes_split(input_list):
    output = list()
    for i in range(len(input_list)):
        string = input_list[i]
        if string.startswith(' ') or string.startswith('>') or (i == 0):
            output.append(string)
        else:
            output[-1] = output[-1] + 'note' + string
    return output


def load_xml_text(in_xml_file):
    # read a whole MusicXML file into a single string (returns '' on failure)
    try:
        with codecs.open(in_xml_file, "r", "utf-8") as fi:
            lines = fi.readlines()
    except Exception as e:
        err = str(e)
        warndlg('ERROR in opening file', f'ERROR: Error in MusicXML file!\nInput file may not be supported or wrong format selected')
        return ''

    return ''.join(lines)


def split_to_notes(single_line):
    splt = single_line.split('note')
    splt = fix_notes_split(splt)
    return splt


def get_part_names(single_line):
    # map the id of every <score-part> of the <part-list> to its <part-name>
    names = dict()
    for match in re.finditer(r'<score-part\s+id="([^"]*)"(.*?)</score-part>', single_line, re.DOTALL):
        part_id = match.group(1)
        names[part_id] = get_label(match.group(2), 'part-name')
    return names


def instrument_staff_key(part_id, staff):
    # unique id of one staff of one instrument, used to select the staves to annotate
    return f'{part_id}/{staff}'


def parse_measures_range(text):
    # parse a measures range text like '3-8' or '1-4,9,12-16' into a list of (first,last) tuples,
    # returns None if the text is not a valid measures range
    ranges = list()
    for section in text.split(','):
        section = section.strip()
        if not section:
            continue
        match = re.match(r'^(\d+)\s*-\s*(\d+)$', section)
        if match:
            first = int(match.group(1))
            last = int(match.group(2))
        elif re.match(r'^\d+$', section):
            first = int(section)
            last = first
        else:
            return None
        if last < first:
            (first, last) = (last, first)
        ranges.append((first, last))

    if not ranges:
        return None
    return ranges


def measure_in_ranges(measure, ranges):
    # ranges = None means "all the measures"
    if ranges is None:
        return True
    for (first, last) in ranges:
        if first <= measure <= last:
            return True
    return False


def get_measures_range(single_line):
    # return the (first,last) measure numbers of the whole file, or None if it holds no measure
    numbers = list()
    for number in re.findall(r'<measure\s+number="([^"]*)"', single_line):
        try:
            numbers.append(int(number))
        except ValueError:
            pass  # irregular measure number (for example "X1"), it is not a range limit
    if not numbers:
        return None
    return (min(numbers), max(numbers))


def measures_range_to_text(measures_range):
    if not measures_range:
        return ''
    (first, last) = measures_range
    if first == last:
        return str(first)
    return f'{first}-{last}'


def iterate_pitched_notes(splt):
    # walk over the splitted chunks and yield (index, chunk, part_id, staff, measure) of every
    # pitched note. the annotated unit is one staff of one instrument (a 2 hands piano part is
    # made of 2 such staves)
    part_id = ''
    measure = 0
    for i in range(len(splt)):
        string = splt[i]
        parts = re.findall(r'<part\s+id="([^"]*)"', string)
        if parts:
            part_id = parts[-1]  # a chunk between 2 notes may close a part and open the next one
        for number in re.findall(r'<measure\s+number="([^"]*)"', string):
            try:
                measure = int(number)
            except ValueError:
                pass  # irregular measure number (for example "X1"), keep the previous one
        if 'pitch' in string:
            staff = get_label(string, 'staff')
            if not staff:
                staff = '1'  # a single staff part may not write the <staff> label at all
            yield i, string, part_id, staff, measure


def scan_music_file(in_xml_file):
    # scan the file once, and return both the list of the instrument staves that hold notes,
    # and the (first,last) measures range of the whole file
    single_line = load_xml_text(in_xml_file)
    if not single_line:
        return [], None

    splt = split_to_notes(single_line)
    part_names = get_part_names(single_line)

    instrument_staves = list()
    by_key = dict()
    for i, string, part_id, staff, measure in iterate_pitched_notes(splt):
        key = instrument_staff_key(part_id, staff)
        if key not in by_key:
            by_key[key] = {'key': key, 'part_id': part_id, 'staff': staff,
                           'name': part_names.get(part_id, '') or part_id, 'count': 0}
            instrument_staves.append(by_key[key])
        by_key[key]['count'] += 1

    staves_per_part = dict()
    parts_per_name = dict()
    for entry in instrument_staves:
        staves_per_part[entry['part_id']] = staves_per_part.get(entry['part_id'], 0) + 1
        parts_per_name.setdefault(entry['name'], set()).add(entry['part_id'])
    for entry in instrument_staves:
        label = entry['name']
        if len(parts_per_name[entry['name']]) > 1:  # several parts share the same name, add the part id
            label = f"{entry['part_id']}: {label}"
        if staves_per_part[entry['part_id']] > 1:  # more than one staff (for example: piano left/right hand)
            label = f"{label} - staff {entry['staff']}"
        entry['label'] = label

    return instrument_staves, get_measures_range(single_line)


def note_to_text(mode, step, octave, alter):
    # the annotation text of a single note, for the selected text mode
    if mode == 0:
        return note_to_text_heb(step, octave, alter)
    elif mode == 1:
        return note_to_text_ChromaticHarmonica10(step, octave, alter, returnAllOptions=False)
    elif mode == 2:
        return note_to_text_ChromaticHarmonica12(step, octave, alter, returnAllOptions=False)
    elif mode == 3:
        return note_to_text_ChromaticHarmonica16(step, octave, alter, returnAllOptions=False)
    elif mode == 4:
        return note_to_text_DiatonicHarmonicaC(step, octave, alter, 0)
    elif mode == 5:
        return note_to_text_trumpet(step, octave, alter, addHebrew=False)
    elif mode == 6:
        return note_to_text_baritone(step, octave, alter, addHebrew=False)
    elif mode == 7:
        return note_to_text_tuba(step, octave, alter, addHebrew=False)
    elif mode == 8:
        return note_to_text_Recorder(step, octave, alter, 0, addHebrew=False)
    elif mode == 9:
        return note_to_text_english(step, octave, alter)

    warndlg('ERROR', 'Text mode not supported!')
    return '?'


def annotation_text(mode, soa, semitonesShift):
    # the annotation of one note, shifted and normalized the same way add_text_to_notes() does it
    (step, octave, alter) = soa_shift(soa, semitonesShift)
    (step, alter) = change_notes_according_to_preference(step, alter)
    new_text = note_to_text(mode, step, octave, alter)
    if '\n' in new_text:
        new_text = '[' + new_text.replace('\n', ',') + ']'
    return new_text


def collect_pitched_notes(splt, selected_staves=None, measures=None):
    # parse the (step,octave,alter) of every selected note once, so that the annotations can be
    # recalculated for many semitones shifts without parsing the file again
    notes = list()
    for i, string, part_id, staff, measure in iterate_pitched_notes(splt):
        if selected_staves is not None and instrument_staff_key(part_id, staff) not in selected_staves:
            continue
        if not measure_in_ranges(measure, measures):
            continue
        notes.append((get_label(string, 'step'), get_label(string, 'octave'), get_label(string, 'alter')))
    return notes


def count_all_shifts(in_xml_file, mode, shifts=None, selected_staves=None, measures=None):
    # count the alterations of every semitones shift, returns {shift: counters}
    global last_pressed
    if shifts is None:
        shifts = SEMITONES_SHIFTS

    single_line = load_xml_text(in_xml_file)
    if not single_line:
        return dict()

    notes = collect_pitched_notes(split_to_notes(single_line), selected_staves, measures)

    counts_per_shift = dict()
    for shift in shifts:
        last_pressed = False  # the harmonica slide starts released on every pass
        all_text = [annotation_text(mode, soa, shift) for soa in notes]
        counts_per_shift[shift] = count_alterations(all_text)
    return counts_per_shift


def add_text_to_notes(in_xml_file, out_xml_file='', mode=0, semitonesShift=0, selected_staves=None, measures=None):
    # selected_staves is a collection of staff keys to annotate (None = annotate all the staves)
    # measures is a list of (first,last) measures to annotate (None = annotate all the measures)
    single_line = load_xml_text(in_xml_file)
    if not single_line:
        return [],[]

    splt = split_to_notes(single_line)

    global last_pressed
    last_pressed = False  # the harmonica slide starts released, so that every run gives the same output

    prev_note = dict()  # last annotated note of each staff (staves are independent of each other)

    all_notes = list()
    all_text = list()
    for i, string, part_id, staff, measure in iterate_pitched_notes(splt):
        key = instrument_staff_key(part_id, staff)
        if selected_staves is not None and key not in selected_staves:
            continue  # this staff was not selected by the user - leave it untouched
        if not measure_in_ranges(measure, measures):
            continue  # this measure is out of the selected measures range - leave it untouched

        step = get_label(string, 'step')
        octave = get_label(string, 'octave')
        alter = get_label(string, 'alter')
        voice = get_label(string, 'voice')
        (step, octave, alter) = soa_shift((step, octave, alter), semitonesShift)
        current_note = step + octave + alter
        if DEFAULT_PLACEMENT == 'above':
            if voice == '1':  # place additional voice "above", where default voice text is "below"
                placement = 'placement="above" '
            else:
                placement = 'placement="below" '
        else:
            if voice == '1':  # place additional voice "above", where default voice text is "below"
                placement = 'placement="below" '
            else:
                placement = 'placement="above" '

        if 'text' not in string:
            if '\n' in string:
                lyric = f'        <lyric number="1" {placement}color="#000000">\n          <syllabic>single</syllabic>\n          <text>NONE</text>\n          </lyric>'
                sss1 = string.split('\n')
                end = sss1.pop()
                sss1.append(lyric)
                sss1.append(end)
                string = '\n'.join(sss1)
            else:
                lyric = f'<lyric number="1" {placement}color="#000000"><syllabic>single</syllabic><text>NONE</text></lyric>'
                string = string[0:-2] + lyric + string[-2:]

        (step, alter) = change_notes_according_to_preference(step, alter)

        new_text = note_to_text(mode, step, octave, alter)
        if '\n' in new_text:
            text = '[' + new_text.replace('\n',',') + ']'
            all_text.append(text)
        else:
            all_text.append(new_text)
        if '?' in new_text:
            string = string.replace('color="#000000"', 'color="#FF0000"')
        newstr = replace_text(string, new_text)
        if 'tie type="stop"' not in string or prev_note.get(key) != current_note:  # don't write note text if this is a 'tie' to previous note, and previous note is identical
            splt[i] = newstr
        prev_note[key] = current_note
        all_notes.append(f'{step}{octave}{alter}')
        #print(f'{step}{octave}{alter}', end=',')

    output = 'note'.join(splt)

    if out_xml_file:
        with codecs.open(out_xml_file, "w+", "utf-8") as fo:
            fo.write(output)

    return all_notes,all_text


def main_process():
    #test_semitones_conversion()
    mode = 1  # heb, chromatic10, chromatic12, diatonicC
    all_notes,all_text = add_text_to_notes(my_xml_file, outfile, mode, 0)
    print(','.join(all_text))
    print(f'Alterations counts = {count_alterations(all_text)}')


class DndLineEdit(QLineEdit):
    def __init__(self, parent):
        super(DndLineEdit, self).__init__(parent)
        self.parent = parent

    def dragEnterEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    # register a callback function when file is dropped
    def setDropFcn(self,dropFcnName):
        self.dropFcn = dropFcnName

    def dropEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            filepath = str(urls[0].path())[1:]
            # any file type here - call external dropFcn() registered earlier
            self.dropFcn(filepath)


class ClickableLineEdit(QLineEdit):
    def __init__(self, parent):
        super(ClickableLineEdit, self).__init__(parent)
        self.parent = parent
        self.clickFcn = None

    # register a callback function when the text box is clicked
    def setClickFcn(self,clickFcnName):
        self.clickFcn = clickFcnName

    def mousePressEvent(self, event):
        if self.clickFcn:
            self.clickFcn()
        QLineEdit.mousePressEvent(self, event)


class InstrumentStavesDialog(QDialog):
    # let the user choose which instruments/staves of the input file will be annotated
    def __init__(self, parent, instrument_staves, selected_staves):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Select Instruments & Staves')
        self.setFont(parent.font())
        self.checkboxes = list()

        grid = QGridLayout(self)
        grid.setSpacing(10)

        index = 0
        grid.addWidget(QLabel('Annotate only the checked staves:'), index, 0, 1, 2)

        for entry in instrument_staves:
            index += 1
            checkbox = QCheckBox(f"{entry['label']}   ({entry['count']} notes)")
            checkbox.setChecked((selected_staves is None) or (entry['key'] in selected_staves))
            checkbox.staff_key = entry['key']
            self.checkboxes.append(checkbox)
            grid.addWidget(checkbox, index, 0, 1, 2)

        index += 1
        self.select_all_btn = QPushButton('Select All')
        self.select_all_btn.clicked.connect(self.select_all)
        self.clear_all_btn = QPushButton('Clear All')
        self.clear_all_btn.clicked.connect(self.clear_all)
        grid.addWidget(self.select_all_btn, index, 0)
        grid.addWidget(self.clear_all_btn,  index, 1)

        index += 1
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        grid.addWidget(buttons, index, 0, 1, 2)

    def select_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def clear_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def selected_staves(self):
        return [checkbox.staff_key for checkbox in self.checkboxes if checkbox.isChecked()]

    def accept(self):
        if not self.selected_staves():
            warndlg('No Staff Selected', 'ERROR: at least one staff must be selected')
            return
        QDialog.accept(self)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self)
        self.input_file = ''
        self.output_file = ''
        self.semitones_shift = 0
        self.instrument_staves = list()  # all the instrument staves found in the input file
        self.selected_staves = None      # keys of the staves to annotate (None = all the staves)
        self.summary_table = None            # built by initUI(), may be resized before that
        self.summary_counts = None           # counters of the last Calc (None = no Calc yet)
        self.summary_counts_per_shift = None  # counters of the last Calc, per semitones shift
        self.file_measures = None        # the (first,last) measures range of the input file
        self.measures = None             # the measures to annotate (None = all the measures)
        self.measures_text = ''          # last valid content of the measures text box
        self.initUI()

    def closeEvent(self, event):
        #print("User has clicked the red x on the main window")
        event.accept()


    def initUI(self):
        self.setWindowIcon(QIcon(APP_ICON_FILE))
        self.title = 'MusicXML Auto Annotator'
        self.version = 'v0.5.4'

        # wide enough to show the whole semitones shifts table without scrolling it,
        # but never wider than the screen
        windowWidth = SUMMARY_HEADER_WIDTH + len(SEMITONES_SHIFTS)*SUMMARY_COLUMN_WIDTH + 40
        windowHeight = 200
        screen = QApplication.primaryScreen().availableGeometry()
        windowWidth = min(windowWidth, screen.width() - 40)
        windowLeft = min(600, max(screen.left(), screen.right() - windowWidth - 20))
        windowTop = 200

        self.setWindowTitle(f'{self.title} - {self.version}')
        self.setGeometry(windowLeft, windowTop, windowWidth, windowHeight)

        defaultDpi = 100
        btnHeight = 25
        btnWidth  = 70
        iconSize = btnHeight - 6
        titleWidth = 130
        bigBtnWidth = 250
        txtHeight = 19

        font1 = QFont()
        font1.setPointSize(defaultDpi // 10)
        font2 = QFont()
        font2.setPointSize(defaultDpi // 10)
        font2.setUnderline(True)
        font = QFont()
        font.setPointSize(defaultDpi // 10)
        #font.setFamily("Courier New")

        self.input_file_title = QLabel('Input MusicXML File:')
        self.input_file_title.setFont(font1)
        self.input_file_title.setFixedWidth(titleWidth)
        self.input_file_edit = DndLineEdit(self)
        self.input_file_edit.setText(str(self.input_file))
        self.input_file_edit.editingFinished.connect(self.input_file_changed)
        self.input_file_edit.setDropFcn(self.handleDropFileInput)
        self.input_file_edit.setFont(font)
        self.input_file_edit.setMinimumWidth(bigBtnWidth)

        #self.browse_input_file = QPushButton(QIcon('download-icon.png'),'Browse')
        self.browse_input_file = QPushButton('Browse')
        self.browse_input_file.setFixedHeight(btnHeight)
        self.browse_input_file.setFixedWidth(btnWidth)
        self.browse_input_file.setCheckable(False)
        self.browse_input_file.setFont(font1)
        self.browse_input_file.clicked.connect(self.select_input_file)

        self.output_file_title = QLabel('Output MusicXML File:')
        self.output_file_title.setFont(font1)
        self.output_file_title.setFixedWidth(titleWidth)
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setText(str(self.output_file))
        #self.output_file_edit.editingFinished.connect(self.output_file_changed)
        #self.output_file_edit.returnPressed.connect(self.output_file_changed)
        self.output_file_edit.setFont(font)
        self.output_file_edit.setMinimumWidth(bigBtnWidth)

        #self.browse_output_file = QPushButton(QIcon('download-icon.png'),'Browse')
        self.browse_output_file = QPushButton('Browse')
        self.browse_output_file.setFixedHeight(btnHeight)
        self.browse_output_file.setFixedWidth(btnWidth)
        self.browse_output_file.setCheckable(False)
        self.browse_output_file.setFont(font1)
        self.browse_output_file.clicked.connect(self.select_output_file)

        self.options_title = QLabel(' ')
        self.options_title.setFont(font1)

        self.semitones_shift_title = QLabel('Semitones Shift:')
        self.semitones_shift_title.setFont(font1)
        self.semitones_shift_title.setFixedWidth(titleWidth)
        self.semitones_shift_edit = QLineEdit()
        self.semitones_shift_edit.setText(str(self.semitones_shift))
        self.semitones_shift_edit.editingFinished.connect(self.semitones_shift_changed)
        self.semitones_shift_edit.returnPressed.connect(self.semitones_shift_changed)
        self.semitones_shift_edit.setFont(font)
        self.semitones_shift_edit.setMinimumWidth(bigBtnWidth)

        self.instruments_title = QLabel('Instruments:')
        self.instruments_title.setFont(font1)
        self.instruments_title.setFixedWidth(titleWidth)
        self.instruments_edit = ClickableLineEdit(self)
        self.instruments_edit.setReadOnly(True)
        self.instruments_edit.setClickFcn(self.instruments_clicked)
        self.instruments_edit.setFont(font)
        self.instruments_edit.setMinimumWidth(bigBtnWidth)

        self.select_staves_btn = QPushButton('Select')
        self.select_staves_btn.setFixedHeight(btnHeight)
        self.select_staves_btn.setFixedWidth(btnWidth)
        self.select_staves_btn.setCheckable(False)
        self.select_staves_btn.setFont(font1)
        self.select_staves_btn.clicked.connect(self.select_instrument_staves)

        self.measures_title = QLabel('Measures:')
        self.measures_title.setFont(font1)
        self.measures_title.setFixedWidth(titleWidth)
        self.measures_edit = QLineEdit()
        self.measures_edit.editingFinished.connect(self.measures_changed)
        self.measures_edit.returnPressed.connect(self.measures_changed)
        self.measures_edit.setToolTip('Measures to annotate, for example: 3-8 or 1-4,9,12-16')
        self.measures_edit.setFont(font)
        self.measures_edit.setMinimumWidth(bigBtnWidth)

        self.text_mode_title = QLabel('Text Mode:')
        self.text_mode_title.setFont(font1)
        self.text_mode_title.setFixedWidth(titleWidth)
        self.text_mode_combo = QComboBox(self)
        items = ['Hebrew Names','Chromatic Harmonica 10','Chromatic Harmonica 12','Chromatic Harmonica 16','Diatonic Harmonica (C)', 'Trumpet+Hebrew', 'Baritone+Hebrew', 'Tuba+Hebrew', 'Recorder+Hebrew', 'English+Hebrew']  # first one is the default one
        self.out_postfix = ['Hebrew','Chromatic10','Chromatic12','Chromatic16','DiatonicC','Trumpet','Baritone','Tuba','Recorder','English']  # name extension for outfile
        self.text_mode_combo.addItems(items)
        self.text_mode_combo.activated.connect(self.combo_activated)
        self.text_mode_combo.setFont(font1)
        selected_mode = 0
        self.text_mode_type = selected_mode
        #index = self.text_mode_combo.findText(selected_mode, Qt.MatchFixedString)
        #if index >= 0:
        #    self.text_mode_combo.setCurrentIndex(index)

        self.summary0_title = QLabel('Summary:')
        self.summary0_title.setFont(font2)

        # the summary holds one (title,value) row per counter of the selected text mode,
        # the unused rows stay hidden and take no space
        self.summary_titles = list()
        self.summary_texts = list()
        for i in range(SUMMARY_ROWS):
            title = QLabel('')
            title.setFont(font1)
            value = QLabel('')
            value.setFont(font1)
            self.summary_titles.append(title)
            self.summary_texts.append(value)

        #self.run_btn = QPushButton(QIcon('download-icon.png'),'Browse')
        self.run_btn = QPushButton('Run')
        self.run_btn.setFixedHeight(btnHeight)
        #self.run_btn.setFixedWidth(btnWidth)
        self.run_btn.setCheckable(False)
        self.run_btn.setFont(font1)
        self.run_btn.clicked.connect(self.run)

        #self.run_btn = QPushButton(QIcon('download-icon.png'),'Browse')
        self.calc_btn = QPushButton('Calc')
        self.calc_btn.setFixedHeight(btnHeight)
        #self.calc_btn.setFixedWidth(btnWidth)
        self.calc_btn.setCheckable(False)
        self.calc_btn.setFont(font1)
        self.calc_btn.clicked.connect(self.calc)

        self.summary_table = QTableWidget(self)
        self.summary_table.setFont(font1)
        self.summary_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.summary_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.summary_table.horizontalHeader().setDefaultSectionSize(SUMMARY_COLUMN_WIDTH)
        self.summary_table.verticalHeader().setDefaultSectionSize(txtHeight + 3)
        self.summary_table.verticalHeader().setFixedWidth(SUMMARY_HEADER_WIDTH)
        self.summary_table.setMinimumWidth(300)
        self.summary_table.setVisible(False)

        self.consoleViewer = QTextBrowser(self)
        self.consoleViewer.setReadOnly(True)
        self.consoleViewer.setMinimumWidth(300)
        self.consoleViewer.setMinimumHeight(200)
        #self.consoleViewer.resize(500,10)
        self.consoleViewer.setLineWrapMode(QTextBrowser.NoWrap)
        font3 = QFont()
        font3.setPointSize(defaultDpi // 10)
        font3.setFamily("Courier New")
        self.consoleViewer.setStyleSheet("color: rgb(0,0,0)")
        self.consoleViewer.setFont(font3)

        widget = QWidget(self)
        self.setCentralWidget(widget)

        grid = QGridLayout(widget)
        grid.setSpacing(10)

        index = 0
        N_GRID = 4  # number of columns in grid layout
        # grid.addWidget(title0, index, 0, 1, 2) # span 1 rows & 2 columns

        index += 1
        grid.addWidget(self.input_file_title,   index, 0)
        grid.addWidget(self.input_file_edit,    index, 1, 1, 2)
        grid.addWidget(self.browse_input_file,  index, 3)

        index += 1
        grid.addWidget(self.output_file_title,  index, 0)
        grid.addWidget(self.output_file_edit,   index, 1, 1, 2)
        grid.addWidget(self.browse_output_file, index, 3)

        index += 1
        grid.addWidget(self.text_mode_title,       index, 0)
        grid.addWidget(self.text_mode_combo,       index, 1, 1, 2)

        index += 1
        grid.addWidget(self.semitones_shift_title,  index, 0)
        grid.addWidget(self.semitones_shift_edit,   index, 1, 1, 2)

        index += 1
        grid.addWidget(self.instruments_title,  index, 0)
        grid.addWidget(self.instruments_edit,   index, 1, 1, 2)
        grid.addWidget(self.select_staves_btn,  index, 3)

        index += 1
        grid.addWidget(self.measures_title,     index, 0)
        grid.addWidget(self.measures_edit,      index, 1, 1, 2)

        index += 1
        grid.addWidget(self.options_title,      index, 0)

        index += 1
        grid.addWidget(self.summary0_title,     index, 0)

        index += 1
        for i in range(SUMMARY_ROWS):
            grid.addWidget(self.summary_titles[i], index, 0)
            grid.addWidget(self.summary_texts[i],  index, 1)
            index += 1

        grid.addWidget(self.summary_table, index, 0, 1, 4)

        index += 1
        grid.addWidget(self.consoleViewer, index, 0, 1, 4)

        index += 1
        grid.addWidget(self.run_btn,  index,    3, 1, 1)
        grid.addWidget(self.calc_btn,  index,   2, 1, 1)

        self.update_summary()
        self.update_instrument_staves_text()
        self.show()

    def combo_activated(self):
        sender = self.sender()  # this is the sender of this signal, i.e. the combo box
        if sender == self.text_mode_combo:
            self.text_mode_type = sender.currentText()
            self.auto_update_output_file()
            self.clear_summary()

    def summary_rows(self, counts):
        # the (title, value, colored, best) summary rows of the selected text mode.
        # a "colored" row is shown in green when it is 0, and in red otherwise.
        # a "best" row also marks its lowest value over all the semitones shifts of the table
        mode = self.text_mode_combo.currentIndex()
        rows = [('Total Amount of Notes', counts['total'], False, False)]

        if mode == 4:  # diatonic harmonica, the easiest shift to play is the lowest one here
            rows.append(('Average Difficulty', diatonic_difficulty(counts), False, True))

        if mode in (1, 2, 3):  # chromatic harmonicas
            rows.append(('Button Count', counts['button'], False, False))

        if mode == 4:  # diatonic harmonica, one row per way of altering a note
            rows.append(('0.5 Draw Bend Count', counts['drawbend05'], False, False))
            rows.append(('1.0 Draw Bend Count', counts['drawbend10'], False, False))
            rows.append(('1.5 Draw Bend Count', counts['drawbend15'], False, False))
            rows.append(('0.5 Blow Bend Count', counts['blowbend05'], False, False))
            rows.append(('1.0 Blow Bend Count', counts['blowbend10'], False, False))
            rows.append(('OverBlow Count', counts['overblow'], False, False))
            rows.append(('OverDraw Count', counts['overdraw'], False, False))

        if mode in (1, 2, 3, 4, 5, 6, 7, 8):  # modes that cannot play every note
            rows.append(('Impossible Notes Count', counts['impossible'], True, False))

        return rows

    def update_summary(self):
        # the harmonica modes get a table of every semitones shift, the other modes a list of rows
        as_table = self.text_mode_combo.currentIndex() in HARMONICA_MODES
        counts = self.summary_counts if self.summary_counts else empty_alterations()
        rows = self.summary_rows(counts)

        for i in range(SUMMARY_ROWS):
            visible = (not as_table) and (i < len(rows))
            if visible:
                (name, value, colored, best) = rows[i]
                self.summary_titles[i].setText(f'- {name}:')
                self.summary_texts[i].setText(summary_value_text(value))
                if colored and value != '':
                    if value == 0:
                        self.summary_texts[i].setStyleSheet("color: rgb(0,155,0)")
                    else:
                        self.summary_texts[i].setStyleSheet("color: rgb(255,0,0)")
                else:
                    self.summary_texts[i].setStyleSheet("")
            else:  # an unused row keeps no stale value
                self.summary_titles[i].setText('')
                self.summary_texts[i].setText('')
            self.summary_titles[i].setVisible(visible)
            self.summary_texts[i].setVisible(visible)

        self.summary_table.setVisible(as_table)
        if as_table:
            self.update_summary_table()

    def update_summary_table(self):
        # one row per counter, one column per semitones shift, and the column of the semitones
        # shift selected by the user is highlighted, because this is the one that "Run" writes
        table = self.summary_table
        counts_per_shift = self.summary_counts_per_shift
        rows_per_shift = dict()
        for shift in SEMITONES_SHIFTS:
            counts = counts_per_shift.get(shift) if counts_per_shift else None
            rows_per_shift[shift] = self.summary_rows(counts if counts else empty_alterations())
        first_rows = rows_per_shift[SEMITONES_SHIFTS[0]]
        names = [name for (name, value, colored, best) in first_rows]

        # the lowest value of every "best" row, to mark the shift that is the easiest to play
        best_values = dict()
        for row in range(len(first_rows)):
            if first_rows[row][3]:
                values = [rows_per_shift[shift][row][1] for shift in SEMITONES_SHIFTS]
                values = [value for value in values if value != '']
                if values:
                    best_values[row] = min(values)

        table.clear()
        table.setRowCount(len(names))
        table.setColumnCount(len(SEMITONES_SHIFTS))
        table.setVerticalHeaderLabels(names)
        for row in range(len(names)):
            if names[row] == 'Average Difficulty':
                weights = ', '.join(f'{key}={weight}' for (key, weight) in DIATONIC_DIFFICULTY.items())
                table.verticalHeaderItem(row).setToolTip(
                    'Average difficulty of a note: a plain blow or draw note is worth 0, and\n'
                    f'{weights}.\nThe lowest value is the easiest shift to play, and it is marked in green.')
        table.setHorizontalHeaderLabels([f'{shift:+d}' if shift else '0' for shift in SEMITONES_SHIFTS])

        highlight = QColor(*HIGHLIGHT_COLOR)
        selected_column = None
        for column in range(len(SEMITONES_SHIFTS)):
            shift = SEMITONES_SHIFTS[column]
            selected = (shift == self.semitones_shift)
            if selected:
                selected_column = column
                header = table.horizontalHeaderItem(column)
                header.setBackground(highlight)
                font = header.font()
                font.setBold(True)
                header.setFont(font)

            for row in range(len(names)):
                (name, value, colored, best) = rows_per_shift[shift][row]
                item = QTableWidgetItem(summary_value_text(value))
                item.setTextAlignment(Qt.AlignCenter)
                if colored and value != '':
                    item.setForeground(QColor(0, 155, 0) if value == 0 else QColor(255, 0, 0))
                if best and row in best_values and value == best_values[row]:
                    item.setForeground(QColor(0, 155, 0))  # the easiest shift to play
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                if selected:
                    item.setBackground(highlight)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                table.setItem(row, column, item)

        self.resize_summary_table()

        # once the table got its real size, fix its height again (the scrollbar is only known by
        # then) and bring the highlighted column into view. only the column index may be kept,
        # the items themselves are dropped by the next table.clear()
        QTimer.singleShot(0, lambda: self.show_summary_table_column(selected_column))

    def resize_summary_table(self):
        # keep the table exactly as high as its rows, plus its scrollbar when it has one
        table = self.summary_table
        if table is None:
            return
        height = table.horizontalHeader().height() + 2*table.frameWidth()
        for row in range(table.rowCount()):
            height += table.rowHeight(row)
        if table.horizontalScrollBar().isVisible():
            height += table.horizontalScrollBar().height()
        if table.height() != height:
            table.setFixedHeight(height)

    def show_summary_table_column(self, column):
        # center the table on the given column, if it is still there
        self.resize_summary_table()
        if column is None:
            return
        item = self.summary_table.item(0, column)
        if item is not None:
            self.summary_table.scrollToItem(item, QAbstractItemView.PositionAtCenter)

    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)
        # the scrollbar of the table appears and disappears with the width of the window,
        # and whether it is there is only known once the layout settled
        QTimer.singleShot(0, self.resize_summary_table)

    def input_file_changed(self,extText=''):
        text = self.input_file_edit.text()
        if text == self.input_file:
            return  # the input file did not change, nothing to do
        self.input_file = text
        self.auto_update_output_file()
        self.refresh_file_info()

    def clear_summary(self):
        # forget the counters of the previous Calc, they belong to another mode or another file
        self.summary_counts = None
        self.summary_counts_per_shift = None
        self.update_summary()

    def refresh_file_info(self):
        # rescan the input file, and reset the selection to all its staves and all its measures
        self.instrument_staves = list()
        self.selected_staves = None
        self.file_measures = None
        if self.input_file and os.path.isfile(self.input_file):
            self.instrument_staves, self.file_measures = scan_music_file(self.input_file)
        self.update_instrument_staves_text()
        self.reset_measures()
        self.clear_summary()

    def reset_measures(self):
        # show the whole measures range of the input file, and annotate all of it
        self.measures = None
        self.measures_text = measures_range_to_text(self.file_measures)
        self.measures_edit.setText(self.measures_text)

    def measures_changed(self):
        # validate the measures text box, and restore its last valid content if it is not a range
        text = self.measures_edit.text().strip()
        ranges = parse_measures_range(text) if text else None
        if text and ranges is None:
            warndlg('ERROR in Measures value',
                    f'ERROR: unsupported measures range: "{text}"'
                    f'\nuse a range like "3-8", a single measure like "5", or a list like "1-4,9,12-16"')
            self.measures_edit.setText(self.measures_text)  # restore the last valid range
            return
        self.measures = ranges  # an empty text box means "all the measures"
        self.measures_text = text

    def selected_staves_labels(self):
        return [entry['label'] for entry in self.instrument_staves
                if (self.selected_staves is None) or (entry['key'] in self.selected_staves)]

    def update_instrument_staves_text(self):
        total = len(self.instrument_staves)
        self.select_staves_btn.setEnabled(total > 0)
        if total == 0:
            self.instruments_edit.setText('')
            self.instruments_edit.setToolTip('')
            self.instruments_edit.setCursor(QCursor(Qt.ArrowCursor))
            return
        labels = self.selected_staves_labels()
        if total == 1:  # a single staff file has nothing to choose from
            text = labels[0]
        elif self.selected_staves is None:
            text = f'All {total} selected: ' + ', '.join(labels)
        else:
            text = f'{len(labels)} of {total} selected: ' + ', '.join(labels)
        self.instruments_edit.setText(text)
        self.instruments_edit.setToolTip(text + '\n(click to choose the staves to annotate)')
        self.instruments_edit.setCursor(QCursor(Qt.PointingHandCursor))

    def instruments_clicked(self):
        # clicking the instruments text box is the same as pressing the "Select" button next to it
        if self.instrument_staves:
            self.select_instrument_staves()

    def select_instrument_staves(self):
        if not self.instrument_staves:
            warndlg('No Staves Found', 'ERROR: no staves found, please load a valid MusicXML input file first')
            return
        dialog = InstrumentStavesDialog(self, self.instrument_staves, self.selected_staves)
        if dialog.exec_() == QDialog.Accepted:
            selected = dialog.selected_staves()
            if len(selected) == len(self.instrument_staves):
                self.selected_staves = None  # all the staves are selected
            else:
                self.selected_staves = selected
            self.update_instrument_staves_text()

    def output_file_changed(self):
        sender = self.sender()
        text = sender.text()
        self.output_file = text
        #print(f'output_file = {text}')
        #self.update_gui_due_to_input_file_change('')

    def semitones_shift_changed(self):
        # validate the semitones text box, and restore its last valid value if it holds no number
        text = self.semitones_shift_edit.text().strip()
        try:
            self.semitones_shift = int(text)
        except ValueError:
            warndlg('ERROR in Semitones value',
                    f'ERROR: unsupported semitones value: "{text}"'
                    f'\nuse a whole number of semitones, for example: -3')
            self.semitones_shift_edit.setText(str(self.semitones_shift))  # restore the last valid value
            return

        self.auto_update_output_file()
        self.update_summary()  # move the highlight to the column of the new semitones shift


    def handleDropFileInput(self,filepath):
        if os.path.isfile(filepath):  # given input is file, take the parent folder
            path, filename = os.path.split(filepath)
        self.input_file = filepath
        self.input_file_edit.setText(filepath)
        self.auto_update_output_file()
        self.refresh_file_info()


    def get_Save_FileName(self, text_box):
        options = QFileDialog.Options()

        if text_box.text():
            suggested_name = text_box.text()
            #inPathFile, inFileExt = os.path.splitext(text_box.text())
            #folder = inPathFile  # get folder from text_box
        else:
            suggested_name = 'C:\\'

        #name, types = QFileDialog.getSaveFileName(self, f'Select File', suggested_name,
        #                                          f'{ext} Log Files (*.{ext})', options=options)

        name, types = QFileDialog.getSaveFileName(self, f'Select File', suggested_name)
        #print(f'name = {name}, types = {types}')
        return name

    def get_Open_FileName(self, text_box):
        options = QFileDialog.Options()

        if text_box.text():
            suggested_name = text_box.text()
            inPathFile, inFileExt = os.path.splitext(text_box.text())
            folder = inPathFile  # get folder from text_box
        else:
            folder = getConfigVar('musicxmlannotator_lastLoadedInputFolder','C:/')  # get last loaded folder from persistence config file

        selectedFilePath, _ = QFileDialog.getOpenFileName(self, "Choose Input File", folder,
                                                 "MusicXML (*.xml *.musicxml)", options=options)

        if len(selectedFilePath) == 0:
            self.statusBar().showMessage("load input file: canceled by user")
            return ''

        setConfigVar('musicxmlannotator_lastLoadedInputFolder', selectedFilePath)
        #print(f'name = {selectedFilePath}')
        return selectedFilePath

    def select_input_file(self):
        fileSelected = self.get_Open_FileName(self.input_file_edit)
        self.input_file = fileSelected
        self.input_file_edit.setText(fileSelected)
        self.auto_update_output_file()
        self.refresh_file_info()

    def select_output_file(self):
        fileSelected = self.get_Save_FileName(self.output_file_edit)
        self.output_file = fileSelected
        self.output_file_edit.setText(self.output_file)
        #self.update_gui_due_to_input_file_change('input')

    def auto_update_output_file(self):
        # update output filename according to input filename and selected mode
        if self.input_file:
            out_postfix = self.out_postfix[self.text_mode_combo.currentIndex()]
            inPathFile, inFileExt = os.path.splitext(self.input_file)
            inFileExt = inFileExt.lower()  # '.xml'
            if self.semitones_shift != 0:
                if self.semitones_shift > 0:
                    semitones_shift = f'+{self.semitones_shift}st'
                else:
                    semitones_shift = f'-{-self.semitones_shift}st'
            else:
                semitones_shift = ''
            self.output_file = inPathFile + '-' + out_postfix + semitones_shift + inFileExt
            self.output_file_edit.setText(self.output_file)

    def run(self):
        self.calc(True)

    def calc(self, saveOutput=False):
        self.input_file_changed()  # in case the user updated the input text box manually
        self.measures_changed()    # in case the user updated the measures text box manually
        self.output_file = self.output_file_edit.text()  # in case the user update the text box manually
        index = self.text_mode_combo.currentIndex()
        if saveOutput:
            all_notes,all_text = add_text_to_notes(self.input_file, self.output_file, index, self.semitones_shift, self.selected_staves, self.measures)
        else:
            all_notes,all_text = add_text_to_notes(self.input_file, '', index, self.semitones_shift, self.selected_staves, self.measures)
        self.consoleViewer.clear()
        if self.instrument_staves:
            self.consoleViewer.append('Annotated Staves:')
            self.consoleViewer.append(', '.join(self.selected_staves_labels()))
            self.consoleViewer.append('')
            self.consoleViewer.append('Annotated Measures:')
            self.consoleViewer.append(self.measures_text if self.measures else 'all')
            self.consoleViewer.append('')
        self.consoleViewer.append('Notes:')
        self.consoleViewer.append(','.join(all_notes))
        self.consoleViewer.append('\nTexts:')
        self.consoleViewer.append(','.join(all_text))
        self.summary_counts = count_alterations(all_text)
        if index in HARMONICA_MODES:  # calculate every semitones shift, not only the selected one
            self.summary_counts_per_shift = count_all_shifts(self.input_file, index, SEMITONES_SHIFTS,
                                                             self.selected_staves, self.measures)
        else:
            self.summary_counts_per_shift = None
        self.update_summary()


def build_note_characters():
    steps = ['C', 'C', 'D', 'D', 'E', 'F', 'F', 'G', 'G', 'A', 'A', 'B']
    alters = ['', '1', '',  '1',  '',  '', '1', '',  '1', '',  '1', '']
    octaves = list('12345678')
    alter_dct = {'': '', '1': '#'}
    first_pitch = 60 - (4 - int(octaves[0]))*12
    texts = list()
    notes = list()
    mode = 10

    # For mode 10 (Generic Chromatic Harmonica):
    #dct = create_chromatic_harmonica_notes_dictionary('G3')
    #dct = create_chromatic_harmonica_notes_dictionary('A3')
    #dct = create_chromatic_harmonica_notes_dictionary('B3b')
    #dct = create_chromatic_harmonica_notes_dictionary('C4')
    #dct = create_chromatic_harmonica_notes_dictionary('D4')
    #dct = create_chromatic_harmonica_notes_dictionary('E4')
    #dct = create_chromatic_harmonica_notes_dictionary('F4')
    dct = create_chromatic_harmonica_notes_dictionary('E4b')

    for octave in octaves:
        for i in range(len(steps)):
            step = steps[i]
            alter = alters[i]
            if mode == 0:
                new_text = note_to_text_heb(step, octave, alter)
            elif mode == 1:
                new_text = note_to_text_ChromaticHarmonica10(step, octave, alter, returnAllOptions=True)
            elif mode == 2:
                new_text = note_to_text_ChromaticHarmonica12(step, octave, alter, returnAllOptions=True)
            elif mode == 3:
                new_text = note_to_text_ChromaticHarmonica16(step, octave, alter, returnAllOptions=True)
            elif mode == 4:
                new_text = note_to_text_DiatonicHarmonicaC(step, octave, alter, 0)
            elif mode == 5:
                new_text = note_to_text_trumpet(step, octave, alter, addHebrew=False)
            elif mode == 6:
                new_text = note_to_text_baritone(step, octave, alter, addHebrew=False)
            elif mode == 7:
                new_text = note_to_text_tuba(step, octave, alter, addHebrew=False)
            elif mode == 8:
                new_text = note_to_text_Recorder(step, octave, alter, 0, addHebrew=True)
            elif mode == 9:
                new_text = note_to_text_english(step, octave, alter)
            elif mode == 10:  # Generic Chromatic Harmonica
                new_text = note_to_text_ChromaticHarmonica(dct, step, octave, alter, returnAllOptions=False)
            else:
                warndlg('ERROR', 'Text mode not supported!')
            texts.append(new_text)
            notes.append(f'{step}{octave}{alter_dct[alter]}')
    non_valid_at_beginning = 0
    non_valid_at_end = len(texts)
    LENGTH = len(texts)
    if 0:  # remove '?' marks of unsupported notes
        for text in texts:
            if '?' in text:
                non_valid_at_beginning += 1
            else:
                break
        for text in texts[-1::-1]:
            if '?' in text:
                non_valid_at_end -= 1
            else:
                break
    texts = texts[non_valid_at_beginning:non_valid_at_end]
    notes = notes[non_valid_at_beginning:non_valid_at_end]
    first_pitch += non_valid_at_beginning
    print(f'non_valid_at_beginning = {non_valid_at_beginning} / {LENGTH}')
    print(f'non_valid_at_end = {non_valid_at_end} / {LENGTH}')
    print(f'first_pitch = {first_pitch}')
    line1 = ' '
    line2 = '['
    line3 = '['
    for i in range(len(notes)):
        note = notes[i]
        text = ascii(texts[i])[1:-1]
        #text = text.replace('\n', '\\n')
        diff = len(text) + 4 - len(note)
        line1 += note + ' '*diff
        line2 += '"' + text + '", '
        line3 += '"' + note + '", ' + ' '*(diff-4)
    line2 = line2[0:-2] + ']'
    ind = line3.rfind(',')
    line3 = line3[0:ind]
    line3 += ']'
    print('      //                            ' + line1)
    print('      property variant fingerings : ' + line2)
    print('      property variant notenames  : ' + line3)


def set_windows_app_id(app_id=APP_ID):
    # without an explicit "app user model id" Windows groups the app under the generic python
    # icon on the taskbar, instead of using the icon of the window
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception as e:
        err = str(e)  # not running on Windows, keep the default behavior


if __name__ == '__main__':
    if 0:  # build only
        build_note_characters()
    else:
        set_windows_app_id()
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(APP_ICON_FILE))  # used by every window and dialog of the app
        mainWin = MainWindow()
        mainWin.show()
        sys.exit(app.exec_())

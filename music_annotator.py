import sys
import codecs
import re

from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QAction, QComboBox, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTextBrowser, QSpacerItem, QSizePolicy, QPushButton, QFileDialog, QMenu, QMessageBox,
                             QToolButton, QSplitter, QCompleter, QDialog, QDialogButtonBox, QGridLayout, QCheckBox, QColorDialog)

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

DRAW = '\u043E'
BLOW = '\u043F'

DEFAULT_PLACEMENT = 'below'  # 'below' or 'above'
PREFER_FLAT = False
PREFER_SHARP = False


last_pressed = False


def warndlg(title,mssg):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowIcon(QIcon("warning_orange.png"))

    msg.setText(mssg)
    #msg.setInformativeText("This is additional information")
    msg.setWindowTitle(title)
    #msg.setDetailedText(details)
    msg.setStandardButtons(QMessageBox.Ok)  # msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

    retval = msg.exec_()
    print("value of pressed warning dialog button:", retval)
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

    if type(name) == list:
        #name = name[0]
        name = '\n'.join(name)

    if name.startswith('('):  # draw notes
        direction = 'draw'
    else:
        direction = 'blow'

    bends = name.count("'")
    overblow = name.count("@")

    name = name.replace("'", "")
    name = name.replace("@", "")
    name = name.replace("(", "")
    name = name.replace(")", "")

    draw_arrows = [DRAW, DRAWBEND1, DRAWBEND2, DRAWBEND3]
    blow_arrows = [BLOW, BLOWBEND1, BLOWBEND2]

    if overblow > 0:
        arrow = OVERBLOW
    else:
        if direction == 'draw':
            arrow = draw_arrows[bends]
        else:
            arrow = blow_arrows[bends]

    name = arrow + '\n ' + name

    return name


def note_to_text_trumpet(step, octave, alter):
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
    dct = {                                                                            'F3#': 7, 'G3b': 7, 'G3': 5, 'G3#': 3, 'A3b': 3, 'A3': 6, 'A3#': 4, 'B3b': 4, 'B3': 2,
           'C4': 0, 'C4#': 7, 'D4b': 7, 'D4': 5, 'D4#': 3, 'E4b': 3, 'E4': 6, 'F4': 4, 'F4#': 2, 'G4b': 2, 'G4': 0, 'G4#': 3, 'A4b': 3, 'A4': 6, 'A4#': 4, 'B4b': 4, 'B4': 2,
           'C5': 0, 'C5#': 6, 'D5b': 6, 'D5': 4, 'D5#': 2, 'E5b': 2, 'E5': 0, 'F5': 4, 'F5#': 2, 'G5b': 2, 'G5': 0, 'G5#': 3, 'A5b': 3, 'A5': 6, 'A5#': 4, 'B5b': 4, 'B5': 2,
           'C6': 0, 'C6#': 6, 'D6b': 6, 'D6': 4, 'D6#': 2, 'E6b': 2, 'E6': 0, 'F6': 4, 'F6#': 2, 'G6b': 2, 'G6': 0,
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
        name += '\n' + note + '\n?'

    name = name.replace('b',FLAT)
    name = name.replace('#',SHARP)
    return name


def note_to_text_baritone(step, octave, alter):
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
                                                                     'E2': 7, 'F2': 5, 'F2#': 3, 'G2b': 3, 'G2': 6, 'G2#': 4, 'A2b': 4, 'A2': 2, 'A2#': 0, 'B2b': 0, 'B2': 7,
           'C3': 5, 'C3#': 3, 'D3b': 3, 'D3': 6, 'D3#': 4, 'E3b': 4, 'E3': 2, 'F3': 0, 'F3#': 3, 'G3b': 3, 'G3': 6, 'G3#': 4, 'A3b': 4, 'A3': 2, 'A3#': 0, 'B3b': 0, 'B3': 6,
           'C4': 4, 'C4#': 2, 'D4b': 2, 'D4': 0, 'D4#': 4, 'E4b': 4, 'E4': 2, 'F4': 0, 'F4#': 3, 'G4b': 3, 'G4': 6, 'G4#': 4, 'A4b': 4, 'A4': 2, 'A4#': 0, 'B4b': 0,
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
        name += '\n' + note + '\n?'

    name = name.replace('b',FLAT)
    name = name.replace('#',SHARP)

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


def note_to_text_tuba(step, octave, alter):
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
                                                                     'E1': 7, 'F1': 5, 'F1#': 3, 'G1b': 3, 'G1': 6, 'G1#': 4, 'A1b': 4, 'A1': 2, 'A1#': 0, 'B1b': 0, 'B1': 7,
           'C2': 5, 'C2#': 3, 'D2b': 3, 'D2': 6, 'D2#': 4, 'E2b': 4, 'E2': 2, 'F2': 0, 'F2#': 3, 'G2b': 3, 'G2': 6, 'G2#': 4, 'A2b': 4, 'A2': 2, 'A2#': 0, 'B2b': 0, 'B2': 6,
           'C3': 4, 'C3#': 2, 'D3b': 2, 'D3': 0, 'D3#': 4, 'E3b': 4, 'E3': 2, 'F3': 0, 'F3#': 3, 'G3b': 3, 'G3': 6, 'G3#': 4, 'A3b': 4, 'A3': 2, 'A3#': 0, 'B3b': 0,
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
        name += '\n' + note + '\n?'

    name = name.replace('b',FLAT)
    name = name.replace('#',SHARP)

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


def count_alterations(all_notes):
    button_count = 0
    bend_count = 0
    overbend_count = 0
    impossibles_count = 0
    for note in all_notes:
        if (DRAWBEND1 in note) or (DRAWBEND2 in note) or (DRAWBEND3 in note) or (BLOWBEND1 in note) or (BLOWBEND2 in note):
            bend_count += 1
        if OVERBLOW in note:
            overbend_count += 1
        if "#" in note:
            button_count += 1
        if "?" in note:
            impossibles_count += 1
    return (button_count, bend_count, overbend_count, impossibles_count)


def fix_notes_split(input_list):
    output = list()
    for i in range(len(input_list)):
        string = input_list[i]
        if string.startswith(' ') or string.startswith('>') or (i == 0):
            output.append(string)
        else:
            output[-1] = output[-1] + 'note' + string
    return output


def add_text_to_notes(in_xml_file, out_xml_file='', mode=0, semitonesShift=0):
    try:
        with codecs.open(in_xml_file, "r", "utf-8") as fi:
            lines = fi.readlines()
    except Exception as e:
        err = str(e)
        warndlg('ERROR in opening file', f'ERROR: Error in MusicXML file!\nInput file may not be supported or wrong format selected')
        return [],[]

    single_line = ''.join(lines)
    splt = single_line.split('note')
    splt = fix_notes_split(splt)

    prev_note = None

    N = len(splt)
    all_notes = list()
    all_text = list()
    for i in range(N):
        string = splt[i]
        if 'pitch' in string:
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

            if mode == 0:
                new_text = note_to_text_heb(step, octave, alter)
            elif mode == 1:
                new_text = note_to_text_ChromaticHarmonica10(step, octave, alter, returnAllOptions=False)
            elif mode == 2:
                new_text = note_to_text_ChromaticHarmonica12(step, octave, alter, returnAllOptions=False)
            elif mode == 3:
                new_text = note_to_text_ChromaticHarmonica16(step, octave, alter, returnAllOptions=False)
            elif mode == 4:
                new_text = note_to_text_DiatonicHarmonicaC(step, octave, alter, 0)
            elif mode == 5:
                new_text = note_to_text_trumpet(step, octave, alter)
            elif mode == 6:
                new_text = note_to_text_baritone(step, octave, alter)
            elif mode == 7:
                new_text = note_to_text_tuba(step, octave, alter)
            elif mode == 8:
                new_text = note_to_text_english(step, octave, alter)
            else:
                warndlg('ERROR', 'Text mode not supported!')
            if '\n' in new_text:
                text = '[' + new_text.replace('\n',',') + ']'
                all_text.append(text)
            else:
                all_text.append(new_text)
            if '?' in new_text:
                string = string.replace('color="#000000"', 'color="#FF0000"')
            newstr = replace_text(string, new_text)
            if 'tie type="stop"' not in string or prev_note != current_note:  # don't write note text if this is a 'tie' to previous note, and previous note is identical
                splt[i] = newstr
            prev_note = current_note
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
    print(f'Alterations counts: (button, bend, overbend, impossible) = {count_alterations(all_notes)}')


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


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self)
        self.input_file = ''
        self.output_file = ''
        self.semitones_shift = 0
        self.initUI()

    def closeEvent(self, event):
        #print("User has clicked the red x on the main window")
        event.accept()


    def initUI(self):
        self.setWindowIcon(QIcon("google-earth-icon.png"))
        self.title = 'MusicXML Auto Annotator'
        self.version = 'v0.8'

        defaultGeometry = (600, 200, 900, 200)
        self.left, self.top, self.width, self.height = defaultGeometry
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        defaultDpi = 100
        btnHeight = 25
        btnWidth  = 70
        iconSize = btnHeight - 6
        titleWidth = 130
        bigBtnWidth = 250
        txtHeight = 19

        font1 = QFont()
        font1.setPointSize(defaultDpi / 10)
        font1red = QFont()
        font1red.setPointSize(defaultDpi / 10)
        #font1red.
        font2 = QFont()
        font2.setPointSize(defaultDpi / 10)
        font2.setUnderline(True)
        font = QFont()
        font.setPointSize(defaultDpi / 10)
        #font.setFamily("Courier New")

        self.input_file_title = QLabel('Input MusicXML File:')
        self.input_file_title.setFont(font1)
        self.input_file_title.setFixedWidth(titleWidth)
        self.input_file_edit = DndLineEdit(self)
        self.input_file_edit.setText(str(self.input_file))
        #self.input_file_edit.editingFinished.connect(self.input_file_changed)
        self.input_file_edit.setDropFcn(self.handleDropFileInput)
        #self.input_file_edit.returnPressed.connect(self.input_file_changed)
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

        self.text_mode_title = QLabel('Text Mode:')
        self.text_mode_title.setFont(font1)
        self.text_mode_title.setFixedWidth(titleWidth)
        self.text_mode_combo = QComboBox(self)
        items = ['Hebrew Names','Chromatic Harmonica 10','Chromatic Harmonica 12','Chromatic Harmonica 16','Diatonic Harmonica (C)', 'Trumpet+Hebrew', 'Baritone+Hebrew', 'Tuba+Hebrew', 'English+Hebrew']  # first one is the default one
        self.out_postfix = ['Hebrew','Chromatic10','Chromatic12','Chromatic16','DiatonicC','Trumpet','Baritone','Tuba','English']  # name extension for outfile
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

        self.summary1_title = QLabel('')
        self.summary1_title.setFont(font1)
        #self.summary1_title.setFixedHeight(txtHeight)
        self.summary1_text = QLabel('')
        self.summary1_text.setFont(font1)
        #self.summary1_text.setFixedHeight(txtHeight)

        self.summary2_title = QLabel('')
        self.summary2_title.setFont(font1)
        #self.summary2_title.setFixedHeight(txtHeight)
        self.summary2_text = QLabel('')
        self.summary2_text.setFont(font1red)
        #self.summary2_text.setFixedHeight(txtHeight)

        self.summary3_title = QLabel('')
        self.summary3_title.setFont(font1)
        #self.summary3_title.setFixedHeight(txtHeight)
        self.summary3_text = QLabel('')
        self.summary3_text.setFont(font1)
        #self.summary3_text.setFixedHeight(txtHeight)

        self.summary4_title = QLabel('')
        self.summary4_title.setFont(font1)
        #self.summary4_title.setFixedHeight(txtHeight)
        self.summary4_text = QLabel('')
        self.summary4_text.setFont(font1)
        #self.summary4_text.setFixedHeight(txtHeight)

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

        self.consoleViewer = QTextBrowser(self)
        self.consoleViewer.setReadOnly(True)
        self.consoleViewer.setMinimumWidth(300)
        self.consoleViewer.setMinimumHeight(200)
        #self.consoleViewer.resize(500,10)
        self.consoleViewer.setLineWrapMode(QTextBrowser.NoWrap)
        font3 = QFont()
        font3.setPointSize(defaultDpi / 10)
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
        grid.addWidget(self.options_title,      index, 0)

        index += 1
        grid.addWidget(self.summary0_title,     index, 0)

        index += 1
        grid.addWidget(self.summary1_title,     index, 0)
        grid.addWidget(self.summary1_text,      index, 1)

        index += 1
        grid.addWidget(self.summary2_title,     index, 0)
        grid.addWidget(self.summary2_text,      index, 1)

        index += 1
        grid.addWidget(self.summary3_title,     index, 0)
        grid.addWidget(self.summary3_text,      index, 1)

        index += 1
        grid.addWidget(self.summary4_title,     index, 0)
        grid.addWidget(self.summary4_text,      index, 1)

        index += 1
        grid.addWidget(self.consoleViewer, index, 0, 1, 4)

        index += 1
        grid.addWidget(self.run_btn,  index,    3, 1, 1)
        grid.addWidget(self.calc_btn,  index,   2, 1, 1)

        self.update_summary_titles()
        self.show()

    def combo_activated(self):
        sender = self.sender()  # this is the sender of this signal, i.e. the combo box
        if sender == self.text_mode_combo:
            self.text_mode_type = sender.currentText()
            self.auto_update_output_file()
            self.update_summary_titles()

    def update_summary_titles(self):
        self.summary1_title.setVisible(False)
        self.summary1_text.setVisible(False)
        self.summary2_title.setVisible(False)
        self.summary2_text.setVisible(False)
        self.summary3_title.setVisible(False)
        self.summary3_text.setVisible(False)
        self.summary4_title.setVisible(False)
        self.summary4_text.setVisible(False)
        if self.text_mode_combo.currentIndex() == 0:  # hebrew text
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText('')
            self.summary1_title.setVisible(True)
            self.summary1_text.setVisible(True)
        elif self.text_mode_combo.currentIndex() == 1:  # chromatic10
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText('')
            self.summary2_title.setText('- Button Count:')
            self.summary2_text.setText('')
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText('')
            self.summary1_title.setVisible(True)
            self.summary1_text.setVisible(True)
            self.summary2_title.setVisible(True)
            self.summary2_text.setVisible(True)
            self.summary4_title.setVisible(True)
            self.summary4_text.setVisible(True)
        elif self.text_mode_combo.currentIndex() == 2:  # chromatic12
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText('')
            self.summary2_title.setText('- Button Count:')
            self.summary2_text.setText('')
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText('')
            self.summary1_title.setVisible(True)
            self.summary1_text.setVisible(True)
            self.summary2_title.setVisible(True)
            self.summary2_text.setVisible(True)
            self.summary4_title.setVisible(True)
            self.summary4_text.setVisible(True)
        elif self.text_mode_combo.currentIndex() == 3:  # chromatic16
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText('')
            self.summary2_title.setText('- Button Count:')
            self.summary2_text.setText('')
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText('')
            self.summary1_title.setVisible(True)
            self.summary1_text.setVisible(True)
            self.summary2_title.setVisible(True)
            self.summary2_text.setVisible(True)
            self.summary4_title.setVisible(True)
            self.summary4_text.setVisible(True)
        elif self.text_mode_combo.currentIndex() == 4:  # diatonic-C
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText('')
            self.summary2_title.setText('- Bend Notes Count:')
            self.summary2_text.setText('')
            self.summary3_title.setText('- OverBlow Notes Count:')
            self.summary3_text.setText('')
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText('')
            self.summary1_title.setVisible(True)
            self.summary1_text.setVisible(True)
            self.summary2_title.setVisible(True)
            self.summary2_text.setVisible(True)
            self.summary3_title.setVisible(True)
            self.summary3_text.setVisible(True)
            self.summary4_title.setVisible(True)
            self.summary4_text.setVisible(True)
        elif self.text_mode_combo.currentIndex() == 5:  # trumpet text
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText('')
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText('')
            self.summary1_title.setVisible(True)
            self.summary1_text.setVisible(True)
            self.summary4_title.setVisible(True)
            self.summary4_text.setVisible(True)
        elif self.text_mode_combo.currentIndex() == 6 or self.text_mode_combo.currentIndex() == 7:  # baritone/tuba text
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText('')
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText('')
            self.summary1_title.setVisible(True)
            self.summary1_text.setVisible(True)
            self.summary4_title.setVisible(True)
            self.summary4_text.setVisible(True)
        elif self.text_mode_combo.currentIndex() == 8:  # English text
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText('')
            self.summary1_title.setVisible(True)
            self.summary1_text.setVisible(True)

    def input_file_changed(self,extText=''):
        sender = self.sender()
        text = sender.text()
        self.input_file = text
        #print(f'input_file = {text}')
        #self.update_gui_due_to_input_file_change('input')

    def output_file_changed(self):
        sender = self.sender()
        text = sender.text()
        self.output_file = text
        #print(f'output_file = {text}')
        #self.update_gui_due_to_input_file_change('')

    def semitones_shift_changed(self):
        sender = self.sender()
        text = sender.text()
        try:
            self.semitones_shift = int(text)
            self.auto_update_output_file()
        except Exception as e:
            err = str(e)
            warndlg('ERROR in Semitones value', f'ERROR: unsupported semitones value (empty string is not supported)')
            return

        #print(f'semitones_shift = {text}')
        #self.update_gui_due_to_input_file_change('')


    def handleDropFileInput(self,filepath):
        if os.path.isfile(filepath):  # given input is file, take the parent folder
            path, filename = os.path.split(filepath)
        self.input_file = filepath
        self.input_file_edit.setText(filepath)
        self.auto_update_output_file()
        #self.update_gui_due_to_input_file_change('input')


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
                                                 "MusicXML (*.xml)", options=options)

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
        #self.update_gui_due_to_input_file_change('input')

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
        self.output_file = self.output_file_edit.text()  # in case the user update the text box manually
        index = self.text_mode_combo.currentIndex()
        if saveOutput:
            all_notes,all_text = add_text_to_notes(self.input_file, self.output_file, index, self.semitones_shift)
        else:
            all_notes,all_text = add_text_to_notes(self.input_file, '', index, self.semitones_shift)
        self.consoleViewer.clear()
        self.consoleViewer.append('Notes:')
        self.consoleViewer.append(','.join(all_notes))
        self.consoleViewer.append('\nTexts:')
        self.consoleViewer.append(','.join(all_text))
        counts = count_alterations(all_text)
        (button_count, bend_count, overbend_count, impossibles_count) = counts
        button_count = str(button_count)
        bend_count = str(bend_count)
        overbend_count = str(overbend_count)
        impossibles_count = str(impossibles_count)
        total_count = str(len(all_text))
        #print(','.join(all_text))
        #print(f'Alterations counts: (button, bend, overbend, impossible) = {counts}')
        if self.text_mode_combo.currentIndex() == 0:  # hebrew text
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText(total_count)
        elif self.text_mode_combo.currentIndex() == 1:  # chromatic10
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText(total_count)
            self.summary2_title.setText('- Button Count:')
            self.summary2_text.setText(button_count)
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText(impossibles_count)
        elif self.text_mode_combo.currentIndex() == 2:  # chromatic12
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText(total_count)
            self.summary2_title.setText('- Button Count:')
            self.summary2_text.setText(button_count)
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText(impossibles_count)
        elif self.text_mode_combo.currentIndex() == 3:  # chromatic16
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText(total_count)
            self.summary2_title.setText('- Button Count:')
            self.summary2_text.setText(button_count)
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText(impossibles_count)
        elif self.text_mode_combo.currentIndex() == 4:  # diatonic-C
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText(total_count)
            self.summary2_title.setText('- Bend Notes Count:')
            self.summary2_text.setText(bend_count)
            self.summary3_title.setText('- OverBlow Notes Count:')
            self.summary3_text.setText(overbend_count)
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText(impossibles_count)
        elif self.text_mode_combo.currentIndex() == 5:  # trumpet text
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText(total_count)
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText(impossibles_count)
        elif self.text_mode_combo.currentIndex() == 6 or self.text_mode_combo.currentIndex() == 7:  # baritone/tuba text
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText(total_count)
            self.summary4_title.setText('- Impossible Notes Count:')
            self.summary4_text.setText(impossibles_count)
        elif self.text_mode_combo.currentIndex() == 8:  # english text
            self.summary1_title.setText('- Total Amount of Notes:')
            self.summary1_text.setText(total_count)

        if impossibles_count == '0':
            self.summary4_text.setStyleSheet("color: rgb(0,155,0)")
        else:
            self.summary4_text.setStyleSheet("color: rgb(255,0,0)")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())

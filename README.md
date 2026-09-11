# MusicXML-Annotator
MusicXML Automated Text Annotation (see screenshots at the bottom)

## How to install
Make sure you have Python 3.7 or higher installed and in your PATH.
Install Python dependencies by running:

    pip install -r requirements.txt

## How to use
Run by:

	python music_annotator.py

Load a MusicXML file by pressing the "Browse" button or Drag&Drop it to the input text box,
then choose the desired annotation.
The tool supports the following annotations, the name in brackets is the one used by the
`--text-mode` command line argument:

| # | Text Mode | name |
|---|-----------|------|
| 0 | Hebrew Note Names | `Hebrew` |
| 1 | Chromatic Harmonica - 10 holes | `Chromatic10` |
| 2 | Chromatic Harmonica - 12 holes | `Chromatic12` |
| 3 | Chromatic Harmonica - 16 holes | `Chromatic16` |
| 4 | Diatonic Harmonica (C) | `DiatonicC` |
| 5 | Trumpet | `Trumpet` |
| 6 | Baritone | `Baritone` |
| 7 | Tuba | `Tuba` |
| 8 | Recorder (Baroque Recorder) | `Recorder` |
| 9 | English+Hebrew Note Names | `English` |

Choose an output folder and file name (by default the output folder will be the same as the input folder,
and file name will append the annotation type and the semitones shift to the input file name).

Click the "Calc" button to check the annotation, see the text of each note and the summary on the screen.
Click the "Run" button to create the MusicXML file at the selected output folder.

### Choosing what gets annotated

**Semitones Shift** transposes the piece before it is annotated, to fit it to the instrument.
It is the value used when "Run" writes the output file.

**Instruments** chooses which staves get the annotations. If the file holds more than a single staff
(for example: the right hand and the left hand of a piano part, or several instruments), press the
"Select" button - or simply click the text box itself - to check the staves to annotate. Every staff of
every instrument is listed with its name and its amount of notes, and any combination of them can be
checked. Notes of a staff that is not checked are left untouched. By default all the staves are
annotated, and the selection is reset whenever a new input file is loaded.

**Measures** limits the annotation to a part of the piece. When a file is loaded the box is filled with
the whole range of the file (for example: 1-58), and it accepts a range like "3-8", a single measure
like "5", or a list like "1-4,9,12-16". Notes outside of the selected measures are left untouched.

### The summary
"Calc" fills a summary of what it takes to play the piece. Every mode shows the total amount of notes,
and the modes that cannot play every note also show how many notes they cannot play at all (those are
the notes marked with "?" in the output, shown in red).

The Chromatic Harmonica modes add the amount of notes that need the button (the slide).

The Diatonic Harmonica breaks its notes down by the way each one is played, so that the effort is
visible before playing a single note:

- 0.5 / 1.0 / 1.5 Draw Bend Count
- 0.5 / 1.0 Blow Bend Count
- OverBlow Count
- OverDraw Count

### The semitones shifts table
For the Harmonica text modes, "Calc" does not calculate only the selected semitones shift: it shows a
table of all those counters for every semitones shift between -12 and +12, one column per shift, so
that the best key can be chosen at a glance. The column of the "Semitones Shift" value is highlighted,
and that value is still the only one used when "Run" writes the output file.

For the Diatonic Harmonica the table also holds an **Average Difficulty** row: every note is given a
difficulty according to the way it is played (0 for a plain blow or draw note, 1 for a half step draw
bend, up to 6 for an overdraw), and the row shows the average over the notes that can be played.
The notes that are not on the harmonica at all are not part of it - they are not hard to play, they
cannot be played - so read that row together with the "Impossible Notes Count" row right below it.

The easiest shift is marked in green. It is looked for only among the shifts that can play every note
of the piece, so that a shift that is "easy" only because most of the piece dropped out of it is never
suggested; when no shift can play the whole piece, nothing is marked.

The weights live in the `DIATONIC_DIFFICULTY` dictionary at the top of `music_annotator.py`, tune them
to your own playing.

## Command line
The GUI can also be opened directly on a file, with the "Calc" operation already done, by giving its
settings on the command line. Every argument is optional, without any of them the GUI just opens empty:

	python music_annotator.py song.xml -t DiatonicC -s 3 -i 1,2 -m 5-11

| argument | meaning |
|----------|---------|
| `input_file` | the MusicXML file to load (.xml or .musicxml) |
| `-t`, `--text-mode` | the annotation, by name (`Hebrew`, `Chromatic10`, `Chromatic12`, `Chromatic16`, `DiatonicC`, `Trumpet`, `Baritone`, `Tuba`, `Recorder`, `English`) or by its index (0-9) |
| `-s`, `--semitones` | semitones shift, a whole number, for example: `-3` |
| `-i`, `--instruments` | 1 based indexes of the staves to annotate, for example: `1,2` - in the order they are listed in the "Instruments" dialog (default: all of them) |
| `-m`, `--measures` | measures to annotate, for example: `5-11` or `3` or `1-4,9,12-16` (default: all of them) |
| `-h`, `--help` | print the arguments and exit |

The output file name is filled in, but the output file itself is still written only when the "Run"
button is pressed.

## Notes
The tool reads both `.xml` and `.musicxml` files, but it does not support compressed MusicXML files
(`.mxl`).

To render the output MusicXML as music sheet pages you can import the output MusicXML file into note sheet application (for example in *[MuseScore3](https://musescore.org/en)* you can do that by drag&drop).
To render the arrows on the Diatonica harmonica annotations correctly use the provided Font: HarmonicaArrows.ttf.
Install the font on your system and then choose the app to use it. 
On MuseScore3 the font for the lyrics is selected on this menu:

	Format > Style...
	"Text Styles" > "Lyrics Odd Lines" > Font > HarmonicaArrows.ttf
![Tux, the GUI](/screenshots/screenshot-font.png)

## Screenshots
The GUI:
![Tux, the GUI](/screenshots/screenshot-gui.png)

Input example - clean notes (no annotations):
![Tux, notes example](/screenshots/screenshot-clean.png)

Output example - Diatonic Harmonica (similar to Tomlin's style):
![Tux, Diatonic Harmonica Annotations](/screenshots/screenshot-dharmonica.png)

Output example - Trumpet buttons (notes that are not playable on the Trumpet are marked with "?"):
![Tux, Trumpet Annotations](/screenshots/screenshot-trumpet.png)

Output example - Recorder holes (notes that are not playable on the Recorder are marked with "?"):
![Tux, Recorder Annotations](/screenshots/screenshot-recorder.png)

Output example - English+Hebrew note names:
![Tux, Hebrew+English Annotations](/screenshots/screenshot-eng.png)

# MusicXML-Annotator
MusicXML Automated Text Annotation (see screenshots at the bottom)

## How to install
Make sure you have Python 3.7 or higher installed and in your PATH.
Install Python dependencies by running:

    pip install -r requirements.txt

## How to use
Run by:

	python music_annotator.py

Load MusicXML file by pressing "BROWSE" button or Drag&Drop to the input text box,
then choose the desired annotations.
The tool supports the following annotations: 
- Diatonic Harmonica
- Chromatic Harmonics - 10 holes
- Chromatic Harmonics - 12 holes
- Chromatic Harmonics - 16 holes
- Trumpet
- Tuba
- Baritone
- Recorder (Baroque Recorder)
- Hebrew Note Names
- English+Hebrew Note Names

If the file holds more than a single staff (for example: the right hand and the left hand of a piano part,
or several instruments), press the "Select" button next to "Instruments" to choose which staves will be annotated.
Every staff of every instrument is listed with its name and its amount of notes, and any combination of them can
be checked. By default all the staves are annotated, and the selection is reset whenever a new input file is loaded.

The "Measures" text box limits the annotation to a part of the piece. When a file is loaded it is filled with the
whole range of the file (for example: 1-58), and it accepts a range like "3-8", a single measure like "5", or a
list like "1-4,9,12-16". Notes outside of the selected measures are left untouched.

Choose an output folder and file name (by default the output folder will be the same as the input folder,
and file name will append the annotation type to the input .xml file) 

Click the "Calc" button to check the annotation and see the text for each note on the screen.
Click the "Run" button to create the MusicXML file at the selected output folder.

For the Harmonica text modes, "Calc" shows a table of the counters (bends, overblows, impossible notes, ...)
for every semitones shift between -12 and +12, one column per shift, so that the best key can be chosen at a
glance. The column of the "Semitones Shift" value is highlighted, and that value is still the only one used
when "Run" writes the output file.

Note that the tool doesn't supports compressed MusicXML files.

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

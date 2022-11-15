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

Choose an output folder and file name (by default the output folder will be the same as the input folder,
and file name will append the annotation type to the input .xml file) 

Click the "Calc" button to check the annotation and see the text for each note on the screen.
Click the "Run" button to create the MusicXML file at the selected output folder.

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

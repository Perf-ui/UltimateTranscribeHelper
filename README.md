# Ultimate Transcribe Helper

Ultimate Transcribe Helper is a Windows desktop application for turning music
recordings into MIDI and other editable outputs. It builds on
[Omnizart](https://github.com/Music-and-Culture-Technology-Lab/omnizart) and
adds a graphical interface, additional transcription models, audio separation
and score-export tools.

## Features

- Transcribe pitched instruments, voice, chords and drums; beat tracking uses
  MIDI input. Available outputs depend on the selected mode and include MIDI,
  CSV and, for vocal pitch contour, WAV.
- Choose between Omnizart models and additional models such as Basic Pitch and
  Transkun. Other models can be installed or downloaded separately; see
  [optional models](docs/OPTIONAL_MODELS.md) and the
  [model inventory](docs/WINDOWS_MODELS.md).
- Reduce vocals or separate audio stems using supported models. Optional
  DirectML acceleration is available for supported separation models.
- Create an editable MusicXML score from MIDI, optionally render a PDF with a
  separate MuseScore 4 installation, and generate note-review reports or
  cleaned MIDI copies.

Transcription and notation are estimates and may require manual correction.
Optional components and model downloads can require an internet connection;
see the model documentation for their requirements and terms.

## Windows application

The repository contains the application source, not a ready-to-run Windows
installation. The Windows package requires a prepared 64-bit Python 3.11
runtime, native dependencies and model files. Recreating that environment on
a clean machine is not yet automated or verified.

Clone this repository with:

```powershell
git clone https://github.com/TomOdellSheetMusic/UltimateTranscribeHelper.git
cd UltimateTranscribeHelper
```

For prerequisites, model files and packaging commands, read the
[Windows build instructions](scripts/windows/BUILDING.md). After building a
portable package, launch `Omnizart.vbs` inside the package. The
[Windows user guide](scripts/windows/README.txt) describes the interface and
its options.

## Omnizart command line

The original Omnizart command-line interface is retained in this source tree.
Once its dependencies and checkpoints are installed, examples include:

```text
omnizart drum transcribe <path/to/audio.wav>
omnizart chord transcribe <path/to/audio.wav>
omnizart music transcribe <path/to/audio.wav>
```

The upstream [Omnizart documentation](https://music-and-culture-technology-lab.github.io/omnizart-doc/)
covers its library and command-line tools. Installing the upstream PyPI or
Docker package does not install this repository's Windows desktop additions.

## Licences and distribution

The original project licence and copyright notice are in [LICENSE](LICENSE).
Third-party code, dependencies and model weights may have separate terms; the
project's MIT licence does not automatically establish the licence of each
model. The NNLS Chroma plugin is GPL-2.0-or-later; see its
[licence and build information](omnizart/resource/vamp/BUILD.md).

The [Windows model and rights inventory](docs/WINDOWS_MODELS.md) records
known terms and unresolved questions. In particular, madmom's bundled model
files have noncommercial terms, and redistribution rights for several other
weights have not been confirmed. Review and resolve the applicable model,
dependency, notice and source obligations before distributing a build; see
the [release checklist](docs/WINDOWS_RELEASE_CHECKLIST.md).

## Attribution

This project builds on Omnizart by the Music and Culture Technology Lab. If
you use Omnizart in research, cite its [JOSS paper](https://doi.org/10.21105/joss.03391).
Further third-party notices are included alongside the relevant components and
in the model inventory.

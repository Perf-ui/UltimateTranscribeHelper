# Optional transcription models

The desktop application can use YourMT3 and MuScriptor as additional
transcribers. Their code and checkpoints are not bundled with Omnizart. Install
the appropriate package in the Python environment used to run Omnizart, then
select the model in the model list.

## YourMT3

Install the PyTorch backend:

```powershell
python -m pip install "mt3-infer[torch] @ git+https://github.com/openmirlab/mt3-infer.git"
```

The first transcription downloads the YourMT3 checkpoint (about 536 MB) into
the backend's cache. YourMT3 targets multi-instrument recordings and can emit
several instrument tracks. The integration uses the `mt3-infer` API when
installed in Omnizart's Python and its `mt3-infer` command when available on
PATH. The weights are published under Apache-2.0 terms; review the upstream
project's per-component notices before redistributing a build.

## MuScriptor

Install the package:

```powershell
python -m pip install muscriptor
```

Before first use, sign in to Hugging Face and accept the model terms on the
official model page. MuScriptor downloads model weights on first use. The
weights are licensed CC BY-NC 4.0, so they are limited to non-commercial use.
Its software is MIT licensed. The app selects MuScriptor's MIDI output; the
normal Omnizart score export can then format that MIDI through MuseScore.

Use Python 3.10–3.12 for MuScriptor. The model's `small` variant is intended
for CPU use; larger variants need more memory and benefit from a GPU. Consult
the official project documentation for model selection and Hugging Face
authentication steps.

## Score output

When **Format score and export MusicXML + PDF** is selected and MuseScore 4 is
configured, Omnizart converts the final MIDI to MusicXML, adds A4 page and
system layout settings, and applies grand-staff notation for piano models.
MuseScore then engraves a PDF from that MusicXML. Quantization is applied to a
temporary MIDI used for score creation only; the original MIDI is unchanged.
Automatic note transcription and layout are drafts: inspect enharmonic spelling,
bar divisions, ties, pedal markings, dynamics, and instrument assignment in
MuseScore before publication or performance.

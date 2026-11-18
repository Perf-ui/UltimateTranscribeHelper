# Optional transcription models

The desktop application can use YourMT3 and MuScriptor as additional
transcribers. Their packages are installed automatically the first time each
model is selected. YourMT3 downloads its weights on first use. MuScriptor's
gated weights must be downloaded manually after accepting Hugging Face's terms.

## YourMT3

The first transcription downloads the YourMT3 checkpoint (about 536 MB) into
the backend's cache. YourMT3 targets multi-instrument recordings and can emit
several instrument tracks. The integration runs `mt3-infer` in a separate
Python environment. Its checkpoint download currently requires Git and Git LFS
on PATH. The weights are published under Apache-2.0 terms; review the upstream
project's per-component notices before redistributing a build.

## MuScriptor

In **Models & import**, open the official [MuScriptor small model page](https://huggingface.co/MuScriptor/muscriptor-small),
accept its access terms, and download both `model.safetensors` and `config.json` from the Files tab. Save them in the
folder shown there using **Open MuScriptor folder**. The app loads these local
files; it does not download the gated weights itself. The weights are licensed
CC BY-NC 4.0, so they are limited to non-commercial use. Its software is MIT
licensed. The app selects MuScriptor's MIDI output; the normal Omnizart score
export can then format that MIDI through MuseScore.

Use Python 3.10–3.12 for MuScriptor. The model's `small` variant is intended
for CPU use; larger variants need more memory and benefit from a GPU. Consult
the official project documentation for model selection and Hugging Face
authentication steps.

## Score output

Select **Create formatted MusicXML score** to create an editable score directly
from the MIDI. No MuseScore installation is required. Omnizart estimates the
tempo from note attacks, quantizes a score-only copy to sixteenth notes, assigns
overlapping notes to separate voices, and uses a grand staff for piano models.
Enter a BPM instead of Auto when the estimate is wrong. The original MIDI is
not changed. A separately installed MuseScore 4 can optionally render a PDF.

The score is a draft: automatic tempo, beat alignment, hand assignment, pitch
spelling, durations and ties may need editing. Percussion tracks are omitted
from MusicXML but remain in the MIDI. Time-signature changes are not yet supported. Dense piano passages may need
extra ties, and passages that exceed a hand span or five held notes are flagged
for review. Score export does not alter the MIDI.

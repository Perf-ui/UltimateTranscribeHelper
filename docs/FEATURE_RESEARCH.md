# MIDI cleanup and transcription projects

Research notes, 2026-11-17. The external projects are integration candidates;
their model quality and licence compatibility have not been validated.

## Piano MIDI Cleanup

[Project and English README](https://github.com/hibikiwtnb/piano-midi-cleanup/blob/main/README_EN.md).
Relevant features include conservative removal of suspect notes, tempo and
first-beat alignment, hand assignment, sustain-overlap trimming, and piano-roll
inspection. It also has a piano-isolation and transcription workflow. Its
cleanup is tuned for ByteDance piano transcription, so applying it to Transkun
or to vocal tracks needs evaluation, not an assumption that defaults transfer.

The project code is AGPL-3.0-only. Directly incorporating its implementation
would bring corresponding licensing obligations; review compatibility and
distribution terms before adopting code. Model weights and third-party
components have separate terms. The README lists ByteDance's checkpoint as
CC BY 4.0 and its separation weights as separately downloaded.

## Music to MIDI

[Project](https://github.com/mason369/music-to-midi) and
[English README](https://github.com/mason369/music-to-midi/blob/master/docs/README.md).
It supports multiple piano transcription backends, multistem workflows, tempo
maps and quantization. Its source is MIT; its
[third-party inventory](https://github.com/mason369/music-to-midi/blob/master/THIRD_PARTY_NOTICES.md)
documents model and dependency terms separately, including some weights with
undeclared rights. Candidate ideas: compare the pedal-aware ByteDance model
and evaluate additional piano models; provide an adjustable tempo/quantization
option. Actual integration requires dependency, hardware, provenance and
accuracy testing for each selected model.

## Oh Sheet

[Project](https://github.com/Oh-Sheet-Team/oh-sheet) provides piano-hand
arrangement, notation and expressive playback, and uses Basic Pitch, which
Omnizart already includes. Its root [licence](https://github.com/Oh-Sheet-Team/oh-sheet/blob/main/LICENSE.txt)
is MIT; `pyproject.toml` also labels the backend package proprietary, so clarify
the scope before copying code. Some components and models have separate terms.
Its web/service architecture and notation stack would need adaptation for a
local Windows application. Two-hand arrangement and score export are later
features, not a shortcut to improved transcription accuracy.

The [transcription dispatcher](https://github.com/Oh-Sheet-Team/oh-sheet/blob/main/backend/services/transcribe.py)
has several paths: optional Demucs four-stem separation followed by Basic
Pitch per stem; Kong/ByteDance pedal-aware piano inference on a piano-like
stem; and a single-mix Basic Pitch fallback. Our Basic Pitch and optional UVR
two-stem separation already overlap with the first idea, and our optional
Pedal Piano adapter uses the same Kong inference package. We have not tested
our adapter with its actual checkpoint, and have not compared accuracy against
Oh Sheet. Demucs may improve isolation on some mixes but can remove or distort
notes, costs additional resources, and its model licences require review.

The optional [AMT-APC path](https://github.com/Oh-Sheet-Team/oh-sheet/blob/main/backend/services/transcribe_amt_apc.py)
generates a piano cover arrangement, which is a different target from recovering
the original played notes. The [upstream project](https://github.com/310hz/amt-apc)
distributes a checkpoint and command-line inference; verify its actual API,
checkpoint terms and Windows CPU/GPU behavior before proposing integration.
Oh Sheet also describes cleanup for fragmented sustains and likely octave or
tail artifacts. Those heuristics can discard real notes, so evaluate them
against reference MIDI before adding independent, optional controls.

Other useful candidates are an interactive piano roll, existing-MIDI import,
editable hand assignment, MusicXML/PDF export, and playback. Prioritize these
by user needs and assess any extra dependencies and licence obligations.

## First feature: optional MIDI cleanup

The independently implemented first pass merges nearby same-pitch fragments on
the same track when at least one is 120 ms or shorter. It writes a separate
MIDI, is off by default, and exposes a maximum gap in milliseconds. It skips
vocal tracks, percussion, ambiguous overlapping notes and passages with pedal
or pitch-bend activity; it retains tempo, control and other MIDI messages.
It may still merge intentional repeated notes, so compare the original.
On the 25-second Mona piano preview, the default 30 ms setting joined zero
fragments: it is not yet established that this improves that recording.

An independent, off-by-default short-note filter is also available with its own
duration control. It removes notes only in unprotected passages, and can still
remove real fast notes. Merging runs first when both options are selected. The
default 40 ms filter also removed zero notes from the Mona piano preview because
its short notes occurred in protected passages. These controls are conservative
and their usefulness needs evaluation on more examples.
Quantization, velocity smoothing, pedal-tail trimming and hand assignment are
different operations and should be separately selectable, not hidden behind a
single irreversible slider. Compare on real recordings and MIDI with known
notes; a more regular-looking result does not necessarily mean greater accuracy.

# Test report: Windows portable build, 2026-11-18

## Scope and build

The application source was commit `a3ac4b9`, which combines YourMT3
predictions into a single piano track when six-stem piano isolation is
selected. The original YourMT3 multitrack MIDI is retained separately. The
portable build was assembled with `scripts/windows/build_portable.py` and the
existing `.runtime311` environment. Its dependency substitutions and provenance
are recorded in `LOCAL-BUILD-NOTES.md` within the local build. No installer was
built because Inno Setup was unavailable.

## Results

- `python -m pip check`: passed in both the source and portable runtimes.
- `python -m unittest discover -s tests -p 'test_*.py' -v`: 113 test entries,
  including 103 successful unittest cases and 10 module import errors because
  `pytest` is absent. This is not a complete pytest run; pytest-style functions
  and parametrized tests were not executed. The previous stale DirectML error
  assertion was corrected before this run.
- Targeted notation, desktop command, beat grid, comparison and separation CLI
  suite: 44 tests passed before the final extension to the YourMT3 regression.
  The extended regression subsequently passed separately, including creation of
  a single piano MIDI, preservation of the original multitrack MIDI and MusicXML
  export. Six-stem separation and YourMT3 inference were mocked in this test.
- Portable GUI transcription smoke test: passed using the Piano model and the
  bundled test audio; the generated MIDI contained notes. This does not test
  YourMT3 or six-stem inference.

## Limitations

A request to install `pytest` and `pytest-mock` was not executed because the
sandbox's automatic approval review reported a usage limit. Six-stem model
weights and the optional YourMT3 runtime were not installed, so their real
combined inference was not tested. GPU inference, fresh installation, upgrades
and uninstallation were not tested. The single-piano output merges predicted
notes and does not establish that every note represents a piano sound.

Adaptive rhythm and tuplets, a score editor, a curated reference set and a real
DuET/PM2S comparison remain unimplemented. These tests therefore do not establish
that all concepts discussed for score quality are complete or that a generated
score is correct or playable.

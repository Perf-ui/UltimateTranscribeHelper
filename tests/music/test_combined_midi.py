"""The combined output keeps instrument and vocal notes in separate tracks."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pretty_midi
from omnizart.desktop.combined import merge_tracks


class CombinedMidiTests(unittest.TestCase):
    def test_combines_tracks_and_preserves_note_timing(self):
        with TemporaryDirectory() as temp:
            piano_path = Path(temp) / "piano.mid"
            result_path = Path(temp) / "combined.mid"
            piano = pretty_midi.PrettyMIDI()
            piano_track = pretty_midi.Instrument(0, name="Piano")
            piano_track.notes.append(pretty_midi.Note(90, 60, 0.5, 1.0))
            piano.instruments.append(piano_track)
            piano.write(str(piano_path))
            voice = pretty_midi.PrettyMIDI()
            voice_track = pretty_midi.Instrument(0)
            voice_track.notes.append(pretty_midi.Note(80, 69, 1.5, 2.0))
            voice.instruments.append(voice_track)
            merge_tracks(piano_path, voice, result_path)
            result = pretty_midi.PrettyMIDI(str(result_path))
            self.assertEqual([track.name for track in result.instruments], ["Piano", "Vocals"])
            self.assertAlmostEqual(result.instruments[1].notes[0].start, 1.5, places=2)

    def test_no_vocal_notes_is_reported(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "piano.mid"
            pretty_midi.PrettyMIDI().write(str(path))
            with self.assertRaisesRegex(ValueError, "No pitched vocal notes"):
                merge_tracks(path, pretty_midi.PrettyMIDI(), Path(temp) / "output.mid")


if __name__ == "__main__":
    unittest.main()

"""Verify that the desktop can distinguish empty MIDI files from notes."""
import logging
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import mido

from omnizart.desktop.app import (midi_note_count, music_options, validate_model_folder, reserve_result_name,
                                  remember_imported_model, read_imported_model, read_imported_models, imported_model_label)
from omnizart.desktop.worker import _HideTensorFlowDeprecations


class DesktopResultTests(unittest.TestCase):
    def test_multiple_imports_preserve_legacy_model_and_disambiguate_names(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = root / "one" / "piano"
            second = root / "two" / "piano"
            for model in (first, second):
                (model / "variables").mkdir(parents=True)
                (model / "saved_model.pb").touch()
                (model / "configurations.yaml").touch()
                (model / "variables" / "variables.index").touch()
                (model / "variables" / "variables.data-00000-of-00001").touch()
            with patch.dict("os.environ", {"LOCALAPPDATA": str(root)}):
                settings = root / "Omnizart" / "custom-model.json"
                settings.parent.mkdir()
                settings.write_text('{"checkpoint": ' + __import__("json").dumps(str(first)) + '}', encoding="utf-8")
                remember_imported_model(second)
                self.assertEqual(read_imported_models(), [str(first), str(second)])
                self.assertEqual(read_imported_model(), str(second))
                self.assertNotEqual(imported_model_label(first), imported_model_label(second))
    def test_repeated_runs_reserve_distinct_names_in_one_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / "song.mid").write_bytes(b"old")
            (directory / "song_2_f0.csv").write_bytes(b"old contour")
            first, lock = reserve_result_name(directory, "song")
            self.assertEqual(first.name, "song_3")
            second, second_lock = reserve_result_name(directory, "song")
            self.assertEqual(second.name, "song_4")
            lock.unlink()
            second_lock.unlink()
            self.assertEqual((directory / "song.mid").read_bytes(), b"old")
            self.assertEqual((directory / "song_2_f0.csv").read_bytes(), b"old contour")
            (directory / "song_3").mkdir()
            third, third_lock = reserve_result_name(directory, "song")
            self.assertEqual(third.name, "song_4")
            third_lock.unlink()

    def test_note_count_is_for_current_run_only(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            midi = mido.MidiFile()
            midi.tracks.append(mido.MidiTrack([mido.Message("note_on", note=60, velocity=80)]))
            midi.save(directory / "song.mid")
            empty = mido.MidiFile()
            empty.tracks.append(mido.MidiTrack())
            empty.save(directory / "song_2.mid")
            self.assertEqual(midi_note_count(directory, directory / "song_2"), 0)
            self.assertIsNone(midi_note_count(directory, directory / "song_3"))

    def test_midi_like_stems_do_not_change_backend_output_path(self):
        with tempfile.TemporaryDirectory() as folder:
            base, lock = reserve_result_name(folder, "mix.mid")
            self.assertEqual(base.name, "mix.mid_result")
            lock.unlink()

    def test_import_requires_a_complete_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertFalse(validate_model_folder(root))
            (root / "saved_model.pb").touch()
            (root / "configurations.yaml").touch()
            (root / "variables").mkdir()
            (root / "variables" / "variables.index").touch()
            self.assertFalse(validate_model_folder(root))
            (root / "variables" / "variables.data-00000-of-00001").touch()
            self.assertTrue(validate_model_folder(root))
            with patch.dict("os.environ", {"LOCALAPPDATA": str(root)}):
                remember_imported_model(root)
                self.assertEqual(read_imported_model(), str(root))
    def test_music_thresholds_are_optional_and_validated(self):
        self.assertEqual(music_options({"onset": "", "duration": "", "instrument": ""}), [])
        self.assertEqual(music_options({"onset": "3.5", "duration": "", "instrument": "0.1"}),
                         ["--onset-th", "3.5", "--instrument-th", "0.1"])
        self.assertEqual(music_options({"onset": "0.4", "duration": "0.2", "instrument": "80"}, "Basic Pitch"),
                         ["--onset-th", "0.4", "--frame-th", "0.2", "--minimum-note-ms", "80.0"])
        self.assertEqual(music_options({"onset": "4", "duration": "0.5", "instrument": ""},
                                       "Transkun (piano)"), [])
        with self.assertRaises(ValueError):
            music_options({"onset": "4", "duration": "", "instrument": ""}, "Basic Pitch")
        for invalid in ("NaN", "-1", "21", "not a number"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                music_options({"onset": invalid, "duration": "", "instrument": ""})

    def test_empty_and_nonempty_midi(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            self.assertIsNone(midi_note_count(directory))
            midi = mido.MidiFile()
            track = mido.MidiTrack()
            midi.tracks.append(track)
            track.append(mido.Message("note_on", note=60, velocity=0))
            midi.save(directory / "result.mid")
            self.assertEqual(midi_note_count(directory), 0)
            track.append(mido.Message("note_on", note=60, velocity=80))
            midi.save(directory / "result.mid")
            self.assertEqual(midi_note_count(directory), 1)
            midi.save(directory / "result_smoothed.mid")
            self.assertEqual(midi_note_count(directory), 1)

    def test_tensorflow_filter_preserves_other_warnings(self):
        filter_ = _HideTensorFlowDeprecations()
        def record(level, message):
            return logging.LogRecord("tensorflow", level, "", 1, message, (), None)
        self.assertFalse(filter_.filter(record(logging.WARNING, "This API is deprecated")))
        self.assertTrue(filter_.filter(record(logging.WARNING, "Model may not load")))
        self.assertTrue(filter_.filter(record(logging.ERROR, "Deprecated API failed")))


if __name__ == "__main__":
    unittest.main()

"""Verify MuseScore subprocess handling without launching the application."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import mido
from omnizart.desktop.score_export import export_musicxml, quantize_score_input


class ScoreTests(unittest.TestCase):
    def test_conversion_checks_xml_and_does_not_replace_original(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            executable, source, destination = root / 'MuseScore4.exe', root / 'song.mid', root / 'song.musicxml'
            executable.touch()
            source.write_bytes(b'original')
            def run(args, **kwargs):
                Path(args[-1]).write_text('<score-partwise version="4.0"/>', encoding='utf-8')
                return SimpleNamespace(returncode=0, stdout='')
            with patch('omnizart.desktop.score_export.subprocess.run', side_effect=run):
                export_musicxml(source, destination, executable)
                with self.assertRaises(FileExistsError):
                    export_musicxml(source, destination, executable)
            self.assertEqual(source.read_bytes(), b'original')
            self.assertIn('score-partwise', destination.read_text())

    def test_score_quantization_keeps_original_and_non_note_events(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source, output = root / 'original.mid', root / 'grid.mid'
            midi = mido.MidiFile(ticks_per_beat=480)
            midi.tracks.append(mido.MidiTrack([
                mido.MetaMessage('set_tempo', tempo=750000),
                mido.Message('control_change', control=64, value=127, time=40),
                mido.Message('note_on', note=60, velocity=74, time=23),
                mido.Message('note_off', note=60, time=30),
                mido.Message('control_change', control=64, value=0, time=40)]))
            midi.save(source)
            original = source.read_bytes()
            quantize_score_input(source, output, 16)
            self.assertEqual(source.read_bytes(), original)
            events, tick = [], 0
            for message in mido.MidiFile(output).tracks[0]:
                tick += message.time
                events.append((tick, message))
            notes = [(time, msg.type, msg.velocity) for time, msg in events if msg.type in ('note_on', 'note_off')]
            self.assertEqual(notes, [(120, 'note_on', 74), (240, 'note_off', 64)])
            controls = [(time, msg.value) for time, msg in events if msg.type == 'control_change']
            self.assertEqual(controls, [(40, 127), (133, 0)])
            self.assertEqual(next(msg.tempo for _, msg in events if msg.type == 'set_tempo'), 750000)

    def test_invalid_output_is_rejected(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            executable = root / 'MuseScore4.exe'
            executable.touch()
            def run(args, **kwargs):
                Path(args[-1]).write_text('<wrong/>', encoding='utf-8')
                return SimpleNamespace(returncode=0, stdout='')
            with patch('omnizart.desktop.score_export.subprocess.run', side_effect=run):
                with self.assertRaises(RuntimeError):
                    export_musicxml(root / 'in.mid', root / 'out.musicxml', executable)
            self.assertFalse((root / 'out.musicxml').exists())

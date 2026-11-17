"""Review reports identify likely issues without changing the source."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import mido
from click.testing import CliRunner
from unittest.mock import patch
from omnizart.desktop.lint import write_report
from omnizart.cli.music.transcribe import transcribe


class ReviewTests(unittest.TestCase):
    def test_report_uses_tempo_and_preserves_midi(self):
        with TemporaryDirectory() as folder:
            source, report = Path(folder) / 'song.mid', Path(folder) / 'review.txt'
            midi = mido.MidiFile(ticks_per_beat=480)
            midi.tracks.append(mido.MidiTrack([mido.MetaMessage('set_tempo', tempo=1000000)]))
            midi.tracks.append(mido.MidiTrack([mido.MetaMessage('track_name', name='Piano'),
                mido.Message('note_on', note=60, velocity=80, time=480),
                mido.Message('note_on', note=60, velocity=80, time=5),
                mido.Message('note_off', note=60, time=5),
                mido.Message('note_off', note=60, time=480)]))
            midi.save(source)
            original = source.read_bytes()
            self.assertEqual(write_report(source, report), 2)
            text = report.read_text(encoding='utf-8')
            self.assertIn('00:01.000', text)
            self.assertIn('Piano', text)
            self.assertIn('Overlapping', text)
            self.assertEqual(source.read_bytes(), original)
            with self.assertRaises(FileExistsError):
                write_report(source, report)

    def test_cli_report_is_optional_and_created_from_output(self):
        with TemporaryDirectory() as folder:
            folder = Path(folder)
            audio = folder / 'song.wav'
            audio.touch()
            def create_midi(*args):
                midi = mido.MidiFile()
                midi.tracks.append(mido.MidiTrack())
                midi.save(folder / 'result.mid')
            with patch('omnizart.cli.music.transcribe._transcribe', side_effect=create_midi):
                result = CliRunner().invoke(transcribe, [str(audio), '--output', str(folder / 'result'), '--lint-notes'])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn('0 possible issues', (folder / 'result_review.txt').read_text(encoding='utf-8'))

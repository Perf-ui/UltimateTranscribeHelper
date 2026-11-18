"""Isolated audio beat tracker interface."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from omnizart.desktop import beat_alignment


class BeatAlignmentTests(unittest.TestCase):
    def test_reads_tracker_output(self):
        def run(command, **kwargs):
            Path(command[-1]).write_text('{"beats": [0.5, 1.0], "downbeats": [0.5]}', encoding='utf-8')
            return SimpleNamespace(returncode=0, stdout='')
        with patch.object(beat_alignment, 'ready', return_value=True), patch.object(beat_alignment, 'environment', return_value=Path('.')), patch.object(beat_alignment, 'python_path', return_value=Path('python')), patch.object(beat_alignment.subprocess, 'run', side_effect=run):
            self.assertEqual(beat_alignment.detect('audio.wav'), ([.5, 1.0], [.5]))

    def test_reports_tracker_failure(self):
        with patch.object(beat_alignment, 'ready', return_value=True), patch.object(beat_alignment, 'environment', return_value=Path('.')), patch.object(beat_alignment, 'python_path', return_value=Path('python')), patch.object(beat_alignment.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout='bad audio')):
            with self.assertRaisesRegex(RuntimeError, 'bad audio'):
                beat_alignment.detect('audio.wav')


if __name__ == '__main__':
    unittest.main()

"""Exercise score export command construction without a GUI display."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from omnizart.desktop.app import Application


def var(value):
    return SimpleNamespace(get=lambda: value)


class ScoreButtonTests(unittest.TestCase):
    def test_musicxml_needs_no_musescore(self):
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            source = folder / 'song.wav'
            source.touch()
            app = SimpleNamespace(
                source=var(str(source)), destination=var(str(folder)), mode=var('Piano and instruments'),
                music_model=var('Piano'), custom_models={}, custom_model_path=None,
                thresholds={key: var('') for key in ('onset', 'duration', 'instrument')},
                piano_only=var(False), remove_vocals=var(False), include_vocals=var(False),
                separator_model=var('UVR MDX (recommended)'), use_gpu=var(False), gpu_index=var('0'),
                smooth_notes=var(False), remove_short_notes=var(False), compare_enabled=var(False),
                musescore_export=var(True), score_tempo=var('154'), pdf_export=var(False),
                musescore_path=var(''), lint_notes=var(False), save_folders=Mock(),
                log=Mock(), start_button=Mock(), open_button=Mock(), progress=Mock(), status=Mock(),
                run=Mock())
            with patch('omnizart.desktop.app.threading.Thread') as thread:
                Application.start(app)
            cmd = thread.call_args.kwargs['args'][0]
            self.assertIn('--score', cmd)
            self.assertEqual(cmd[cmd.index('--score-tempo') + 1], '154')
            self.assertNotIn('--musescore', cmd)
            app.output_lock.unlink()


if __name__ == '__main__':
    unittest.main()

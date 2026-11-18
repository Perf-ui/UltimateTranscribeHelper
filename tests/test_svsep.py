"""Safety checks around the experimental piano staff model."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from omnizart.desktop import svsep


class PianoSVSepTests(unittest.TestCase):
    def test_validates_checkpoint_and_preserves_note_order(self):
        with TemporaryDirectory() as folder:
            model = Path(folder) / 'model.ckpt'
            model.write_bytes(b'checkpoint')
            def run(command, **kwargs):
                Path(command[3]).write_text('[2, 1]', encoding='utf-8')
                return SimpleNamespace(returncode=0, stdout='')
            with patch.object(svsep, 'ready', return_value=True), patch.object(svsep, 'environment', return_value=Path(folder)), patch.object(svsep, 'python_path', return_value=Path('python')), patch.object(svsep, 'SVSEP_SHA256', hashlib.sha256(b'checkpoint').hexdigest()), patch.object(svsep.subprocess, 'run', side_effect=run):
                self.assertEqual(svsep.predict_staff([(0, 2, 48, 80), (0, 2, 72, 80)], 16), [2, 1])

    def test_rejects_wrong_prediction_count(self):
        with TemporaryDirectory() as folder:
            model = Path(folder) / 'model.ckpt'
            model.write_bytes(b'checkpoint')
            def run(command, **kwargs):
                Path(command[3]).write_text('[1]', encoding='utf-8')
                return SimpleNamespace(returncode=0, stdout='')
            with patch.object(svsep, 'ready', return_value=True), patch.object(svsep, 'environment', return_value=Path(folder)), patch.object(svsep, 'python_path', return_value=Path('python')), patch.object(svsep, 'SVSEP_SHA256', hashlib.sha256(b'checkpoint').hexdigest()), patch.object(svsep.subprocess, 'run', side_effect=run):
                with self.assertRaisesRegex(RuntimeError, 'invalid staff predictions'):
                    svsep.predict_staff([(0, 2, 48, 80), (0, 2, 72, 80)], 16)

    def test_rejects_unverified_checkpoint_before_running(self):
        with TemporaryDirectory() as folder:
            (Path(folder) / 'model.ckpt').write_bytes(b'untrusted')
            with patch.object(svsep, 'ready', return_value=True), patch.object(svsep, 'environment', return_value=Path(folder)), patch.object(svsep.subprocess, 'run') as run:
                with self.assertRaisesRegex(RuntimeError, 'verification failed'):
                    svsep.predict_staff([(0, 1, 60, 80)], 16)
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()

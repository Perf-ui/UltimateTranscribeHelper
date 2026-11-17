"""Exercise model verification and safe extraction without downloading weights."""
import hashlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import zipfile

from omnizart.desktop import transkun_aug


def archive_bytes(extra=False):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("checkpointMSimplerAug/checkpoint.pt", b"weights")
        archive.writestr("checkpointMSimplerAug/model.conf", b"config")
        if extra:
            archive.writestr("../escape", b"bad")
    return stream.getvalue()


TEST_FILES = {
    "checkpointMSimplerAug/checkpoint.pt": ("checkpoint.pt", 7, hashlib.sha256(b"weights").hexdigest()),
    "checkpointMSimplerAug/model.conf": ("model.conf", 6, hashlib.sha256(b"config").hexdigest()),
}


class TranskunAugTests(unittest.TestCase):
    def test_download_verify_extract_and_run(self):
        data = archive_bytes()
        with TemporaryDirectory() as folder:
            target = Path(folder) / "model.zip"
            with patch.object(transkun_aug, "model_path", return_value=target), \
                 patch.object(transkun_aug, "ARCHIVE_SIZE", len(data)), \
                 patch.object(transkun_aug, "ARCHIVE_SHA256", hashlib.sha256(data).hexdigest()), \
                 patch.object(transkun_aug, "FILES", TEST_FILES), \
                 patch.object(transkun_aug.urllib.request, "urlopen", return_value=io.BytesIO(data)), \
                 patch("omnizart.desktop.transkun.transcribe") as run:
                self.assertEqual(transkun_aug.install_model(), target)
                def check_files(*args, **kwargs):
                    self.assertEqual(kwargs["weight"].read_bytes(), b"weights")
                    self.assertEqual(kwargs["config"].read_bytes(), b"config")
                run.side_effect = check_files
                transkun_aug.transcribe("song.wav", "song.mid")
                run.assert_called_once()

    def test_rejects_unexpected_archive_members(self):
        with TemporaryDirectory() as folder:
            archive = Path(folder) / "model.zip"
            archive.write_bytes(archive_bytes(extra=True))
            with patch.object(transkun_aug, "FILES", TEST_FILES):
                with self.assertRaisesRegex(ValueError, "Unexpected"):
                    transkun_aug.extract_model(archive, folder)
            self.assertFalse((Path(folder).parent / "escape").exists())

    def test_invalid_import_preserves_existing_archive(self):
        with TemporaryDirectory() as folder:
            target, source = Path(folder) / "model.zip", Path(folder) / "bad.zip"
            target.write_bytes(b"keep")
            source.write_bytes(b"wrong")
            with patch.object(transkun_aug, "model_path", return_value=target), \
                 patch.object(transkun_aug, "ARCHIVE_SIZE", 5), \
                 patch.object(transkun_aug, "ARCHIVE_SHA256", hashlib.sha256(b"right").hexdigest()):
                with self.assertRaises(ValueError):
                    transkun_aug.install_model(source)
            self.assertEqual(target.read_bytes(), b"keep")

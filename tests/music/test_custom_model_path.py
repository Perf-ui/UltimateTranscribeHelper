"""Imported checkpoints can have any directory name."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from omnizart.music.app import MusicTranscription


class CustomModelPathTests(unittest.TestCase):
    def test_resolves_saved_model_without_music_prefix(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory) / "my-checkpoint"
            folder.mkdir()
            (folder / "saved_model.pb").touch()
            (folder / "configurations.yaml").touch()
            application = object.__new__(MusicTranscription)
            application.settings = SimpleNamespace(model=SimpleNamespace(save_prefix="music"))
            model_path, config_path = application._resolve_model_path(str(folder))
            self.assertEqual(Path(model_path), folder)
            self.assertEqual(Path(config_path), folder / "configurations.yaml")


if __name__ == "__main__":
    unittest.main()

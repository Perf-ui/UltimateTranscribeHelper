"""Verify MuseScore subprocess handling without launching the application."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from omnizart.desktop.score_export import export_musicxml


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

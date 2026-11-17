"""Verify optional checkpoint preparation without downloading or running a model."""
import hashlib
import io
import sys
import types
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from omnizart.desktop import pedal_piano


class PedalPianoTests(unittest.TestCase):
    def test_download_is_verified_and_installed(self):
        data = b"known checkpoint contents"
        with TemporaryDirectory() as folder:
            target = Path(folder) / "models" / "model.pth"
            with patch.object(pedal_piano, "checkpoint_path", return_value=target), \
                 patch.object(pedal_piano, "CHECKPOINT_SIZE", len(data)), \
                 patch.object(pedal_piano, "CHECKPOINT_SHA256", hashlib.sha256(data).hexdigest()), \
                 patch.object(pedal_piano.urllib.request, "urlopen", return_value=io.BytesIO(data)):
                self.assertEqual(pedal_piano.install_checkpoint(), target)
                self.assertTrue(pedal_piano.verify_checkpoint(target))
                self.assertEqual(target.read_bytes(), data)

    def test_invalid_import_does_not_replace_existing_model(self):
        with TemporaryDirectory() as folder:
            target, imported = Path(folder) / "model.pth", Path(folder) / "import.pth"
            target.write_bytes(b"keep")
            imported.write_bytes(b"wrong")
            with patch.object(pedal_piano, "checkpoint_path", return_value=target), \
                 patch.object(pedal_piano, "CHECKPOINT_SIZE", 5), \
                 patch.object(pedal_piano, "CHECKPOINT_SHA256", hashlib.sha256(b"right").hexdigest()):
                with self.assertRaisesRegex(ValueError, "does not match"):
                    pedal_piano.install_checkpoint(imported)
            self.assertEqual(target.read_bytes(), b"keep")
            self.assertEqual(sorted(p.name for p in Path(folder).iterdir()), ["import.pth", "model.pth"])

    def test_missing_checkpoint_fails_without_starting_inference(self):
        with TemporaryDirectory() as folder:
            with patch.object(pedal_piano, "checkpoint_path", return_value=Path(folder) / "missing"):
                with self.assertRaisesRegex(FileNotFoundError, "Models & import"):
                    pedal_piano.transcribe("song.wav", folder)

    def test_transcription_adapter_keeps_pedal_events(self):
        import mido
        import numpy as np
        with TemporaryDirectory() as folder:
            output = Path(folder) / "song.mid"
            class FakePiano:
                def __init__(self, device, checkpoint_path):
                    self.device = device
                def transcribe(self, audio, midi_path):
                    midi = mido.MidiFile()
                    midi.tracks.append(mido.MidiTrack([mido.Message("control_change", control=64, value=127)]))
                    midi.save(midi_path)
            fake_piano = types.SimpleNamespace(PianoTranscription=FakePiano, sample_rate=16000)
            fake_librosa = types.SimpleNamespace(load=lambda *args, **kwargs: (np.zeros(16), 16000))
            with patch.object(pedal_piano, "checkpoint_path", return_value=Path(folder) / "model.pth"), \
                 patch.object(pedal_piano, "verify_checkpoint", return_value=True), \
                 patch.dict(sys.modules, {"piano_transcription_inference": fake_piano, "librosa": fake_librosa}):
                pedal_piano.transcribe("song.wav", output)
            messages = [message for track in mido.MidiFile(str(output)).tracks for message in track]
            self.assertTrue(any(message.type == "control_change" and message.control == 64 for message in messages))

"""Optional metadata-enabled UVR models: safe installation and routing."""
import hashlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import types
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf
from omnizart.desktop import sherpa_uvr


class SherpaUvrTests(unittest.TestCase):
    def test_download_verifies_and_invalid_import_preserves_existing(self):
        data = b"official model"
        with TemporaryDirectory() as folder:
            target, bad = Path(folder) / "model.onnx", Path(folder) / "bad.onnx"
            bad.write_bytes(b"invalid")
            models = {"vocal-ft": ("model.onnx", hashlib.sha256(data).hexdigest())}
            with patch.object(sherpa_uvr, "model_path", return_value=target), \
                 patch.object(sherpa_uvr, "MODELS", models), \
                 patch.object(sherpa_uvr.urllib.request, "urlopen", return_value=io.BytesIO(data)):
                sherpa_uvr.install_model("vocal-ft")
                with self.assertRaises(ValueError):
                    sherpa_uvr.install_model("vocal-ft", bad)
            self.assertEqual(target.read_bytes(), data)

    def test_vocal_and_accompaniment_stems_are_routed_correctly(self):
        with TemporaryDirectory() as folder:
            folder = Path(folder)
            audio = np.arange(12, dtype=np.float32).reshape(6, 2) / 100
            source, vocals, accompaniment = folder / "input.wav", folder / "vocals.wav", folder / "music.wav"
            sf.write(str(source), audio, 44100, subtype="FLOAT")
            class Config:
                def __init__(self, **kwargs):
                    pass
                def validate(self):
                    return True
            class Separator:
                def __init__(self, config):
                    pass
                def process(self, rate, samples):
                    return types.SimpleNamespace(sample_rate=rate, stems=[
                        types.SimpleNamespace(data=samples * 0.25),
                        types.SimpleNamespace(data=samples * 0.75)])
            fake = types.SimpleNamespace(OfflineSourceSeparationConfig=Config,
                OfflineSourceSeparationModelConfig=Config, OfflineSourceSeparationUvrModelConfig=Config,
                OfflineSourceSeparation=Separator)
            with patch.object(sherpa_uvr, "verify_model", return_value=True), \
                 patch.dict("sys.modules", {"sherpa_onnx": fake, "librosa": types.SimpleNamespace()}):
                sherpa_uvr.separate("vocal-ft", source, accompaniment, vocals)
            np.testing.assert_allclose(sf.read(str(vocals), dtype="float32", always_2d=True)[0], audio * .25)
            np.testing.assert_allclose(sf.read(str(accompaniment), dtype="float32", always_2d=True)[0], audio * .75)

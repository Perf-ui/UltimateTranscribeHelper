"""Optional metadata-enabled UVR models supported by sherpa-onnx."""
import hashlib
import os
from pathlib import Path
import tempfile
import urllib.request

MODELS = {
    "vocal-ft": ("UVR-MDX-NET-Voc_FT.onnx", "e411182ce2c53541fefdcc99a8f46f2fe03978eb22038b9497c1d9d95a00fad4"),
    "inst-hq4": ("UVR-MDX-NET-Inst_HQ_4.onnx", "af6de857b80f3ea7c4fd7b0380e7138f5ecf91da3e5f140c463b5aa6d927636f"),
    "inst-hq5": ("UVR-MDX-NET-Inst_HQ_5.onnx", "487e35ae87ed9af9914c85c357e60800c07b8196949e274fe884c18a0c620dbb"),
}
MAX_SIZE = 100_000_000
SOURCE = "https://huggingface.co/k2-fsa/sherpa-onnx-models/resolve/main/source-separation-models/"


def model_path(model):
    if model not in MODELS:
        raise ValueError("Unknown UVR model.")
    root = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share")))
    return root / "Omnizart" / "models" / "uvr-sherpa" / MODELS[model][0]


def verify_model(model, path):
    path = Path(path)
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_SIZE:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == MODELS[model][1]


def install_model(model, source=None):
    target = model_path(model)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, filename = tempfile.mkstemp(prefix="uvr-", suffix=".partial", dir=str(target.parent))
    temporary = Path(filename)
    try:
        with os.fdopen(fd, "wb") as output:
            input_stream = urllib.request.urlopen(SOURCE + MODELS[model][0], timeout=60) if source is None else Path(source).open("rb")
            with input_stream:
                for chunk in iter(lambda: input_stream.read(1024 * 1024), b""):
                    output.write(chunk)
                    if output.tell() > MAX_SIZE:
                        raise ValueError("The selected UVR file is larger than expected.")
        if not verify_model(model, temporary):
            raise ValueError("The file does not match the selected sherpa-onnx UVR model (SHA-256).")
        temporary.replace(target)
        return target
    finally:
        temporary.unlink(missing_ok=True)


def separate(model, source, accompaniment_path, vocal_path=None):
    import librosa
    import numpy as np
    import sherpa_onnx
    import soundfile as sf

    checkpoint = model_path(model)
    if not verify_model(model, checkpoint):
        raise FileNotFoundError("The selected UVR model is missing or invalid. Use Manage separation models.")
    samples, rate = sf.read(str(source), dtype="float32", always_2d=True)
    if not len(samples):
        raise ValueError("The input audio contains no samples.")
    if samples.shape[1] == 1:
        samples = np.repeat(samples, 2, axis=1)
    else:
        samples = samples[:, :2]
    samples = samples.T
    if rate != 44100:
        samples = librosa.resample(samples, orig_sr=rate, target_sr=44100, axis=-1)
        rate = 44100
    config = sherpa_onnx.OfflineSourceSeparationConfig(
        model=sherpa_onnx.OfflineSourceSeparationModelConfig(
            uvr=sherpa_onnx.OfflineSourceSeparationUvrModelConfig(model=str(checkpoint)),
            num_threads=1, provider="cpu"))
    if not config.validate():
        raise RuntimeError("Could not initialize the selected UVR model.")
    print(f"Separating with {MODELS[model][0]} on CPU...", flush=True)
    result = sherpa_onnx.OfflineSourceSeparation(config).process(rate, np.ascontiguousarray(samples))
    if len(result.stems) < 2:
        raise RuntimeError("The UVR model did not return both stems.")
    for index, destination in ((0, vocal_path), (1, accompaniment_path)):
        if destination is not None:
            stem = np.asarray(result.stems[index].data).T
            if stem.size == 0:
                raise RuntimeError("The UVR model returned an empty stem.")
            sf.write(str(destination), stem, result.sample_rate, subtype="FLOAT")

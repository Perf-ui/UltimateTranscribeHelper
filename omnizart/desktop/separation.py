"""Optional CPU vocal separation before instrument transcription."""
from pathlib import Path


def remove_vocals(source, destination):
    """Write the Spleeter accompaniment stem as a WAV file."""
    separate_stems(source, destination)


def separate_stems(source, destination, vocal_destination=None):
    """Write accompaniment and, optionally, vocal stems from one separation pass."""
    import librosa
    import numpy as np
    import sherpa_onnx
    import soundfile as sf
    from omnizart import MODULE_PATH

    directory = Path(MODULE_PATH) / "checkpoints" / "vocal" / "sherpa-onnx-spleeter-2stems-fp16"
    vocals = directory / "vocals.fp16.onnx"
    accompaniment = directory / "accompaniment.fp16.onnx"
    if not vocals.is_file() or not accompaniment.is_file():
        raise FileNotFoundError("The bundled vocal separation model is missing. Reinstall Omnizart.")
    samples, rate = sf.read(str(source), dtype="float32", always_2d=True)
    if not len(samples):
        raise ValueError("The input audio contains no samples.")
    if samples.shape[1] == 1:
        samples = np.repeat(samples, 2, axis=1)
    elif samples.shape[1] > 2:
        samples = samples[:, :2]
    samples = samples.T
    if rate != 44100:
        samples = librosa.resample(samples, orig_sr=rate, target_sr=44100, axis=-1)
        rate = 44100
    config = sherpa_onnx.OfflineSourceSeparationConfig(
        model=sherpa_onnx.OfflineSourceSeparationModelConfig(
            spleeter=sherpa_onnx.OfflineSourceSeparationSpleeterModelConfig(
                vocals=str(vocals), accompaniment=str(accompaniment)),
            num_threads=1, provider="cpu"))
    if not config.validate():
        raise RuntimeError("Could not initialize the vocal separation model.")
    print("Separating vocals from accompaniment; this can take several minutes...", flush=True)
    result = sherpa_onnx.OfflineSourceSeparation(config).process(rate, np.ascontiguousarray(samples))
    if len(result.stems) < 2:
        raise RuntimeError("Vocal separation did not return an accompaniment track.")
    stem = np.asarray(result.stems[1].data).T
    if stem.size == 0:
        raise RuntimeError("Vocal separation returned an empty accompaniment track.")
    sf.write(str(destination), stem, result.sample_rate, subtype="FLOAT")
    if vocal_destination is not None:
        vocal_stem = np.asarray(result.stems[0].data).T
        if vocal_stem.size == 0:
            raise RuntimeError("Vocal separation returned an empty vocal track.")
        sf.write(str(vocal_destination), vocal_stem, result.sample_rate, subtype="FLOAT")

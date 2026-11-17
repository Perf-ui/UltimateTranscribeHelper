"""CPU inference for UVR-MDX-NET-Inst HQ 3.

Overlap-add and spectral layout adapted from python-audio-separator (MIT),
https://github.com/nomadkaraoke/python-audio-separator.
"""
from pathlib import Path


def separate(source, accompaniment_path, vocal_path=None, device="cpu", gpu_index=0):
    import librosa
    import numpy as np
    import onnxruntime as ort
    import soundfile as sf
    import torch
    from omnizart import MODULE_PATH

    model = Path(MODULE_PATH) / "checkpoints" / "vocal" / "UVR-MDX-NET-Inst_HQ_3.onnx"
    if not model.is_file():
        raise FileNotFoundError("The UVR separator model is missing. Reinstall Omnizart.")
    audio, rate = sf.read(str(source), dtype="float32", always_2d=True)
    if not len(audio):
        raise ValueError("The input audio contains no samples.")
    if audio.shape[1] == 1:
        audio = np.repeat(audio, 2, axis=1)
    else:
        audio = audio[:, :2]
    mix = audio.T
    if rate != 44100:
        mix = librosa.resample(mix, orig_sr=rate, target_sr=44100, axis=-1)
    # Match the upstream separator's input normalization.
    peak = np.max(np.abs(mix))
    if peak > 0 and (peak > 0.9 or peak < 0.6):
        mix = mix * (0.9 / peak if peak > 0.9 else 0.6 / peak)
    mix = np.asarray(mix, dtype=np.float32)
    n_fft, hop, frames, dim_f = 6144, 1024, 256, 3072
    chunk, trim = hop * (frames - 1), n_fft // 2
    gen = chunk - 2 * trim
    padding = gen + trim - (mix.shape[-1] % gen)
    mixture = np.pad(mix, ((0, 0), (trim, padding)))
    result = np.zeros_like(mixture)
    weights = np.zeros(mixture.shape[-1], dtype=np.float32)
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    if device == "directml":
        if "DmlExecutionProvider" not in ort.get_available_providers():
            raise RuntimeError("DirectML GPU support is unavailable. Choose CPU or reinstall the Windows build.")
        options.enable_mem_pattern = False
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        providers = [("DmlExecutionProvider", {"device_id": gpu_index}), "CPUExecutionProvider"]
    elif device == "cpu":
        providers = ["CPUExecutionProvider"]
    else:
        raise ValueError(f"Unknown separator device: {device}")
    try:
        session = ort.InferenceSession(str(model), sess_options=options, providers=providers)
    except Exception as exc:
        if device == "directml":
            raise RuntimeError(f"Could not initialize DirectML GPU {gpu_index}. Check the GPU index and driver, or choose CPU. {exc}") from exc
        raise
    if device == "directml":
        session.disable_fallback()
        if "DmlExecutionProvider" not in session.get_providers():
            raise RuntimeError("DirectML GPU initialization failed. Check the GPU index and driver, or choose CPU.")
    window = torch.hann_window(n_fft)
    step = int(chunk * 0.75)
    print(f"Separating instruments with UVR MDX on {'DirectML GPU ' + str(gpu_index) if device == 'directml' else 'CPU'}...", flush=True)
    with torch.no_grad():
        for start in range(0, mixture.shape[-1], step):
            end = min(start + chunk, mixture.shape[-1])
            size = end - start
            part = np.pad(mixture[:, start:end], ((0, 0), (0, chunk - size)))
            spectrum = torch.stft(torch.from_numpy(part), n_fft=n_fft, hop_length=hop,
                                  window=window, center=True, return_complex=True)
            spectrum = torch.view_as_real(spectrum).permute(0, 3, 1, 2).reshape(1, 4, -1, frames)
            spectrum = spectrum[:, :, :dim_f, :].contiguous()
            spectrum[:, :, :3, :] = 0
            prediction = session.run(None, {session.get_inputs()[0].name: spectrum.numpy()})[0]
            pred = torch.from_numpy(prediction)
            pred = torch.nn.functional.pad(pred, (0, 0, 0, n_fft // 2 + 1 - dim_f))
            pred = pred.reshape(2, 2, n_fft // 2 + 1, frames).permute(0, 2, 3, 1).contiguous()
            wave = torch.istft(torch.view_as_complex(pred), n_fft=n_fft, hop_length=hop,
                               window=window, center=True).numpy()
            taper = np.hanning(size).astype(np.float32)
            result[:, start:end] += wave[:, :size] * taper
            weights[start:end] += taper
    instrument = (result[:, trim:trim + mix.shape[1]] /
                  np.maximum(weights[trim:trim + mix.shape[1]], 1e-8)) * 1.022
    vocals = mix - instrument
    sf.write(str(accompaniment_path), instrument.T, 44100, subtype="FLOAT")
    if vocal_path is not None:
        sf.write(str(vocal_path), vocals.T, 44100, subtype="FLOAT")

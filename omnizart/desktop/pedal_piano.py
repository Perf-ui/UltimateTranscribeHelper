"""Optional pedal-aware piano transcription using the upstream Kong model."""
import hashlib
import os
from pathlib import Path
import tempfile
import urllib.request

CHECKPOINT_NAME = "CRNN_note_F1=0.9677_pedal_F1=0.9186.pth"
CHECKPOINT_URL = ("https://zenodo.org/record/4034264/files/"
                  "CRNN_note_F1%3D0.9677_pedal_F1%3D0.9186.pth?download=1")
CHECKPOINT_SIZE = 171_966_578
CHECKPOINT_SHA256 = "c3fa9730725bf4a762f1c14bc80cd5986eacda01b026f5a4a2525cd607876141"


def checkpoint_path():
    root = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share")))
    return root / "Omnizart" / "models" / "pedal-piano" / CHECKPOINT_NAME


def verify_checkpoint(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size != CHECKPOINT_SIZE:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == CHECKPOINT_SHA256


def install_checkpoint(source=None):
    """Download the pinned file, or import it, only after verifying its identity."""
    target = checkpoint_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="pedal-piano-", suffix=".partial", dir=str(target.parent))
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as output:
            if source is None:
                input_stream = urllib.request.urlopen(CHECKPOINT_URL, timeout=60)
            else:
                input_stream = Path(source).open("rb")
            with input_stream:
                while True:
                    chunk = input_stream.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    if output.tell() > CHECKPOINT_SIZE:
                        raise ValueError("The checkpoint is larger than the expected official model.")
        if not verify_checkpoint(temporary):
            raise ValueError("The file does not match the official piano checkpoint (size or SHA-256).")
        temporary.replace(target)
        return target
    finally:
        temporary.unlink(missing_ok=True)


def transcribe(input_audio, output):
    path = checkpoint_path()
    if not verify_checkpoint(path):
        raise FileNotFoundError("Pedal Piano model is missing or invalid. Use Models & import to download or import it.")
    try:
        import librosa
        import numpy as np
        from piano_transcription_inference import PianoTranscription, sample_rate
    except ImportError as exc:
        raise RuntimeError("Pedal Piano runtime is missing. Install or rebuild the Windows package.") from exc
    audio, _ = librosa.load(str(input_audio), sr=sample_rate, mono=True)
    if not len(audio):
        raise ValueError("The input audio contains no samples.")
    target = Path(output)
    if target.is_dir():
        target = target / (Path(input_audio).stem + ".mid")
    elif target.suffix.lower() not in (".mid", ".midi"):
        target = Path(str(target) + ".mid")
    print("Loading Pedal Piano and transcribing on CPU...", flush=True)
    model = PianoTranscription(device="cpu", checkpoint_path=str(path))
    model.transcribe(np.asarray(audio, dtype=np.float32), str(target))
    if not target.is_file() or not target.stat().st_size:
        raise RuntimeError("Pedal Piano did not produce a MIDI file.")
    print(f"MIDI written to {target}", flush=True)

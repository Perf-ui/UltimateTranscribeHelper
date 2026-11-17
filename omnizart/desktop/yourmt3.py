"""Optional YourMT3 inference adapter backed by the third-party mt3-infer API."""
from pathlib import Path
import shutil
import subprocess


def transcribe(input_audio, output):
    try:
        import librosa
        import numpy as np
        from mt3_infer import transcribe as run_transcription
    except ImportError:
        command = shutil.which("mt3-infer")
        if command is None:
            raise RuntimeError(
                'YourMT3 needs mt3-infer. Install with: '
                'pip install "mt3-infer[torch] @ git+https://github.com/openmirlab/mt3-infer.git"'
            )
        target = Path(output)
        if target.is_dir():
            target = target / (Path(input_audio).stem + ".mid")
        elif target.suffix.lower() not in (".mid", ".midi"):
            target = Path(str(target) + ".mid")
        result = subprocess.run([command, "transcribe", str(input_audio), "-o", str(target), "-m", "yourmt3"],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace", timeout=3600,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode != 0 or not target.is_file():
            raise RuntimeError("YourMT3 failed: " + result.stdout[-3000:])
        return
    audio, sample_rate = librosa.load(str(input_audio), sr=16000, mono=True)
    result = run_transcription(np.asarray(audio, dtype=np.float32), sr=sample_rate, model="yourmt3")
    target = Path(output)
    if target.is_dir():
        target = target / (Path(input_audio).stem + ".mid")
    elif target.suffix.lower() not in (".mid", ".midi"):
        target = Path(str(target) + ".mid")
    result.save(str(target))

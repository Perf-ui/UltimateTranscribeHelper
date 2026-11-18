"""Optional MuScriptor CLI adapter."""
import subprocess
from omnizart.desktop.optional_models import python_path, ready
import os
from pathlib import Path


def model_folder():
    root = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share")))
    folder = root / "Omnizart" / "models" / "muscriptor"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def model_checkpoint():
    checkpoints = sorted(model_folder().glob("*.safetensors"))
    return checkpoints[0] if len(checkpoints) == 1 and (model_folder() / "config.json").is_file() else None


def transcribe(input_audio, output):
    checkpoint = model_checkpoint()
    if checkpoint is None:
        raise RuntimeError(f"Download the MuScriptor small model from Hugging Face and save its .safetensors and config.json files in: {model_folder()}")
    target = Path(output)
    if target.is_dir():
        target = target / (Path(input_audio).stem + ".mid")
    elif target.suffix.lower() not in (".mid", ".midi"):
        target = Path(str(target) + ".mid")
    if not ready("MuScriptor"):
        raise RuntimeError("MuScriptor is not installed. Select it in the desktop app to install it.")
    command = [str(python_path("MuScriptor")), "-m", "muscriptor", "transcribe"]
    command.extend([str(input_audio), "--model", str(checkpoint), "--format", "midi", "--output", str(target)])
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace", timeout=3600,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Could not start MuScriptor. Install the optional package and model access first.") from exc
    if result.returncode != 0 or not target.is_file():
        raise RuntimeError("MuScriptor failed: " + result.stdout[-3000:])

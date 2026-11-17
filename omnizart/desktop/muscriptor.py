"""Optional MuScriptor CLI adapter."""
import subprocess
import sys
import shutil
from pathlib import Path


def transcribe(input_audio, output):
    target = Path(output)
    if target.is_dir():
        target = target / (Path(input_audio).stem + ".mid")
    elif target.suffix.lower() not in (".mid", ".midi"):
        target = Path(str(target) + ".mid")
    executable = shutil.which("muscriptor")
    command = ([executable, "transcribe"] if executable else
               [sys.executable, "-m", "muscriptor", "transcribe"])
    command.extend([str(input_audio), "--model", "small", "--format", "midi", "--output", str(target)])
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace", timeout=3600,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Could not start MuScriptor. Install the optional package and model access first.") from exc
    if result.returncode != 0 or not target.is_file():
        raise RuntimeError("MuScriptor failed: " + result.stdout[-3000:])

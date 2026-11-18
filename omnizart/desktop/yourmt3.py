"""Optional YourMT3 inference adapter."""
from pathlib import Path
import subprocess
from omnizart.desktop.optional_models import python_path, ready


def transcribe(input_audio, output):
    if not ready("YourMT3"):
        raise RuntimeError("YourMT3 is not installed. Select it in the desktop app to install it.")
    target = Path(output)
    if target.is_dir():
        target = target / (Path(input_audio).stem + ".mid")
    elif target.suffix.lower() not in (".mid", ".midi"):
        target = Path(str(target) + ".mid")
    command = [str(python_path("YourMT3")), "-m", "mt3_infer.cli", "transcribe",
               str(input_audio), "-o", str(target), "-m", "yourmt3"]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", timeout=3600,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if result.returncode != 0 or not target.is_file():
        raise RuntimeError("YourMT3 failed: " + result.stdout[-3000:])

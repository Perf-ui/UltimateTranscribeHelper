"""Isolated runtimes for optional transcription backends."""
import os
from pathlib import Path
import subprocess
import sys

PACKAGES = {
    "YourMT3": "mt3-infer[torch] @ https://github.com/openmirlab/mt3-infer/archive/refs/heads/master.zip",
    "MuScriptor": "muscriptor @ https://github.com/muscriptor/muscriptor/archive/refs/heads/main.zip",
}

# Revision 2 repairs environments created before the Transformers constraint.
READY_REVISIONS = {"YourMT3": "2", "MuScriptor": "ready"}


def environment(model):
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return root / "Omnizart" / "optional" / model.lower()


def python_path(model):
    folder = environment(model)
    return folder / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ready(model):
    try:
        return (python_path(model).is_file() and
                (environment(model) / ".ready").read_text(encoding="utf-8").strip() == READY_REVISIONS[model])
    except OSError:
        return False


def install(model):
    folder = environment(model)
    marker = folder / ".ready"
    marker.unlink(missing_ok=True)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    base_python = Path(sys.executable)
    if base_python.name.lower() == "pythonw.exe":
        base_python = base_python.with_name("python.exe")
    dependencies = [PACKAGES[model]]
    if model == "YourMT3":
        dependencies.append("transformers==4.43.4")
    for command in ([str(base_python), "-m", "venv", str(folder)],
                    [str(python_path(model)), "-m", "pip", "install", *dependencies]):
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace", creationflags=flags)
        if result.returncode:
            raise RuntimeError(result.stdout[-4000:] or "Optional model setup failed.")
    marker.write_text(READY_REVISIONS[model], encoding="utf-8")

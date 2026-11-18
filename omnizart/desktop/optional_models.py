"""Isolated runtimes for optional transcription backends."""
import hashlib
import os
import urllib.request
from pathlib import Path
import subprocess
import sys

PACKAGES = {
    "YourMT3": "mt3-infer[torch] @ https://github.com/openmirlab/mt3-infer/archive/refs/heads/master.zip",
    "MuScriptor": "muscriptor @ https://github.com/muscriptor/muscriptor/archive/refs/heads/main.zip",
}

# Revision 2 repairs environments created before the Transformers constraint.
READY_REVISIONS = {"YourMT3": "2", "MuScriptor": "ready", "Piano SVSep": "1", "Beat This": "1"}
SVSEP_COMMIT = "1462e7c28d7adaae033150883a7cb00238ee364a"
SVSEP_SHA256 = "1f71ab8b6c7cd271e18adfba5ccbcd634a8530a44e46aabede27e15ce84dbe32"
SVSEP_URL = f"https://raw.githubusercontent.com/CPJKU/piano_svsep/{SVSEP_COMMIT}/pretrained_models/model.ckpt"
BEAT_SHA256 = "8c328b45f59d8dd3dff219253ff6a8d6482be57d0133a29140e2febbf8eb8331"
BEAT_URL = "https://huggingface.co/MuScriptor/assets/resolve/main/beat_this-final0.ckpt"




def environment(model):
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return root / "Omnizart" / "optional" / model.lower()


def python_path(model):
    folder = environment(model)
    return folder / ("Scripts/python.exe" if os.name == "nt" else "bin/python")



def _verified_model(path, expected):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest() == expected

def ready(model):
    try:
        return (python_path(model).is_file() and
                (model not in ("Piano SVSep", "Beat This") or
                 _verified_model(environment(model) / "model.ckpt", SVSEP_SHA256 if model == "Piano SVSep" else BEAT_SHA256)) and
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
    if model in ("Piano SVSep", "Beat This"):
        # The portable app bundles the CPU build of torch 2.5.1. A separate
        # environment can read it while keeping newly installed packages local.
        venv = [str(base_python), "-m", "venv", "--system-site-packages", str(folder)]
        if model == "Piano SVSep":
            dependencies = ["torch-geometric==2.8.1", "torch-scatter==2.1.2+pt25cpu", "partitura==1.8.0",
                            "pytorch-lightning==2.6.6", "verovio==4.2.1", "torchmetrics==1.9.0",
                            "scikit-learn==1.6.0", "gitpython"]
            pip = [str(python_path(model)), "-m", "pip", "install", *dependencies,
                   "-f", "https://data.pyg.org/whl/torch-2.5.0+cpu.html"]
        else:
            pip = [str(python_path(model)), "-m", "pip", "install", "beat-this==1.1.0",
                   "einops==0.8.2", "rotary-embedding-torch==0.9.2"]
    else:
        venv = [str(base_python), "-m", "venv", str(folder)]
        dependencies = [PACKAGES[model]]
        if model == "YourMT3":
            dependencies.append("transformers==4.43.4")
        pip = [str(python_path(model)), "-m", "pip", "install", *dependencies]
    commands = [venv]
    if model in ("Piano SVSep", "Beat This"):
        commands.append([str(python_path(model)), "-c", "import torch; assert torch.__version__.split('+')[0].startswith('2.5.') and torch.version.cuda is None, 'This model requires the bundled CPU PyTorch 2.5 runtime.'"])
    commands.append(pip)
    for command in commands:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace", creationflags=flags)
        if result.returncode:
            raise RuntimeError(result.stdout[-4000:] or "Optional model setup failed.")
    if model in ("Piano SVSep", "Beat This"):
        url, expected = (SVSEP_URL, SVSEP_SHA256) if model == "Piano SVSep" else (BEAT_URL, BEAT_SHA256)
        target = folder / "model.ckpt"
        temporary = folder / "model.ckpt.download"
        try:
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as output:
                digest = hashlib.sha256()
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
                    output.write(block)
            if digest.hexdigest() != expected:
                raise RuntimeError(f"{model} model download failed its SHA-256 verification.")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    marker.write_text(READY_REVISIONS[model], encoding="utf-8")

"""Optional official TransKun V2 augmented checkpoint."""
import hashlib
import os
from pathlib import Path
import tempfile
import urllib.request
import zipfile

ARCHIVE_SIZE = 50_694_377
ARCHIVE_SHA256 = "f61ebf6467d89081fde9728b659895a3e3d65b4c89516964178967167fae6590"
ARCHIVE_URL = ("https://drive.usercontent.google.com/download?"
               "id=1Hg5ua8vYdtg1Y-MnXD0mLyhRK9Srd7hm&export=download&confirm=t")
FILES = {
    "checkpointMSimplerAug/checkpoint.pt": ("checkpoint.pt", 56_423_254,
        "8bd6b4b5ddf9ce8c5f296a57859eec9f166cd337c35245ec2a2576d90be68c4c"),
    "checkpointMSimplerAug/model.conf": ("model.conf", 782,
        "d3d989214eb148230ee5df476d994dcde6af595904d3f968f1221d2e3bea5ac6"),
}


def model_path():
    root = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share")))
    return root / "Omnizart" / "models" / "transkun-v2-aug" / "checkpointTransformerAug.zip"


def verify_model(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size != ARCHIVE_SIZE:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == ARCHIVE_SHA256


def install_model(source=None):
    target = model_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, filename = tempfile.mkstemp(prefix="transkun-aug-", suffix=".partial", dir=str(target.parent))
    temporary = Path(filename)
    try:
        with os.fdopen(fd, "wb") as output:
            request = urllib.request.Request(ARCHIVE_URL, headers={"User-Agent": "Omnizart/2"})
            input_stream = urllib.request.urlopen(request, timeout=60) if source is None else Path(source).open("rb")
            with input_stream:
                for chunk in iter(lambda: input_stream.read(1024 * 1024), b""):
                    output.write(chunk)
                    if output.tell() > ARCHIVE_SIZE:
                        raise ValueError("The model archive is larger than expected.")
        if not verify_model(temporary):
            raise ValueError("The file does not match the official TransKun V2 Aug archive (size or SHA-256).")
        temporary.replace(target)
        return target
    finally:
        temporary.unlink(missing_ok=True)


def extract_model(archive_path, directory):
    """Extract only the two pinned files, never paths supplied by the archive."""
    result = {}
    with zipfile.ZipFile(archive_path) as archive:
        entries = [item for item in archive.infolist() if not item.is_dir()]
        if len(entries) != len(FILES) or {item.filename for item in entries} != set(FILES):
            raise ValueError("Unexpected TransKun V2 Aug archive contents.")
        for item in entries:
            output_name, expected_size, expected_hash = FILES[item.filename]
            if item.file_size != expected_size:
                raise ValueError("Unexpected TransKun V2 Aug model file size.")
            destination = Path(directory) / output_name
            digest = hashlib.sha256()
            with archive.open(item) as source, destination.open("xb") as output:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    output.write(chunk)
                    digest.update(chunk)
            if digest.hexdigest() != expected_hash:
                raise ValueError("Unexpected TransKun V2 Aug model file checksum.")
            result[output_name] = destination
    return result["checkpoint.pt"], result["model.conf"]


def transcribe(input_audio, output):
    archive = model_path()
    if not verify_model(archive):
        raise FileNotFoundError("TransKun V2 Aug is missing or invalid. Use Models & import to download or import it.")
    from omnizart.desktop.transkun import transcribe as run_transkun
    with tempfile.TemporaryDirectory(prefix="omnizart-transkun-aug-") as folder:
        weight, config = extract_model(archive, folder)
        run_transkun(input_audio, output, weight=weight, config=config)

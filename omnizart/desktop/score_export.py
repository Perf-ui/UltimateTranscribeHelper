"""Convert a MIDI draft through the user's MuseScore installation."""
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from xml.etree import ElementTree


def export_musicxml(source, destination, executable):
    source, destination, executable = Path(source), Path(destination), Path(executable)
    if not executable.is_file():
        raise FileNotFoundError("MuseScore executable not found. Select MuseScore4.exe.")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing score: {destination}")
    with TemporaryDirectory(prefix="omnizart-score-") as folder:
        draft = Path(folder) / "score.musicxml"
        result = subprocess.run([str(executable), str(source), "-o", str(draft)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace",
                                timeout=300, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode != 0:
            raise RuntimeError("MuseScore conversion failed: " + result.stdout[-2000:])
        try:
            root = ElementTree.parse(draft).getroot()
        except (OSError, ElementTree.ParseError) as exc:
            raise RuntimeError("MuseScore did not produce a valid MusicXML score.") from exc
        if root.tag not in ("score-partwise", "score-timewise"):
            raise RuntimeError("MuseScore produced an unexpected XML document.")
        with draft.open("rb") as input_file, destination.open("xb") as output_file:
            shutil.copyfileobj(input_file, output_file)
    return destination

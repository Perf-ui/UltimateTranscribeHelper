"""Convert a MIDI draft through the user's MuseScore installation."""
from collections import defaultdict, deque
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

import mido


def quantize_score_input(source, destination, denominator):
    """Snap note starts and ends to a score grid, preserving all other events."""
    if denominator not in (8, 16, 32):
        raise ValueError("Score grid must be 8, 16 or 32.")
    midi = mido.MidiFile(str(source))
    if midi.type == 2 or midi.ticks_per_beat <= 0:
        raise ValueError("This MIDI timing format is not supported by score quantization.")
    spacing = midi.ticks_per_beat * 4 / denominator
    if spacing < 1:
        raise ValueError("MIDI resolution is too low for this score grid.")
    def snap(tick):
        return round(round(tick / spacing) * spacing)
    for track in midi.tracks:
        events, active, tick = [], defaultdict(deque), 0
        for order, msg in enumerate(track):
            tick += msg.time
            if msg.type == "end_of_track":
                continue
            pos = tick
            if msg.type == "note_on" and msg.velocity:
                pos = snap(tick)
                active[(msg.channel, msg.note)].append(pos)
            elif msg.type in ("note_off", "note_on"):
                starts = active[(msg.channel, msg.note)]
                if starts:
                    start = starts.popleft()
                    pos = max(snap(tick), round(start + spacing))
            # Release notes before new attacks at the same time.
            priority = 0 if msg.type == "note_off" or (msg.type == "note_on" and not msg.velocity) else 1
            events.append((pos, priority, order, msg))
        events.sort(key=lambda event: event[:3])
        track.clear()
        previous = 0
        for pos, _, _, msg in events:
            track.append(msg.copy(time=pos - previous))
            previous = pos
        track.append(mido.MetaMessage("end_of_track", time=0))
    midi.save(str(destination))


def export_musicxml(source, destination, executable, grid=0):
    source, destination, executable = Path(source), Path(destination), Path(executable)
    if not executable.is_file():
        raise FileNotFoundError("MuseScore executable not found. Select MuseScore4.exe.")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing score: {destination}")
    with TemporaryDirectory(prefix="omnizart-score-") as folder:
        draft = Path(folder) / "score.musicxml"
        score_input = source
        if grid:
            score_input = Path(folder) / "score-input.mid"
            quantize_score_input(source, score_input, grid)
        result = subprocess.run([str(executable), str(score_input), "-o", str(draft)],
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

"""Convert a MIDI draft through the user's MuseScore installation."""
from collections import defaultdict, deque
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

import mido


def _child(parent, name):
    found = parent.find(name)
    if found is None:
        found = ElementTree.SubElement(parent, name)
    return found


def _ordered_child(parent, name, before):
    found = parent.find(name)
    if found is not None:
        return found
    found = ElementTree.Element(name)
    position = next((i for i, child in enumerate(parent) if child.tag in before), len(parent))
    parent.insert(position, found)
    return found


def format_musicxml(source, destination, title=None, piano_grand_staff=False):
    """Apply consistent page layout and optional piano grand-staff notation."""
    tree = ElementTree.parse(source)
    root = tree.getroot()
    if root.tag != "score-partwise":
        raise ValueError("Score formatting requires partwise MusicXML.")
    title = title or Path(source).stem
    work = _ordered_child(root, "work", ("movement-number", "movement-title", "identification",
                                         "defaults", "credit", "part-list", "part"))
    _child(work, "work-title").text = title
    _ordered_child(root, "movement-title", ("identification", "defaults", "credit", "part-list", "part")).text = title
    identification = _ordered_child(root, "identification", ("defaults", "credit", "part-list", "part"))
    encoding = _child(identification, "encoding")
    _child(encoding, "software").text = "Omnizart score formatter"
    defaults = _ordered_child(root, "defaults", ("credit", "part-list", "part"))
    scaling = _child(defaults, "scaling")
    _child(scaling, "millimeters").text = "7"
    _child(scaling, "tenths").text = "40"
    page = _child(defaults, "page-layout")
    _child(page, "page-height").text = "1697"
    _child(page, "page-width").text = "1200"
    margins = _child(page, "page-margins")
    _child(margins, "left-margin").text = "70"
    _child(margins, "right-margin").text = "70"
    _child(margins, "top-margin").text = "70"
    _child(margins, "bottom-margin").text = "70"
    system = _child(defaults, "system-layout")
    _child(system, "system-distance").text = "100"
    _child(system, "top-system-distance").text = "70"
    parts = root.findall("part")
    piano_ids = {item.get("id") for item in root.findall("./part-list/score-part")
                 if any(token in " ".join((item.findtext("part-name", ""),
                                             item.findtext("part-abbreviation", ""))).lower()
                        for token in ("piano", "keyboard", "keyboards"))}
    if piano_grand_staff and len(parts) == 1:
        piano_ids.update(part.get("id") for part in parts if len(parts) == 1)
    for part in parts:
        if part.get("id") not in piano_ids:
            continue
        measures = part.findall("measure")
        if not measures:
            continue
        attributes = measures[0].find("attributes")
        if attributes is None:
            attributes = ElementTree.Element("attributes")
            measures[0].insert(0, attributes)
        clefs = attributes.findall("clef")
        for clef in clefs:
            attributes.remove(clef)
        staves = attributes.find("staves")
        if staves is None:
            staves = ElementTree.SubElement(attributes, "staves")
        staves.text = "2"
        treble = ElementTree.SubElement(attributes, "clef", number="1")
        ElementTree.SubElement(treble, "sign").text = "G"
        ElementTree.SubElement(treble, "line").text = "2"
        bass = ElementTree.SubElement(attributes, "clef", number="2")
        ElementTree.SubElement(bass, "sign").text = "F"
        ElementTree.SubElement(bass, "line").text = "4"
        for note in part.iter("note"):
            pitch = note.find("pitch")
            if pitch is None:
                continue
            step = pitch.findtext("step", "C")
            octave = int(pitch.findtext("octave", "4"))
            alter = int(pitch.findtext("alter", "0"))
            semitones = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
            midi_pitch = 12 * (octave + 1) + semitones[step] + alter
            staff = note.find("staff")
            if staff is None:
                staff = ElementTree.Element("staff")
                after = ("beam", "notations", "lyric", "play")
                index = next((i for i, child in enumerate(note) if child.tag in after), len(note))
                note.insert(index, staff)
            staff.text = "2" if midi_pitch < 60 else "1"
    tree.write(destination, encoding="utf-8", xml_declaration=True)


def _run_musescore(executable, source, destination):
    result = subprocess.run([str(executable), str(source), "-o", str(destination)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace",
                            timeout=300, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if result.returncode != 0 or not Path(destination).is_file():
        raise RuntimeError("MuseScore export failed: " + result.stdout[-2000:])


def export_formatted_score(source, destination, pdf_destination, executable, grid=0, piano_grand_staff=False):
    """Convert MIDI to MusicXML, apply score layout, then engrave a PDF with MuseScore."""
    source, destination, pdf_destination, executable = map(Path, (source, destination, pdf_destination, executable))
    if not executable.is_file():
        raise FileNotFoundError("MuseScore executable not found. Select MuseScore4.exe.")
    if destination.exists() or pdf_destination.exists():
        raise FileExistsError("Refusing to overwrite an existing score or PDF.")
    with TemporaryDirectory(prefix="omnizart-score-") as folder:
        folder = Path(folder)
        draft = folder / "draft.musicxml"
        formatted = folder / "formatted.musicxml"
        score_input = source
        if grid:
            score_input = folder / "score-input.mid"
            quantize_score_input(source, score_input, grid)
        _run_musescore(executable, score_input, draft)
        try:
            root = ElementTree.parse(draft).getroot()
        except ElementTree.ParseError as exc:
            raise RuntimeError("MuseScore did not produce valid MusicXML.") from exc
        if root.tag != "score-partwise":
            raise RuntimeError("MuseScore produced an unsupported MusicXML score type.")
        format_musicxml(draft, formatted, source.stem, piano_grand_staff)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with formatted.open("rb") as src, destination.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        _run_musescore(executable, destination, pdf_destination)
    return destination, pdf_destination


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

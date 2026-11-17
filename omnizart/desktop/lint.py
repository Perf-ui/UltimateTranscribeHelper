"""Optional, non-destructive hints for reviewing a transcription."""
from collections import defaultdict, deque
from pathlib import Path

import mido

from omnizart.desktop.smoothing import _tempo_map


def write_report(source, destination):
    """Report short notes and overlapping same-pitch notes, without editing MIDI."""
    midi = mido.MidiFile(str(source))
    if midi.type == 2:
        raise ValueError("Independent-track MIDI files are not supported by the report.")
    seconds_at = _tempo_map(midi)
    findings = []
    for number, track in enumerate(midi.tracks, 1):
        label = next((msg.name for msg in track if msg.type == "track_name" and msg.name), f"Track {number}")
        active = defaultdict(deque)
        tick = 0
        for msg in track:
            tick += msg.time
            if msg.type not in ("note_on", "note_off"):
                continue
            key = (msg.channel, msg.note)
            is_start = msg.type == "note_on" and msg.velocity > 0
            if is_start:
                if active[key] and msg.channel != 9:
                    findings.append((seconds_at(tick), label, f"Overlapping MIDI note {msg.note}; check for a duplicate or repeated note."))
                active[key].append(tick)
            elif active[key]:
                start = active[key].popleft()
                duration = seconds_at(tick) - seconds_at(start)
                if msg.channel != 9 and duration < 0.04:
                    findings.append((seconds_at(start), label, f"Very short MIDI note {msg.note} ({duration * 1000:.0f} ms); check whether it is noise or an intentional fast note."))
    findings.sort(key=lambda entry: entry[0])
    lines = ["Omnizart transcription review", "", "These are suggestions, not confirmed errors. Listen to the original audio before editing.",
             "Times refer to playback from the beginning; track names come from the MIDI.", "",
             f"{len(findings)} possible issues found.", ""]
    for timestamp, label, detail in findings[:1000]:
        minutes, seconds = divmod(timestamp, 60)
        lines.append(f"{int(minutes):02d}:{seconds:06.3f}  |  {label}  |  {detail}")
    if len(findings) > 1000:
        lines.append(f"... {len(findings) - 1000} further findings omitted.")
    with Path(destination).open("x", encoding="utf-8") as output:
        output.write("\n".join(lines) + "\n")
    return len(findings)

"""Combine instrument transcription with a separated vocal melody."""
from pathlib import Path


def merge_tracks(instrument_midi, vocal_midi, destination):
    import pretty_midi

    result = pretty_midi.PrettyMIDI(str(instrument_midi))
    vocals = [track for track in vocal_midi.instruments if not track.is_drum and track.notes]
    if not vocals:
        raise ValueError("No pitched vocal notes were detected; try the instrumental-only option or another recording.")
    for track in vocals:
        track.name = "Vocals"
        track.program = 54  # General MIDI voice oohs
        result.instruments.append(track)
    result.write(str(destination))


def add_vocals(input_audio, vocal_stem, instrument_midi, output):
    from omnizart.vocal import app

    print("Transcribing the separated vocal melody on CPU...", flush=True)
    vocal_midi = app.transcribe(input_audio, output=None, vocal_audio=str(vocal_stem))
    destination = Path(output)
    if destination.is_dir():
        destination = destination / (Path(input_audio).stem + ".mid")
    elif destination.suffix.lower() not in (".mid", ".midi"):
        destination = Path(str(destination) + ".mid")
    merge_tracks(instrument_midi, vocal_midi, destination)
    print(f"Combined MIDI written to {destination}", flush=True)

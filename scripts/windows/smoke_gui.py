"""Exercise the desktop app with a musical fixture and verify MIDI notes."""
from pathlib import Path
import os
import tempfile
import time
import tkinter as tk
import sys

import soundfile

from omnizart.desktop.app import Application, midi_note_count
import omnizart.desktop.app as desktop_app


def main():
    with tempfile.TemporaryDirectory(prefix="omnizart-smoke-") as folder:
        folder = Path(folder)
        desktop_app.folder_settings_path = lambda: folder / "folders.json"
        audio = folder / "sample.wav"
        fixture = Path(os.environ.get("OMNIZART_SMOKE_AUDIO", Path(__file__).resolve().parents[2] / "tests" / "resource" / "sample.wav"))
        with soundfile.SoundFile(fixture) as stream:
            sample_rate = stream.samplerate
            data = stream.read(frames=sample_rate * (25 if "--include-vocals" in sys.argv else 12))
        soundfile.write(audio, data, sample_rate)
        root = tk.Tk()
        root.withdraw()
        app = Application(root)
        app.source.set(str(audio))
        app.destination.set(str(folder))
        model = sys.argv[1] if len(sys.argv) > 1 else "Piano"
        app.music_model.set(model)
        app.mode_changed()
        app.thresholds["onset"].set("0.4" if model == "Basic Pitch" else "3")
        separated = "--remove-vocals" in sys.argv[2:]
        if separated:
            app.remove_vocals.set(True)
            app.keep_accompaniment.set(True)
            app.update_separation_controls()
        if "--gpu" in sys.argv:
            app.use_gpu.set(True)
            app.update_separation_controls()
        if "--include-vocals" in sys.argv:
            app.include_vocals.set(True)
            app.update_vocal_controls()
        app.start()
        deadline = time.monotonic() + 300
        while app.running and time.monotonic() < deadline:
            root.update()
            time.sleep(0.05)
        log = app.log.get("1.0", "end")
        if "--gpu" in sys.argv and "DirectML GPU 0" not in log:
            raise RuntimeError(f"GPU acceleration was not used:\n{log}")
        result = folder / "sample_omnizart" / "sample.mid"
        if app.running or not result.is_file() or not midi_note_count(result.parent):
            raise RuntimeError(f"GUI transcription failed: {app.status.get()}\n{log}")
        if separated and not (result.parent / "sample_accompaniment.wav").is_file():
            raise RuntimeError("GUI did not save the requested accompaniment WAV")
        if "--include-vocals" in sys.argv:
            import pretty_midi
            tracks = pretty_midi.PrettyMIDI(str(result)).instruments
            if not any(track.name == "Vocals" and track.notes for track in tracks):
                raise RuntimeError("GUI did not create a vocal MIDI track")
        root.destroy()
        print("Desktop transcription succeeded:", result.name)


if __name__ == "__main__":
    main()

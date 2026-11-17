"""Exercise two desktop runs without starting a transcription process."""
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
import unittest
from unittest.mock import patch

import mido
from omnizart.desktop.app import Application


class RepeatedRunsTests(unittest.TestCase):
    def test_same_folder_distinct_results_and_current_note_count(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            audio = folder / "song.wav"
            audio.touch()
            with patch("omnizart.desktop.app.folder_settings_path", return_value=folder / "folders.json"), \
                    patch("omnizart.desktop.app.threading.Thread") as thread:
                root = tk.Tk()
                root.withdraw()
                try:
                    app = Application(root)
                    app.source.set(str(audio))
                    app.destination.set(str(folder))
                    app.start()
                    first_command, first_folder = thread.call_args.kwargs["args"]
                    first_base = Path(first_command[first_command.index("--output") + 1])
                    midi = mido.MidiFile()
                    midi.tracks.append(mido.MidiTrack([mido.Message("note_on", note=60, velocity=80)]))
                    midi.save(str(first_base) + ".mid")
                    app.messages.put(("done", (0, first_folder)))
                    app.poll()
                    self.assertIn("1 notes", app.status.get())
                    app.start()
                    second_command, second_folder = thread.call_args.kwargs["args"]
                    second_base = Path(second_command[second_command.index("--output") + 1])
                    self.assertEqual(first_folder, second_folder)
                    self.assertEqual(second_base.name, "song_2")
                    empty = mido.MidiFile()
                    empty.tracks.append(mido.MidiTrack())
                    empty.save(str(second_base) + ".mid")
                    app.messages.put(("done", (0, second_folder)))
                    app.poll()
                    self.assertIn("No notes", app.status.get())
                    self.assertTrue(Path(str(first_base) + ".mid").is_file())
                    self.assertFalse(list(first_folder.glob("*.omnizart.lock")))
                finally:
                    root.destroy()

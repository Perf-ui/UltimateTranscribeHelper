"""Check that the optional separation stage passes its WAV to transcription."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from click.testing import CliRunner
from omnizart.cli.music.transcribe import transcribe


class SeparationCliTests(unittest.TestCase):
    def test_smoothing_saves_a_second_midi(self):
        import mido
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            audio = folder / "song.wav"
            audio.touch()
            def make_midi(*args):
                midi = mido.MidiFile()
                midi.tracks.append(mido.MidiTrack([
                    mido.Message("note_on", note=60, velocity=80),
                    mido.Message("note_off", note=60, time=20),
                    mido.Message("note_on", note=60, velocity=80, time=1),
                    mido.Message("note_off", note=60, time=20)]))
                midi.save(str(folder / "song.mid"))
            with patch("omnizart.cli.music.transcribe._transcribe", side_effect=make_midi):
                result = CliRunner().invoke(transcribe, [str(audio), "--smooth-notes", "--output", str(folder)])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue((folder / "song.mid").is_file())
            cleaned = mido.MidiFile(str(folder / "song_smoothed.mid"))
            self.assertEqual(sum(m.type == "note_on" for t in cleaned.tracks for m in t), 1)

    def test_uvr_gpu_and_index_are_forwarded(self):
        with TemporaryDirectory() as directory:
            audio = Path(directory) / "song.wav"
            audio.touch()
            with patch("omnizart.desktop.mdx.separate") as separation, \
                    patch("omnizart.cli.music.transcribe._transcribe"):
                result = CliRunner().invoke(transcribe, [str(audio), "--remove-vocals", "--separator", "uvr",
                                                       "--uvr-device", "directml", "--gpu-index", "1"])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(separation.call_args.kwargs, {"device": "directml", "gpu_index": 1})

    def test_gpu_is_rejected_for_spleeter(self):
        with TemporaryDirectory() as directory:
            audio = Path(directory) / "song.wav"
            audio.touch()
            result = CliRunner().invoke(transcribe, [str(audio), "--remove-vocals", "--uvr-device", "directml"])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("only to UVR", result.output)

    def test_uvr_is_selected_and_passes_both_stems(self):
        with TemporaryDirectory() as directory:
            audio = Path(directory) / "song.wav"
            audio.touch()
            with patch("omnizart.desktop.mdx.separate") as separation, \
                    patch("omnizart.cli.music.transcribe._transcribe") as run, \
                    patch("omnizart.desktop.combined.add_vocals") as combine:
                result = CliRunner().invoke(transcribe, [str(audio), "--remove-vocals", "--include-vocals",
                                                       "--separator", "uvr", "--output", directory])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(separation.call_args.args[0], str(audio))
            self.assertEqual(separation.call_args.args[2].name, "vocals.wav")
            self.assertEqual(run.call_args.args[0], str(separation.call_args.args[1]))
            combine.assert_called_once()

    def test_separated_audio_does_not_overwrite_existing_file(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            audio = folder / "song.mp3"
            audio.touch()
            existing = folder / "song_accompaniment.wav"
            existing.write_bytes(b"keep")
            def create_stem(source, destination):
                destination.write_bytes(b"new")
            with patch("omnizart.desktop.separation.remove_vocals", side_effect=create_stem), \
                    patch("omnizart.cli.music.transcribe._transcribe") as run:
                result = CliRunner().invoke(transcribe, [str(audio), "--remove-vocals", "--save-accompaniment",
                                                       "--output", str(folder)])
            self.assertNotEqual(result.exit_code, 0)
            self.assertEqual(existing.read_bytes(), b"keep")
            run.assert_not_called()

    def test_separation_uses_a_temporary_file_and_preserves_name(self):
        with TemporaryDirectory() as directory:
            audio = Path(directory) / "song.mp3"
            audio.touch()
            with patch("omnizart.desktop.separation.remove_vocals") as separation, \
                    patch("omnizart.cli.music.transcribe._transcribe") as run:
                result = CliRunner().invoke(transcribe, [str(audio), "--remove-vocals", "--model-path", "Piano"])
            self.assertEqual(result.exit_code, 0, result.output)
            temporary_audio = separation.call_args.args[1]
            self.assertEqual(temporary_audio.name, "song.wav")
            self.assertEqual(run.call_args.args[0], str(temporary_audio))
            self.assertFalse(temporary_audio.exists())


if __name__ == "__main__":
    unittest.main()

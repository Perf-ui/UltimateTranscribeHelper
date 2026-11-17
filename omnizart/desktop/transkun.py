"""CPU piano transcription using the bundled Transkun checkpoint."""
from pathlib import Path
import sys
import warnings


def transcribe(input_audio, output):
    import soundfile
    import transkun.transcribe as transkun

    target = Path(output)
    if target.is_dir():
        target = target / (Path(input_audio).stem + ".mid")
    elif target.suffix.lower() not in (".mid", ".midi"):
        target = Path(str(target) + ".mid")

    def read_audio(path, normalize=True):
        samples, sample_rate = soundfile.read(path, dtype="float32", always_2d=True)
        return sample_rate, samples

    # Use the app's audio decoder so MP3/WAV/FLAC work without a separate
    # system FFmpeg installation. Only the bundled, trusted checkpoint is used.
    previous_reader = transkun.readAudio
    transkun.readAudio = read_audio
    old_argv = sys.argv
    try:
        sys.argv = ["transkun", str(input_audio), str(target), "--device", "cpu"]
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="You are using `torch.load` with `weights_only=False`.*", category=FutureWarning)
            warnings.filterwarnings("ignore", message="torch.utils.checkpoint: the use_reentrant parameter.*", category=UserWarning)
            warnings.filterwarnings("ignore", message="None of the inputs have requires_grad=True.*", category=UserWarning)
            print("Loading Transkun piano model and transcribing on CPU...", flush=True)
            transkun.main()
        print(f"MIDI written to {target}", flush=True)
    finally:
        sys.argv = old_argv
        transkun.readAudio = previous_reader

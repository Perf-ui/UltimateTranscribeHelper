"""CPU transcription with the separately licensed Basic Pitch model."""
import logging
from pathlib import Path


class _OptionalBackendWarnings(logging.Filter):
    def filter(self, record):
        text = record.getMessage()
        return not (record.levelno == logging.WARNING and any(
            text.startswith(name + " is not installed.")
            for name in ("Coremltools", "tflite-runtime", "onnxruntime")
        ))


def transcribe(input_audio, output, onset_threshold=None, frame_threshold=None, minimum_note_ms=None):
    root_logger = logging.getLogger()
    filter_ = _OptionalBackendWarnings()
    root_logger.addFilter(filter_)
    try:
        from basic_pitch.inference import predict
    finally:
        root_logger.removeFilter(filter_)
    options = {}
    if onset_threshold is not None:
        options["onset_threshold"] = onset_threshold
    if frame_threshold is not None:
        options["frame_threshold"] = frame_threshold
    if minimum_note_ms is not None:
        options["minimum_note_length"] = minimum_note_ms
    print("Loading Basic Pitch and transcribing on CPU...", flush=True)
    _, midi, _ = predict(str(input_audio), **options)
    target = Path(output)
    if target.is_dir():
        target = target / (Path(input_audio).stem + ".mid")
    elif target.suffix.lower() not in (".mid", ".midi"):
        target = Path(str(target) + ".mid")
    midi.write(str(target))
    print(f"MIDI written to {target}", flush=True)

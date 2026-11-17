# pylint: disable=C0303,W1401
import click
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil

from omnizart.cli import silence_tensorflow
from omnizart.cli.common_options import add_common_options, COMMON_TRANSCRIBE_OPTIONS
from omnizart.utils import LazyLoader


music = LazyLoader("music", globals(), "omnizart.music")


@click.command()
@add_common_options(COMMON_TRANSCRIBE_OPTIONS)
@click.option("--onset-th", type=click.FloatRange(0, 20), default=None, help="Override note onset threshold.")
@click.option("--duration-th", type=click.FloatRange(0, 20), default=None, help="Override note duration threshold.")
@click.option("--instrument-th", type=click.FloatRange(0, 5), default=None, help="Override instrument confidence threshold.")
@click.option("--frame-th", type=click.FloatRange(0, 1), default=None, help="Basic Pitch frame threshold.")
@click.option("--minimum-note-ms", type=click.FloatRange(0, 2000), default=None, help="Basic Pitch minimum note length in milliseconds.")
@click.option("--remove-vocals", is_flag=True, help="Separate vocals before instrument transcription.")
@click.option("--save-accompaniment", is_flag=True, help="Keep the separated accompaniment WAV.")
@click.option("--include-vocals", is_flag=True, help="Add a separate vocal melody track to the MIDI.")
@click.option("--separator", type=click.Choice(["spleeter", "uvr", "vocal-ft", "inst-hq4", "inst-hq5"]), default="spleeter", help="Vocal separation model.")
@click.option("--uvr-device", type=click.Choice(["cpu", "directml"]), default="cpu", help="Device for UVR separation only.")
@click.option("--gpu-index", type=click.IntRange(min=0), default=0, help="DirectML adapter index.")
@click.option("--smooth-notes", is_flag=True, help="Also save a conservatively smoothed MIDI copy.")
@click.option("--smooth-gap-ms", type=click.FloatRange(0, 200), default=30, help="Maximum gap to join, in milliseconds.")
@click.option("--remove-short-ms", type=click.FloatRange(0, 200), default=0, help="Also remove notes shorter than this duration; 0 disables.")
def transcribe(input_audio, model_path, output, onset_th, duration_th, instrument_th, frame_th, minimum_note_ms,
               remove_vocals, save_accompaniment, include_vocals, separator, uvr_device, gpu_index,
               smooth_notes, smooth_gap_ms, remove_short_ms):
    """Transcribe a single audio and output as a MIDI file.

    This will output a MIDI file with the same name as the given audio, except the
    extension will be replaced with '.mid'.

    Supported modes are: Piano, Stream, Pop

    \b
    Example Usage
    $ omnizart music transcribe \\ 
        example.wav \\ 
        --model-path path/to/model \\ 
        --output example.mid
    """
    if save_accompaniment and not remove_vocals:
        raise click.UsageError("--save-accompaniment requires --remove-vocals.")
    if uvr_device != "cpu" and (separator != "uvr" or not (remove_vocals or include_vocals)):
        raise click.UsageError("DirectML applies only to UVR vocal separation.")
    if model_path in ("Transkun (piano)", "Transkun V2 Aug", "Pedal Piano"):
        if any(value is not None for value in (onset_th, duration_th, instrument_th, frame_th, minimum_note_ms)):
            raise click.UsageError("These thresholds are not available for the selected piano model.")
    elif model_path == "Basic Pitch":
        if onset_th is not None and onset_th > 1:
            raise click.BadParameter("Basic Pitch onset must be between 0 and 1", param_hint="--onset-th")
        if duration_th is not None or instrument_th is not None:
            raise click.UsageError("Duration and instrument thresholds apply to Omnizart models only.")
    elif frame_th is not None or minimum_note_ms is not None:
        raise click.UsageError("Frame threshold and minimum note length apply to Basic Pitch only.")
    if remove_vocals or include_vocals:
        from omnizart.desktop.separation import remove_vocals as separate, separate_stems
        with TemporaryDirectory(prefix="omnizart-separation-") as temporary:
            separated = Path(temporary) / (Path(input_audio).stem + ".wav")
            vocal_stem = Path(temporary) / "vocals.wav"
            if separator == "uvr":
                from omnizart.desktop.mdx import separate as separate_uvr
                if uvr_device == "cpu":
                    separate_uvr(input_audio, separated, vocal_stem if include_vocals else None)
                else:
                    separate_uvr(input_audio, separated, vocal_stem if include_vocals else None,
                                 device=uvr_device, gpu_index=gpu_index)
            elif separator in ("vocal-ft", "inst-hq4", "inst-hq5"):
                from omnizart.desktop.sherpa_uvr import separate as separate_sherpa_uvr
                separate_sherpa_uvr(separator, input_audio, separated, vocal_stem if include_vocals else None)
            elif include_vocals:
                separate_stems(input_audio, separated, vocal_stem)
            else:
                separate(input_audio, separated)
            if save_accompaniment:
                target = Path(output)
                folder = target if target.is_dir() else target.parent
                name = Path(input_audio).stem if target.is_dir() else (
                    target.stem if target.suffix.lower() in (".mid", ".midi") else target.name)
                saved = folder / (name + "_accompaniment.wav")
                try:
                    with separated.open("rb") as source_file, saved.open("xb") as destination_file:
                        shutil.copyfileobj(source_file, destination_file)
                except FileExistsError as exc:
                    raise click.ClickException(f"Refusing to overwrite existing accompaniment: {saved}") from exc
                click.echo(f"Accompaniment saved to {saved}")
            instrument_input = str(separated) if remove_vocals else input_audio
            if include_vocals:
                instrument_midi = Path(temporary) / "instruments.mid"
                _transcribe(instrument_input, model_path, str(instrument_midi), onset_th, duration_th, instrument_th, frame_th, minimum_note_ms)
                from omnizart.desktop.combined import add_vocals
                add_vocals(input_audio, vocal_stem, instrument_midi, output)
            else:
                _transcribe(instrument_input, model_path, output, onset_th, duration_th, instrument_th, frame_th, minimum_note_ms)
    else:
        _transcribe(input_audio, model_path, output, onset_th, duration_th, instrument_th, frame_th, minimum_note_ms)
    if smooth_notes or remove_short_ms:
        from omnizart.desktop.smoothing import smooth_midi
        target = Path(output)
        if target.is_dir():
            target = target / (Path(input_audio).stem + ".mid")
        elif model_path not in ("Basic Pitch", "Transkun (piano)", "Transkun V2 Aug", "Pedal Piano") and not include_vocals:
            if not str(target).endswith(".mid"):
                target = Path(str(target) + ".mid")
        elif target.suffix.lower() not in (".mid", ".midi"):
            target = Path(str(target) + ".mid")
        cleaned = target.with_name(target.stem + "_smoothed.mid")
        try:
            merged = smooth_midi(target, cleaned, smooth_gap_ms, remove_short_ms, join_notes=smooth_notes)
        except (OSError, ValueError) as exc:
            raise click.ClickException(f"Original MIDI was saved, but smoothing failed: {exc}") from exc
        click.echo(f"Cleaned MIDI saved to {cleaned} ({merged} fragments joined). Original preserved.")


def _transcribe(input_audio, model_path, output, onset_th, duration_th, instrument_th, frame_th, minimum_note_ms):
    if model_path == "Transkun V2 Aug":
        from omnizart.desktop.transkun_aug import transcribe as transkun_aug_transcribe
        transkun_aug_transcribe(input_audio, output)
        return
    if model_path == "Pedal Piano":
        from omnizart.desktop.pedal_piano import transcribe as pedal_piano_transcribe
        pedal_piano_transcribe(input_audio, output)
        return
    if model_path == "Transkun (piano)":
        from omnizart.desktop.transkun import transcribe as transkun_transcribe
        transkun_transcribe(input_audio, output)
        return
    if model_path == "Basic Pitch":
        from omnizart.desktop.basic_pitch import transcribe as basic_pitch_transcribe
        basic_pitch_transcribe(input_audio, output, onset_th, frame_th, minimum_note_ms)
        return
    silence_tensorflow()
    music.app.transcribe(input_audio, model_path, output=output, onset_th=onset_th,
                         duration_th=duration_th, instrument_th=instrument_th)


def process_doc():
    # Some dirty work for preserving and converting the docstring inside the decorated
    # function into .rst format.
    doc = transcribe.__doc__
    doc = doc.replace("\b", "").replace("    ", "").replace("--", "        --")

    code_block = "\n.. code-block:: bash\n\n"
    doc = doc.replace("$", f"{code_block}    $")

    return doc


__doc__ = process_doc()

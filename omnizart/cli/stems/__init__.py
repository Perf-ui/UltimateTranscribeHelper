"""CLI entry point for optional six-stem audio separation."""
import click


@click.group()
def stems():
    """Separate an audio recording into six WAV stems."""


@stems.command()
@click.argument("input_audio", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", required=True, type=click.Path(), help="Output basename, without extension.")
@click.option("--device", type=click.Choice(["cpu", "directml"]), default="cpu")
@click.option("--gpu-index", type=click.IntRange(0, 99), default=0)
def transcribe(input_audio, output, device, gpu_index):
    """Create drums, bass, other, vocals, guitar, and piano WAV files."""
    from omnizart.desktop.six_stems import separate
    try:
        separate(input_audio, output, device=device, gpu_index=gpu_index)
    except (OSError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc

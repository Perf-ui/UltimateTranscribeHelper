"""Use Beat This! to detect beat and downbeat times from an audio file."""
import json
from pathlib import Path
import sys


def main():
    from beat_this.inference import File2Beats
    audio, checkpoint, output = sys.argv[1:4]
    beats, downbeats = File2Beats(checkpoint_path=checkpoint, device='cpu', dbn=False)(audio)
    Path(output).write_text(json.dumps({'beats': beats.tolist(), 'downbeats': downbeats.tolist()}), encoding='utf-8')


if __name__ == '__main__':
    main()

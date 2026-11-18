"""Run the optional Beat This! model in its isolated environment."""
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from omnizart.desktop.optional_models import environment, python_path, ready


def detect(audio):
    if not ready('Beat This'):
        raise RuntimeError('Beat This is not installed. Enable audio bar alignment in the desktop app to set it up.')
    with TemporaryDirectory(prefix='omnizart-beats-') as folder:
        output = Path(folder) / 'beats.json'
        worker = Path(__file__).with_name('beat_worker.py')
        model = environment('Beat This') / 'model.ckpt'
        result = subprocess.run([str(python_path('Beat This')), str(worker), str(audio), str(model), str(output)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                                errors='replace', timeout=3600,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode or not output.is_file():
            raise RuntimeError('Beat This failed: ' + result.stdout[-2500:])
        values = json.loads(output.read_text(encoding='utf-8'))
    if not isinstance(values, dict) or not isinstance(values.get('beats'), list) or not isinstance(values.get('downbeats'), list):
        raise RuntimeError('Beat This returned invalid beat data.')
    return values['beats'], values['downbeats']

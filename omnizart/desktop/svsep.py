"""Invoke Piano SVSep without allowing it to rewrite or discard score notes."""
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from omnizart.desktop.optional_models import environment, python_path, ready, SVSEP_SHA256


def predict_staff(notes, measure_length, beat_type=4):
    if not ready('Piano SVSep'):
        raise RuntimeError('Piano SVSep is not installed. Select the neural piano option in the desktop app to set it up.')
    model = environment('Piano SVSep') / 'model.ckpt'
    digest = hashlib.sha256()
    with model.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != SVSEP_SHA256:
        raise RuntimeError('Piano SVSep model verification failed. Remove its .ready file and run setup again.')
    with TemporaryDirectory(prefix='omnizart-svsep-') as folder:
        request, output = Path(folder) / 'input.json', Path(folder) / 'output.json'
        request.write_text(json.dumps({'notes': notes, 'measure_length': measure_length, 'beat_type': beat_type}), encoding='utf-8')
        worker = Path(__file__).with_name('svsep_worker.py')
        result = subprocess.run([str(python_path('Piano SVSep')), str(worker), str(request), str(output), str(model)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                                errors='replace', timeout=3600,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode or not output.is_file():
            raise RuntimeError('Piano SVSep failed: ' + result.stdout[-3000:])
        predicted = json.loads(output.read_text(encoding='utf-8'))
    if len(predicted) != len(notes) or any(value not in (1, 2) for value in predicted):
        raise RuntimeError('Piano SVSep returned invalid staff predictions.')
    return predicted

"""Run the vendored Piano SVSep model on quantized note events.

The model supplies staff suggestions only. Omnizart retains the original notes,
timing and tie creation rather than using the project's MusicXML exporter.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'vendor' / 'piano_svsep'))


def main():
    import numpy as np
    import torch
    import torch_geometric as pyg
    from piano_svsep.models.pl_models import PLPianoSVSep
    from piano_svsep.utils import (hetero_graph_from_note_array, get_vocsep_features,
                                   score_graph_to_pyg, HeteroScoreGraph,
                                   get_measurewise_pot_edges, get_pot_chord_edges)

    request_path, output_path, checkpoint = map(Path, sys.argv[1:4])
    request = json.loads(request_path.read_text(encoding='utf-8'))
    entries = request['notes']
    measure_length = request['measure_length']
    beat_type = request.get('beat_type', 4)
    beats_per_measure = int(measure_length * beat_type / 16)
    # The upstream predictor forms a dense note-by-note assignment matrix.
    # Bound memory on long recordings by splitting at attack boundaries.
    chunks, current = [], []
    for index, entry in enumerate(entries):
        if current and entry[0] != entries[current[-1]][0] and (
                len(current) >= 1200 or entry[0] // measure_length // 32 != entries[current[0]][0] // measure_length // 32):
            chunks.append(current)
            current = []
        current.append(index)
    if current:
        chunks.append(current)
    model = PLPianoSVSep.load_from_checkpoint(str(checkpoint), map_location='cpu', strict=False, weights_only=False)
    model.module.eval()
    predictions = [None] * len(entries)
    for indices in chunks:
        array = np.empty(len(indices), dtype=[('onset_div', 'i4'), ('duration_div', 'i4'),
                         ('onset_beat', 'f4'), ('duration_beat', 'f4'), ('ts_beats', 'i4'),
                         ('pitch', 'i4'), ('staff', 'i4'), ('voice', 'i4')])
        for position, index in enumerate(indices):
            start, end, pitch, _velocity = entries[index]
            array[position] = (start, end - start, start * beat_type / 16,
                               (end - start) * beat_type / 16, beats_per_measure, pitch, 1, 1)
        _, edges = hetero_graph_from_note_array(array, pot_edge_dist=0)
        graph = HeteroScoreGraph(get_vocsep_features(array), edges, name='score', labels=None, note_array=array)
        graph.pot_edges = torch.tensor(get_measurewise_pot_edges(array, array['onset_div'] // measure_length))
        graph.pot_chord_edges = torch.tensor(get_pot_chord_edges(array, graph.get_edges_of_type('onset').numpy()))
        data = pyg.data.Batch.from_data_list([score_graph_to_pyg(graph)])
        with torch.no_grad():
            _voice_edges, staff = model.predict_step(data)
        for index, value in zip(indices, staff.tolist()):
            predictions[index] = int(value) + 1
    output_path.write_text(json.dumps(predictions), encoding='utf-8')


if __name__ == '__main__':
    main()

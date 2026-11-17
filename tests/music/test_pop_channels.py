"""The Pop model has six instrument groups, including organ and piano."""
import unittest
from unittest.mock import patch

import numpy as np
import pretty_midi

from omnizart.constants.midi import POP_INSTRUMENT_PROGRAMES
from omnizart.music.inference import multi_inst_note_inference


class PopChannelTests(unittest.TestCase):
    def test_all_pop_channels_have_the_correct_midi_program(self):
        dummy = pretty_midi.PrettyMIDI()
        dummy.instruments.append(pretty_midi.Instrument(program=0))
        data = np.random.default_rng(7).random((5, 352, 13))
        with patch("omnizart.music.inference.note_inference", return_value=dummy):
            result = multi_inst_note_inference(data, mode="pop-note-stream", inst_th=0,
                                               channel_program_mapping=POP_INSTRUMENT_PROGRAMES)
        self.assertEqual([instrument.program for instrument in result.instruments], [24, 32, 40, 16, 0, 56])


if __name__ == "__main__":
    unittest.main()

"""Tests for independent MIDI to MusicXML score generation."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as ET
import mido
from omnizart.desktop.notation import export_score, _estimate_tempo, _piano_voices, _assign_piano_hands


class NativeScoreTests(unittest.TestCase):
    def test_overlapping_note_lengths_get_independent_voices(self):
        with TemporaryDirectory() as directory:
            midi_file = Path(directory) / 'input.mid'
            output = Path(directory) / 'score.musicxml'
            midi = mido.MidiFile(ticks_per_beat=480)
            midi.tracks.append(mido.MidiTrack([
                mido.MetaMessage('set_tempo', tempo=500000),
                mido.Message('note_on', note=64, velocity=90),
                mido.Message('note_on', note=67, velocity=90),
                mido.Message('note_off', note=67, time=480),
                mido.Message('note_on', note=69, velocity=90),
                mido.Message('note_off', note=69, time=480),
                mido.Message('note_off', note=64),
            ]))
            midi.save(midi_file)
            original = midi_file.read_bytes()
            export_score(midi_file, output, tempo=120)
            root = ET.parse(output).getroot()
            notes = [n for n in root.findall('.//note') if n.find('pitch') is not None]
            held = [n for n in notes if n.findtext('pitch/step') == 'E']
            self.assertEqual(len(held), 1)
            self.assertEqual(held[0].findtext('type'), 'half')
            self.assertIsNone(held[0].find('tie'))
            self.assertGreaterEqual(len({n.findtext('voice') for n in notes}), 2)
            self.assertEqual(midi_file.read_bytes(), original)
            with self.assertRaises(FileExistsError):
                export_score(midi_file, output)

    def test_score_skips_percussion_and_preserves_original_midi(self):
        with TemporaryDirectory() as directory:
            path, result = Path(directory) / 'in.mid', Path(directory) / 'out.musicxml'
            midi = mido.MidiFile(ticks_per_beat=480)
            midi.tracks.append(mido.MidiTrack([
                mido.Message('note_on', channel=0, note=60, velocity=90),
                mido.Message('note_on', channel=9, note=36, velocity=90),
                mido.Message('note_off', channel=9, note=36, time=240),
                mido.Message('note_off', channel=0, note=60, time=240),
            ]))
            midi.save(path)
            original = path.read_bytes()
            with self.assertWarnsRegex(UserWarning, 'Percussion tracks are omitted'):
                export_score(path, result, tempo=120)
            root = ET.parse(result).getroot()
            self.assertEqual([n.findtext('pitch/step') for n in root.findall('.//note') if n.find('pitch') is not None], ['C'])
            self.assertEqual(path.read_bytes(), original)

    def test_percussion_only_reports_why_there_is_no_score(self):
        with TemporaryDirectory() as directory:
            path, result = Path(directory) / 'in.mid', Path(directory) / 'out.musicxml'
            midi = mido.MidiFile(ticks_per_beat=480)
            midi.tracks.append(mido.MidiTrack([mido.Message('note_on', channel=9, note=36, velocity=90),
                                               mido.Message('note_off', channel=9, note=36, time=240)]))
            midi.save(path)
            with self.assertRaisesRegex(ValueError, 'only percussion'):
                export_score(path, result)
            self.assertFalse(result.exists())

    def test_tempo_detection_follows_attacks_instead_of_default_midi_tempo(self):
        notes = {(0, 0): [(index * 60 / 154, index * 60 / 154 + .2, 60, 80)
                           for index in range(40)]}
        self.assertEqual(_estimate_tempo(notes, 120), 154)

    def test_overflow_moves_to_other_staff_for_editor_compatibility(self):
        notes = {1: [], 2: [(0, length, 40 + length, 80) for length in range(1, 6)]}
        voices = _piano_voices(notes)
        self.assertEqual(len(voices[2]), 4)
        self.assertEqual(len(voices[1]), 1)
        self.assertEqual(sum(len(lane) for staff in voices.values() for lane in staff), 5)

    def test_voice_overflow_does_not_force_a_wide_span_on_the_other_hand(self):
        notes = {1: [(0, 8, 90, 80)],
                 2: [(0, length, 40 + length, 80) for length in range(1, 6)]}
        with self.assertWarnsRegex(UserWarning, 'Dense overlapping'):
            voices = _piano_voices(notes)
        upper = [pitch[0] for lane in voices[1] for _, _, chord in lane for pitch in chord]
        self.assertEqual(upper, [90])

    def test_hand_assignment_splits_a_wide_chord_between_hands(self):
        entries = [(0, 4, pitch, 80) for pitch in (48, 60, 72, 84)]
        hands = _assign_piano_hands(entries)
        self.assertEqual([note[2] for note in hands[2]], [48, 60])
        self.assertEqual([note[2] for note in hands[1]], [72, 84])

    def test_dense_overlap_preserves_attacks_and_fixed_clefs(self):
        with TemporaryDirectory() as directory:
            path, result = Path(directory) / 'in.mid', Path(directory) / 'out.musicxml'
            midi = mido.MidiFile(ticks_per_beat=480)
            # Nine different note ends cannot fit in eight concurrent voices.
            track = mido.MidiTrack()
            for pitch in range(48, 57):
                track.append(mido.Message('note_on', note=pitch, velocity=80))
            for pitch in range(48, 57):
                track.append(mido.Message('note_off', note=pitch, time=120))
            midi.tracks.append(track)
            midi.save(path)
            with self.assertWarnsRegex(UserWarning, 'Dense overlapping'):
                export_score(path, result, tempo=120)
            root = ET.parse(result).getroot()
            notes = [note for note in root.findall('.//note') if note.find('pitch') is not None]
            starts = [note for note in notes if not any(tie.get('type') == 'stop' for tie in note.findall('tie'))]
            self.assertEqual(len(starts), 9)
            self.assertEqual([(clef.get('number'), clef.findtext('sign')) for clef in root.findall('.//clef')], [('1', 'G'), ('2', 'F')])

    def test_ties_across_barlines_and_optional_tempo(self):
        with TemporaryDirectory() as directory:
            path, result = Path(directory) / 'in.mid', Path(directory) / 'out.musicxml'
            midi = mido.MidiFile(ticks_per_beat=480)
            midi.tracks.append(mido.MidiTrack([mido.Message('note_on', note=60, velocity=70, time=1440),
                                               mido.Message('note_off', note=60, time=960)]))
            midi.save(path)
            export_score(path, result, tempo=120)
            root = ET.parse(result).getroot()
            self.assertEqual([t.get('type') for t in root.findall('.//tie')], ['start', 'stop'])
            self.assertEqual(root.find('.//sound').get('tempo'), '120')
            self.assertEqual(len(root.findall('.//clef')), 2)


if __name__ == '__main__':
    unittest.main()

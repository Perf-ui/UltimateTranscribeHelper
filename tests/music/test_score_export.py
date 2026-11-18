"""Verify MuseScore subprocess handling without launching the application."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import mido
from omnizart.desktop.score_export import export_musicxml, format_musicxml, quantize_score_input, _hide_covered_rests


class ScoreTests(unittest.TestCase):
    def test_conversion_checks_xml_and_does_not_replace_original(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            executable, source, destination = root / 'MuseScore4.exe', root / 'song.mid', root / 'song.musicxml'
            executable.touch()
            source.write_bytes(b'original')
            def run(args, **kwargs):
                Path(args[-1]).write_text('<score-partwise version="4.0"/>', encoding='utf-8')
                return SimpleNamespace(returncode=0, stdout='')
            with patch('omnizart.desktop.score_export.subprocess.run', side_effect=run):
                export_musicxml(source, destination, executable)
                with self.assertRaises(FileExistsError):
                    export_musicxml(source, destination, executable)
            self.assertEqual(source.read_bytes(), b'original')
            self.assertIn('score-partwise', destination.read_text())

    def test_score_quantization_keeps_original_and_non_note_events(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source, output = root / 'original.mid', root / 'grid.mid'
            midi = mido.MidiFile(ticks_per_beat=480)
            midi.tracks.append(mido.MidiTrack([
                mido.MetaMessage('set_tempo', tempo=750000),
                mido.Message('control_change', control=64, value=127, time=40),
                mido.Message('note_on', note=60, velocity=74, time=23),
                mido.Message('note_off', note=60, time=30),
                mido.Message('control_change', control=64, value=0, time=40)]))
            midi.save(source)
            original = source.read_bytes()
            quantize_score_input(source, output, 16)
            self.assertEqual(source.read_bytes(), original)
            events, tick = [], 0
            for message in mido.MidiFile(output).tracks[0]:
                tick += message.time
                events.append((tick, message))
            notes = [(time, msg.type, msg.velocity) for time, msg in events if msg.type in ('note_on', 'note_off')]
            self.assertEqual(notes, [(120, 'note_on', 74), (240, 'note_off', 64)])
            controls = [(time, msg.value) for time, msg in events if msg.type == 'control_change']
            self.assertEqual(controls, [(40, 127), (133, 0)])
            self.assertEqual(next(msg.tempo for _, msg in events if msg.type == 'set_tempo'), 750000)

    def test_piano_clef_fix_preserves_existing_voice_and_staff_assignments(self):
        import xml.etree.ElementTree as ET
        with TemporaryDirectory() as folder:
            source, output = Path(folder) / 'in.xml', Path(folder) / 'out.xml'
            source.write_text("""<score-partwise><part-list><score-part id="P1"><part-name>Piano</part-name></score-part></part-list><part id="P1"><measure number="1"><attributes><staves>2</staves><clef number="1"><sign>G</sign><line>2</line></clef><clef number="2"><sign>G</sign><line>2</line></clef></attributes><note><pitch><step>C</step><octave>4</octave></pitch><voice>5</voice><stem>up</stem><staff>2</staff></note><note><chord/><pitch><step>G</step><octave>4</octave></pitch><voice>5</voice><staff>2</staff></note></measure></part></score-partwise>""", encoding='utf-8')
            format_musicxml(source, output, piano_grand_staff=True)
            root = ET.parse(output).getroot()
            self.assertEqual([note.findtext('staff') for note in root.findall('.//note')], ['2', '2'])
            self.assertIsNone(root.find('.//note/stem'))
            self.assertEqual(root.findtext('.//clef[@number="2"]/sign'), 'F')
            self.assertEqual(root.findtext('.//clef[@number="2"]/line'), '4')

    def test_rests_are_hidden_only_when_other_voice_covers_them(self):
        import xml.etree.ElementTree as ET
        measure = ET.fromstring("""<measure><note><pitch/><duration>8</duration><voice>1</voice><staff>1</staff></note><backup><duration>8</duration></backup><note><rest/><duration>4</duration><voice>2</voice><staff>1</staff></note><note><rest/><duration>8</duration><voice>2</voice><staff>1</staff></note></measure>""")
        _hide_covered_rests(measure)
        rests = [n for n in measure.findall('note') if n.find('rest') is not None]
        self.assertEqual(rests[0].get('print-object'), 'no')
        self.assertIsNone(rests[1].get('print-object'))

    def test_later_piano_clef_changes_are_removed(self):
        import xml.etree.ElementTree as ET
        with TemporaryDirectory() as folder:
            source, output = Path(folder) / 'in.xml', Path(folder) / 'out.xml'
            source.write_text("""<score-partwise><part-list><score-part id="P1"><part-name>Piano</part-name></score-part></part-list><part id="P1"><measure><attributes><staves>2</staves><clef number="1"><sign>G</sign><line>2</line></clef><clef number="2"><sign>F</sign><line>4</line></clef></attributes></measure><measure><attributes><clef number="2"><sign>G</sign><line>2</line></clef><key><fifths>2</fifths></key></attributes></measure></part></score-partwise>""", encoding='utf-8')
            format_musicxml(source, output)
            root = ET.parse(output).getroot()
            self.assertEqual(len(root.findall('.//clef')), 2)
            self.assertEqual(root.findtext('.//key/fifths'), '2')

    def test_invalid_output_is_rejected(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            executable = root / 'MuseScore4.exe'
            executable.touch()
            def run(args, **kwargs):
                Path(args[-1]).write_text('<wrong/>', encoding='utf-8')
                return SimpleNamespace(returncode=0, stdout='')
            with patch('omnizart.desktop.score_export.subprocess.run', side_effect=run):
                with self.assertRaises(RuntimeError):
                    export_musicxml(root / 'in.mid', root / 'out.musicxml', executable)
            self.assertFalse((root / 'out.musicxml').exists())

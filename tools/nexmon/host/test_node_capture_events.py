import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from csi_verify import HEADER
from node_capture_events import assemble, export

MAC = '68:8f:c9:62:f3:17'


def frame(core, seq, seed=1):
    words = [(seed + i) << 18 for i in range(64)]
    head = HEADER.pack(0x1111, -30, 0, bytes.fromhex(MAC.replace(':', '')),
                       seq, core << 8, 0x1006, 106)
    return head + struct.pack('<64I', *words)


class NodeEvents(unittest.TestCase):
    def test_core_order_and_packed_values_preserved(self):
        records = [(100 + i / 10000, frame(c, 16, c + 1)) for i, c in enumerate([2, 0, 1])]
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'export'
            with patch('node_capture_events.pcap_udp', return_value=iter(records)):
                report = export('unused.pcap', out, 64, [0, 1, 2], MAC)
            with np.load(out / 'node-events.npz') as data:
                self.assertEqual(data['packed_words'].shape, (1, 3, 64))
                np.testing.assert_array_equal(data['packed_words'][0, :, 0], np.array([1, 2, 3]) << 18)
                np.testing.assert_array_equal(data['decoded_unscaled'][0, :, 0], [1 + 0j, 2 + 0j, 3 + 0j])
                self.assertEqual(data['event_start_seconds'][0], 100)
            self.assertFalse(report['model_ready'])
            self.assertEqual(json.loads((out / 'summary.json').read_text())['receiver_nodes'], 1)

    def test_repeated_identity_is_retained(self):
        records = [(100 + j * .001 + c * .00001, frame(c, 16, j + 1))
                   for j in range(2) for c in range(3)]
        with tempfile.TemporaryDirectory() as directory:
            with patch('node_capture_events.pcap_udp', return_value=iter(records)):
                report = export('unused.pcap', Path(directory) / 'out', 64, [0, 1, 2], MAC)
            self.assertEqual(report['complete_contiguous_core_events'], 2)
            self.assertEqual(report['repeated_identity_events_20ms'], 1)

    def test_missing_core_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            assemble([(100., frame(0, 16)), (100.001, frame(1, 16))], 64, [0, 1, 2], MAC)

    def test_interleaved_event_rejected(self):
        with self.assertRaisesRegex(ValueError, 'interleaved'):
            assemble([(100., frame(0, 16)), (100.001, frame(1, 32))], 64, [0, 1, 2], MAC)


if __name__ == '__main__':
    unittest.main()

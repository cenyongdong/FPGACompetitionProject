"""Protocol fixtures for the independent diagnostic stream; no network I/O."""
import struct
import tempfile
import unittest
from pathlib import Path

from diagnose_metadata import decode, diagnose


MAC = bytes.fromhex('50bbb5dba502')


def diagnostic(core=0, retry=False, event=7, tsf=65520, qos=5):
    return struct.pack('<4sHH6s7H', b'NMD1', 1, 28, MAC, 0x1230,
                       core << 8, 0xd095, 0x0188 | (0x800 if retry else 0), qos, tsf, event)


def wire(port, payload):
    ip = bytearray(20)
    ip[0], ip[9] = 0x45, 17
    struct.pack_into('>H', ip, 2, 28 + len(payload))
    return b'\xff' * 6 + b'NEXMON\x08\x00' + ip + struct.pack('>4H', port, port, len(payload)+8, 0) + payload


class MetadataProtocol(unittest.TestCase):
    def test_fields_and_invalid_inputs(self):
        d = decode(diagnostic(retry=True))
        self.assertTrue(d['retry'])
        self.assertEqual((d['tid'], d['rx_tsf16'], d['event16']), (5, 65520, 7))
        self.assertIsNone(decode(diagnostic(qos=65535))['tid'])
        p = bytearray(diagnostic()); struct.pack_into('<H', p, 20, 0x0108)
        self.assertIsNone(decode(p)['tid'])
        for p in (diagnostic()[:-1], diagnostic().replace(b'NMD1', b'FAIL'),
                  diagnostic()[:4] + b'\x02\0' + diagnostic()[6:]):
            with self.assertRaises(ValueError):
                decode(p)

    def fixture(self, path, bad_core=False):
        with path.open('wb') as f:
            f.write(struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1))
            for event in range(2):
                for core in range(3):
                    c = struct.pack('<HbB6s4H', 0x1111, -40, 0, MAC, 0x1230, core << 8, 0xd095, 106) + bytes(256)
                    d = diagnostic(core, bool(event), event+7, (65520+event*300) & 65535)
                    if bad_core and event == 1 and core == 2:
                        d = diagnostic(core, True, event+8, 284)
                    for port, payload in ((5500, c), (5501, d)):
                        b = wire(port, payload)
                        f.write(struct.pack('<4I', 100, 1000+event*300+core, len(b), len(b)))
                        f.write(b)

    def test_pairing_retry_and_timestamp_wrap(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'fixture.pcap'; self.fixture(p)
            r, _ = diagnose(p)
            self.assertEqual(r['issues'], [])
            self.assertEqual((r['paired_packets'], r['complete_events']), (6, 2))
            self.assertEqual(r['repeated_identity_events'], 1)
            self.assertTrue(r['repeats'][0]['retry'])
            self.assertFalse(r['repeats'][0]['same_dump'])
            self.assertEqual(r['repeats'][0]['rx_tsf_delta_mod65536'], 300)
            self.fixture(p, bad_core=True)
            r, _ = diagnose(p)
            self.assertTrue(r['issues'])


if __name__ == '__main__':
    unittest.main()

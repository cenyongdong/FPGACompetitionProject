import math
from pathlib import Path
import random
import struct
import unittest
import uuid

from csi_verify import HEADER, parse_payload, pcap_udp, unpack_acphy, verify

MAC = '02:11:22:33:44:55'


def payload(core=0, seq=0, chip=101, nfft=64, word=0x00040000):
    config = core << 8 if chip == 106 else core
    return HEADER.pack(0x1111, -40, 0, bytes.fromhex(MAC.replace(':', '')),
                       seq, config, 0xd024, chip) + struct.pack('<I', word) * nfft


def ethernet_udp(data, port=5500):
    udp = struct.pack('!HHHH', 5500, port, len(data) + 8, 0) + data
    ip = struct.pack('!BBHHHBBH4s4s', 0x45, 0, 20 + len(udp), 1, 0, 64, 17, 0,
                     bytes([10, 10, 10, 10]), bytes([255] * 4)) + udp
    return bytes(12) + b'\x08\x00' + ip


def write_pcap(path, packets):
    with Path(path).open('wb') as f:
        f.write(struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1))
        for index, data in enumerate(packets):
            frame = ethernet_udp(data)
            f.write(struct.pack('<IIII', 1, index * 100, len(frame), len(frame)))
            f.write(frame)


class VerifierTests(unittest.TestCase):
    def setUp(self):
        # Keep bounded fixtures with the evidence; do not use protected OS TEMP.
        root = Path(__file__).resolve().parents[3] / '.local' / 'nexmon-rtac86u-20261017-r1' / 'test-fixtures'
        root.mkdir(parents=True, exist_ok=True)
        self.temp = root / ('case-' + uuid.uuid4().hex)
        self.temp.mkdir()
        self.path = self.temp / 'capture.pcap'

    def check(self, packets, **kwargs):
        write_pcap(self.path, packets)
        return verify(self.path, 64, [0, 1, 2], 0, 101, MAC, min_groups=2, **kwargs)

    def test_three_cores_reordered(self):
        result = self.check([payload(c, s) for s in range(2) for c in [2, 0, 1]])
        self.assertTrue(result['acquisition_pass'])
        self.assertEqual(result['counts']['complete_groups'], 2)

    def test_missing_core_rejected(self):
        self.assertFalse(self.check([payload(c, s) for s in range(2) for c in [0, 1]])['acquisition_pass'])

    def test_duplicate_is_not_silently_deduplicated(self):
        result = self.check([payload(c, s) for s in range(2) for c in [0, 1, 2, 2]])
        self.assertFalse(result['acquisition_pass'])

    def test_sequence_mixing_rejected(self):
        self.assertFalse(self.check([payload(c, c) for c in [0, 1, 2]])['acquisition_pass'])

    def test_chip_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'chip marker'):
            self.check([payload(chip=999)])

    def test_unrequested_chain(self):
        with self.assertRaisesRegex(ValueError, 'core/stream'):
            self.check([payload(core=3)])

    def test_zero_record_rejected(self):
        self.assertFalse(self.check([payload(c, s, word=0) for s in range(2) for c in [0, 1, 2]])['acquisition_pass'])

    def test_header_and_length(self):
        record = parse_payload(payload(), 64)
        self.assertEqual(record['rssi'], -40)
        self.assertEqual(record['mac'], MAC)
        for data in [b'', payload()[:-1], b'\x00\x00' + payload()[2:]]:
            with self.assertRaises(ValueError):
                parse_payload(data, 64)

    def test_bcm4366_measured_header_bits(self):
        # Actual consecutive headers from the first RT-AC86U three-core capture.
        headers = ['1111d200a070b7ee8d504080000095d06a00',
                   '1111d200a070b7ee8d504080000195d06a00',
                   '1111d200a070b7ee8d504080000295d06a00']
        records = [parse_payload(bytes.fromhex(header) + struct.pack('<I', 0x40000) * 64, 64)
                   for header in headers]
        self.assertEqual([record['core'] for record in records], [0, 1, 2])
        self.assertEqual([record['stream'] for record in records], [0, 0, 0])
        header = bytes.fromhex('1111d200a070b7ee8d504080001995d06a00')
        record = parse_payload(header + struct.pack('<I', 0x40000) * 64, 64)
        self.assertEqual((record['core'], record['stream']), (1, 3))

    def test_bcm4366_incorrect_low_byte_rejected(self):
        bad = bytearray(payload(core=0, chip=106))
        bad[12:14] = b'\x01\x00'
        with self.assertRaisesRegex(ValueError, 'reserved bits'):
            parse_payload(bad, 64)

    def test_actual_bcm4366_three_core_fixture(self):
        root = Path(__file__).resolve().parents[3]
        fixture = root / 'tools/nexmon/evidence/device-20261019-r1/threecore-r1.pcap'
        result = verify(fixture, 64, [0, 1, 2], 0, 106, 'a0:70:b7:ee:8d:50')
        self.assertTrue(result['acquisition_pass'])
        self.assertEqual(result['counts']['complete_groups'], 97)
        self.assertEqual(result['counts']['incomplete_groups'], 0)
        self.assertEqual(result['counts'].get('duplicate_core_records', 0), 0)

    def test_legacy_requires_explicit_profile(self):
        data = b'\x11' * 4 + payload()[4:]
        self.assertIsNone(parse_payload(data, 64, 'legacy18')['rssi'])
        with self.assertRaises(ValueError):
            parse_payload(payload(), 64, 'legacy18')

    def test_non_csi_udp_ignored(self):
        frame = ethernet_udp(b'other', 1234)
        self.path.write_bytes(struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)
                              + struct.pack('<IIII', 1, 0, len(frame), len(frame)) + frame)
        self.assertEqual(list(pcap_udp(self.path)), [])

    def test_truncated_capture(self):
        write_pcap(self.path, [payload()])
        self.path.write_bytes(self.path.read_bytes()[:-1])
        with self.assertRaises(ValueError):
            list(pcap_udp(self.path))

    def test_budgets(self):
        write_pcap(self.path, [payload(), payload()])
        with self.assertRaises(ValueError):
            list(pcap_udp(self.path, max_packets=1))
        with self.assertRaises(ValueError):
            list(pcap_udp(self.path, max_bytes=1))

    def test_fragment_rejected(self):
        write_pcap(self.path, [payload()])
        data = bytearray(self.path.read_bytes())
        data[24 + 16 + 14 + 6:24 + 16 + 14 + 8] = b'\x20\x00'
        self.path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'Fragmented'):
            list(pcap_udp(self.path))

    def test_acphy_sign_exponent_and_zero(self):
        rng = random.Random(20261017)
        for nman, nexp in [(12, 6), (9, 5)]:
            for _ in range(1000):
                real = rng.randrange(-(1 << (nman - 1)) + 1, 1 << (nman - 1))
                imag = rng.randrange(-(1 << (nman - 1)) + 1, 1 << (nman - 1))
                exponent = rng.randrange(-(1 << (nexp - 1)), 1 << (nexp - 1))
                word = ((abs(real) << (nexp + nman)) | (abs(imag) << nexp)
                        | (exponent & ((1 << nexp) - 1))
                        | ((real < 0) << (nexp + 2 * nman - 1))
                        | ((imag < 0) << (nexp + nman - 1)))
                self.assertEqual(unpack_acphy([word], nman, nexp)[0],
                                 complex(math.ldexp(real, exponent), math.ldexp(imag, exponent)))


if __name__ == '__main__':
    unittest.main()

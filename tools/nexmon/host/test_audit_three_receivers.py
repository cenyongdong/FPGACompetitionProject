"""Targeted tests for common-frame identity versus common time-grid coverage."""
import struct
import unittest

from audit_three_receivers import Receiver, compare
from stream_node import NodeStream


MAC = bytes.fromhex('021122334455')
CHANNEL = 0xd0a1


def receiver(name, start=0, stop=800, drops=(), seq_origin=0, clock_offset=0,
             retry_at=None, reuse_at=None, shift_after=None, batch='same-job'):
    node = NodeStream(MAC.hex(':'), CHANNEL)
    events, windows = [], []
    node.on_event = events.append
    counter = 0

    def feed(ordinal, timestamp, seq, retry=False):
        nonlocal counter
        for core in range(3):
            words = struct.pack('<64I', *([1 << 18]*64))
            c = struct.pack('<HbB6s4H', 0x1111, -40, 0, MAC, seq,
                            core << 8, CHANNEL, 106)+words
            d = struct.pack('<4sHH6s7H', b'NMD3', 3, 50, MAC, seq, core << 8,
                            CHANNEL, 0x08 | (0x800 if retry else 0), 0xffff,
                            timestamp & 65535, counter & 65535)
            d += struct.pack('<HH3IHI', 28, 3, *([1 << 18]*3), 64,
                             (timestamp+80) & 0xffffffff)
            host = 100+ordinal/300+core/1e6
            # host arrival only bounds clock continuity, never sets RF time.
            if retry:
                host += .0004
            windows.extend(node.feed(host, 5500, c))
            windows.extend(node.feed(host, 5501, d))
        counter += 1

    for ordinal in range(start, stop):
        if ordinal in drops:
            continue
        timestamp = round(ordinal*1e6/300)+clock_offset
        if shift_after is not None and ordinal >= shift_after[0]:
            timestamp += shift_after[1]
        seq = ((ordinal+seq_origin) & 4095) << 4
        if ordinal == reuse_at:
            seq = ((ordinal+seq_origin-1) & 4095) << 4
        feed(ordinal, timestamp, seq)
        if ordinal == retry_at:
            feed(ordinal, timestamp+400, seq, retry=True)
    return Receiver(name, batch, events, windows, node.finish())


class ThreeReceivers(unittest.TestCase):
    def test_independent_clock_origins_and_capture_starts(self):
        nodes = [receiver('a'), receiver('b', start=7, clock_offset=12345),
                 receiver('c', start=19, clock_offset=56789)]
        r = compare(nodes)
        self.assertEqual(r['common_packets']['common_identities'], 781)
        g = r['joint_grid']
        self.assertEqual(g['status'], 'common_packet_anchor_proven')
        self.assertEqual(g['fixed_integer_slot_shifts'], [0, 7, 19])
        self.assertGreater(g['complete_windows'], 0)
        self.assertEqual(g['valid_windows'], g['complete_windows'])
        self.assertFalse(r['hardware_synchronization_proven'])

    def test_missing_packet_rejects_whole_joint_window(self):
        r = compare([receiver('a'), receiver('b', drops=(410,)), receiver('c')])
        self.assertEqual(r['common_packets']['common_identities'], 799)
        self.assertEqual(r['common_packets']['missing_from_union_by_receiver'], [0, 1, 0])
        self.assertGreater(r['joint_grid']['valid_windows'], 0)
        self.assertEqual(r['joint_grid']['reasons']['missing_cell'], 1)
        self.assertEqual(r['joint_grid']['complete_windows']-r['joint_grid']['valid_windows'], 1)

    def test_retry_keeps_first_valid_and_does_not_fill_cells(self):
        r = compare([receiver('a'), receiver('b', retry_at=410), receiver('c')])
        self.assertEqual(r['receivers'][1]['sequence']['dropped_retransmissions'], 1)
        self.assertEqual(r['common_packets']['common_identities'], 800)
        self.assertEqual(r['joint_grid']['valid_windows'], r['joint_grid']['complete_windows'])

    def test_one_sequence_rollover_is_not_global_identity_collision(self):
        r = compare([receiver(n, seq_origin=4000) for n in ('a', 'b', 'c')])
        self.assertTrue(all(n['sequence']['observed_mod4096_wraps'] == 1 for n in r['receivers']))
        self.assertEqual(r['joint_grid']['valid_windows'], r['joint_grid']['complete_windows'])

    def test_nonretry_reuse_is_unproven(self):
        r = compare([receiver('a'), receiver('b', reuse_at=410), receiver('c')])
        self.assertEqual(r['joint_grid']['status'], 'unproven')
        self.assertIsNone(r['joint_grid']['valid_windows'])

    def test_later_timing_shift_cannot_be_fitted_away(self):
        r = compare([receiver('a'), receiver('b', shift_after=(450, 1200)), receiver('c')])
        self.assertEqual(r['common_packets']['common_identities'], 800)
        self.assertGreater(r['common_packets']['consecutive_events']['nonoverlapping_20_event_candidates'], 0)
        self.assertFalse(r['common_packets']['consecutive_events']['proves_300hz_grid'])
        self.assertGreater(r['joint_grid']['reasons']['point_error'], 0)
        self.assertLess(r['joint_grid']['valid_windows'], r['joint_grid']['complete_windows'])

    def test_same_sequences_from_different_jobs_are_rejected(self):
        nodes = [receiver('a'), receiver('b', batch='another-job'), receiver('c')]
        with self.assertRaisesRegex(ValueError, 'Different or absent TX batch'):
            compare(nodes)

    def test_matching_sequence_with_conflicting_frame_length_is_not_same_packet(self):
        nodes = [receiver(n) for n in ('a', 'b', 'c')]
        nodes[1].events[410].meta['raw_rx_frame_size'] += 1
        r = compare(nodes)
        self.assertEqual(r['joint_grid']['status'], 'unproven')
        self.assertIn('Matching sequence identities have conflicting raw frame lengths',
                      r['joint_grid']['reasons'])

    def test_later_whole_cell_shift_reports_disagreement_without_reanchoring(self):
        r = compare([receiver('a'), receiver('b', shift_after=(450, 3400)), receiver('c')])
        self.assertEqual(r['joint_grid']['fixed_integer_slot_shifts'], [0, 0, 0])
        self.assertGreater(r['joint_grid']['common_event_slot_disagreements'][1], 0)
        self.assertGreater(r['joint_grid']['reasons'].get('different_selected_event', 0), 0)
        self.assertLess(r['joint_grid']['valid_windows'], r['joint_grid']['complete_windows'])

    def test_missing_half_sequence_cycle_is_ambiguous(self):
        # With fewer than 120 observations startup may also fail, but the
        # sequence jump itself must remain an explicit independent reason.
        nodes = [receiver(n, stop=3000, drops=range(100, 2300)) for n in ('a', 'b', 'c')]
        r = compare(nodes)
        self.assertEqual(r['joint_grid']['status'], 'unproven')
        self.assertTrue(all(n['sequence']['ambiguous_forward_steps'] == 1 for n in r['receivers']))

    def test_no_common_startup_or_eof_padding(self):
        r = compare([receiver(n, stop=320) for n in ('a', 'b', 'c')])
        self.assertEqual(r['joint_grid']['status'], 'unproven')
        self.assertIsNone(r['joint_grid']['valid_windows'])


if __name__ == '__main__':
    unittest.main()

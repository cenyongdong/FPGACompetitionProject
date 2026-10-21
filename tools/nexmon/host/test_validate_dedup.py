"""First-valid selection/clock/window cases, including a missed original."""
import tempfile
from pathlib import Path
import struct
import unittest

import numpy as np

from test_diagnose_metadata import MAC, wire
from validate_dedup import Event, clock_segments, finalize, read_events, select_first_valid, windows


def event(i, seq=16, tid=0, retry=False, valid=True, t_us=None):
    t = i*3333 if t_us is None else t_us
    return Event(i, dict(mac=MAC.hex(':'),seq=seq,channel=0xd095,tid=tid,
        retry=retry,time=100+t/1e6,rx_tsf16=t & 65535,event16=i),
        np.full((3,64),1 << 18,dtype='<u4'),valid)


class FirstValid(unittest.TestCase):
    def test_nmd2_original_words_remain_distinct_per_core(self):
        group=[]
        for core in range(3):
            d=dict(mac=MAC.hex(':'),seq=16,config=core<<8,channel=0xd095,
                   fc=0x0188,qos=0,tid=0,rx_tsf16=0,event16=0,time=100,
                   original_offset=28,original_words=(core+1,123,456))
            group.append((d,dict(words=[1<<18]*64)))
        e=finalize(0,group)
        self.assertTrue(e.valid)
        np.testing.assert_array_equal(e.original_words[:,0],[1,2,3])
        np.testing.assert_array_equal(e.words[:,28],[1<<18]*3)

    def test_retry_not_tid_fragment_or_sequence_reuse(self):
        e = [event(0), event(1,retry=True,t_us=400),
             event(2,seq=32,retry=True,t_us=3333),
             event(3,tid=1,retry=True,t_us=3500),
             event(4,seq=17,retry=True,t_us=3700),
             event(5,retry=True,t_us=50000)]
        kept = select_first_valid(e)
        self.assertEqual([x.index for x in kept],[0,2,3,4,5])
        self.assertEqual(e[1].first_valid,0)
        self.assertEqual(e[1].decision,'drop_retransmission')
        self.assertTrue(all(np.array_equal(x.words,e[x.index].words) for x in kept))

    def test_invalid_original_does_not_suppress_first_valid_retry(self):
        e = [event(0,valid=False),event(1,retry=True,t_us=400),event(2,retry=True,t_us=800)]
        self.assertEqual([x.index for x in select_first_valid(e)],[1])
        self.assertEqual(e[2].first_valid,1)
        e = [event(0), event(1,t_us=400)]
        select_first_valid(e)
        self.assertEqual(e[1].decision,'ambiguous_identity_reuse')

    def test_low16_wrap_and_long_gap(self):
        e = [event(0,t_us=65000),event(1,t_us=68333),event(2,t_us=200000)]
        boundaries = clock_segments(e)
        self.assertEqual((e[1].segment,e[1].time_us),(0,3333))
        self.assertEqual(e[2].segment,1)
        self.assertEqual(len(boundaries),1)

    def test_unknown_qos_identity_is_not_a_valid_original(self):
        group=[]
        for core in range(3):
            d=dict(mac=MAC.hex(':'),seq=16,config=core<<8,channel=0xd095,
                   fc=0x0188,qos=65535,tid=None,rx_tsf16=0,event16=0,time=100)
            group.append((d,dict(words=[1<<18]*64)))
        e=finalize(0,group)
        self.assertFalse(e.valid)
        self.assertIn('qos_tid_unavailable',e.reason)

    def test_windows_detect_cluster_and_boundary(self):
        e = [event(i,seq=i*16,t_us=round(i*1e6/300)) for i in range(20)]
        clock_segments(e); select_first_valid(e)
        rows, _ = windows(e)
        self.assertTrue(rows[0]['integer_clock_uniform'])
        e[1].time_us = 300
        rows, _ = windows(e)
        self.assertFalse(rows[0]['candidate_50pct'])
        e[1].segment = 1
        rows, _ = windows(e)
        self.assertIsNone(rows[0]['span_us'])

    def test_real_packet_pairing_rejects_zero_and_incomplete_original(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'first-valid.pcap'
            with p.open('wb') as f:
                f.write(struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,1))
                for index,cores in enumerate(([0,1],[0,1,2],[0,1,2])):
                    for core in cores:
                        # First complete retry is valid; the original is partial
                        # and zero. The second retry must refer to the first retry.
                        words = [0 if index==0 else 1<<18]*64
                        c = struct.pack('<HbB6s4H',0x1111,-40,0,MAC,16,core<<8,0xd095,106)+struct.pack('<64I',*words)
                        diag = struct.pack('<4sHH6s7H',b'NMD1',1,28,MAC,16,core<<8,0xd095,
                            0x0188 | (0x800 if index else 0),0,index*400,index)
                        for port,payload in ((5500,c),(5501,diag)):
                            b=wire(port,payload);f.write(struct.pack('<4I',100,index*400+core,len(b),len(b)));f.write(b)
            e, _ = read_events(p)
            self.assertFalse(e[0].valid)
            self.assertEqual([x.index for x in select_first_valid(e)],[1])


if __name__ == '__main__':
    unittest.main()

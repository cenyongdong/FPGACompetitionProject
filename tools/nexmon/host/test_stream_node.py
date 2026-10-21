import struct
import unittest

from stream_node import NodeStream
from test_diagnose_metadata import MAC


def feed_event(a,event,seq=None,tsf=None,retry=False,cores=(0,1,2),lost_diag=False):
    tsf=round(event*1e6/300) if tsf is None else tsf
    seq=((event%4096)<<4) if seq is None else seq
    out=[]
    for core in cores:
        c=struct.pack('<HbB6s4H',0x1111,-40,0,MAC,seq,core<<8,0xd095,106)+struct.pack('<64I',*([1<<18]*64))
        d=struct.pack('<4sHH6s7H',b'NMD1',1,28,MAC,seq,core<<8,0xd095,
                      0x188|(0x800 if retry else 0),0,tsf&65535,event&65535)
        host=100+tsf/1e6+core/1e6
        out.extend(a.feed(host,5500,c))
        if not lost_diag:
            out.extend(a.feed(host,5501,d))
    return out


class NodePackets(unittest.TestCase):
    def test_original_and_retry_and_missed_original(self):
        a=NodeStream(MAC.hex(':'),0xd095)
        feed_event(a,0,seq=16,tsf=0)
        feed_event(a,1,seq=16,tsf=400,retry=True)
        feed_event(a,2,seq=32,tsf=3333,retry=True)
        self.assertEqual(a.counts['keep'],2)
        self.assertEqual(a.counts['drop_retransmission'],1)

    def test_lost_pair_partial_core_and_timeout_reset(self):
        a=NodeStream(MAC.hex(':'),0xd095)
        feed_event(a,0,cores=(0,),lost_diag=True)
        a.expire(100.021)
        self.assertEqual(a.counts['pair_timeout'],1)
        feed_event(a,10,tsf=40000,cores=(0,1))
        feed_event(a,11,tsf=43333)
        self.assertEqual(a.counts['incomplete_group'],1)
        self.assertEqual(a.counts['keep'],1)

    def test_unknown_identity_stops_and_idle_never_pads(self):
        a=NodeStream(MAC.hex(':'),0xd095)
        feed_event(a,0)
        with self.assertRaises(ValueError):
            feed_event(NodeStream('00:11:22:33:44:55',0xd095),1)
        a.expire(101)
        self.assertEqual(a.grid.total_windows,0)
        self.assertFalse(a.grid.prefix)

    def test_stream_outputs_native_words_and_resets_on_event_gap(self):
        a=NodeStream(MAC.hex(':'),0xd095);windows=[]
        for event in range(350):
            windows.extend(feed_event(a,event))
        self.assertTrue(windows)
        self.assertTrue(all(w.valid for w in windows))
        self.assertEqual(windows[0].observations[0].payload.shape,(3,64))
        feed_event(a,352)
        self.assertEqual(a.counts['reset_clock_discontinuity'],1)


if __name__=='__main__':
    unittest.main()

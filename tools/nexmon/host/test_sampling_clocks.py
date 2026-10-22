from types import SimpleNamespace
import unittest

import numpy as np

from associate_length_codes import anchored_rx32, match_codes
from audit_sampling_clocks import ledger_audit, replay_fixed_scale, slope


class SamplingClockAudit(unittest.TestCase):
    def test_a_loss_with_a_repeated_length_must_not_misidentify_the_boundary(self):
        sent=[9,4,8,4,5,6,7,8,9,10,11,12,13,14,15,16,17]
        # Frame1 is observed, frames2/3 are lost, then frames4..16 arrive.
        # The remaining '4' falsely looks like frame3 if only lengths are used.
        received=[4]+sent[4:]
        unsafe,_=match_codes(sent,received,0)
        self.assertIn((0,3),unsafe)
        safe,info=match_codes(sent,received,0,received_contiguous=[False]+[True]*(len(received)-2))
        self.assertNotIn(0,[j for j,_ in safe])
        self.assertTrue(safe)
        self.assertTrue(all(i==j+3 for j,i in safe))
        self.assertEqual(info['conflicting_received_indices'],0)

    def test_nonunique_codes_or_a_send_gap_cannot_create_an_anchor(self):
        self.assertEqual(match_codes([1]*20,[89]*8,88)[0],[])
        sent=list(range(8));received=[s+88 for s in sent]
        self.assertEqual(len(match_codes(sent,received,88)[0]),8)
        self.assertEqual(match_codes(sent,received,88,sent_contiguous=[True]*3+[False]+[True]*3)[0],[])

    def test_hook_anchor_crosses_low16_and_low32_wrap_without_host_time(self):
        events=[]
        for value in (2**32-20,2**32+15,2**32+80):
            hook=(value+200)&0xffffffff
            events.append(SimpleNamespace(meta=dict(hook_tsf_l=hook,hook_minus_rx_low16=200)))
        np.testing.assert_array_equal(anchored_rx32(events),[0,35,100])
        events[1].meta['hook_minus_rx_low16']=32768
        with self.assertRaises(ValueError):anchored_rx32(events)

    def test_relative_slope_resists_one_delay_outlier(self):
        x=np.arange(20)*250000
        y=x*100e-6
        y[10]+=10000
        self.assertAlmostEqual(slope(x,y),100e-6)

    def test_fixed_clock_experiment_still_rejects_a_missing_real_frame(self):
        events=[SimpleNamespace(decision='keep',segment=0,index=i,time_us=round(i*1e6/300*1.0001))
                for i in range(3000) if i!=1500]
        scaled=replay_fixed_scale(events,100)
        self.assertGreater(scaled['valid_windows'],0)
        self.assertGreater(scaled['rejected']['missing_cell'],0)
        self.assertTrue(scaled['real_observations_only'])

    def test_sender_ledger_rejects_backward_calls_without_repair(self):
        sender=dict(requested_hz=300,skipped_late_slots=0,
            sends=[[0,0,10,20,256],[1,3333333,3333340,3333350,256]])
        self.assertEqual(ledger_audit(sender)['trusted_udp_slot_to_rf_associations'],0)
        sender['sends'][1][2]=9
        with self.assertRaises(ValueError):ledger_audit(sender)


if __name__=='__main__':unittest.main()

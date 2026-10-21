"""Fixed-phase/missing-cell/no-reuse tests, without hardware or inference."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from validate_time_grid import analyze,available,grid_segment,window_rows


def grid(times):
    return grid_segment(times,np.arange(len(times)),100+np.arange(len(times)))


class RealGrid(unittest.TestCase):
    def test_regular_twenty_and_integer_period(self):
        times=[round(i*1e6/300) for i in range(40)]
        g=grid(times);r=window_rows(0,g)
        self.assertEqual(g['slots'],40)
        self.assertTrue(available(g,.25).all())
        self.assertEqual([x['start_slot'] for x in r if x['nonoverlapping']],[0,20])
        self.assertTrue(all(x['valid_25pct'] for x in r))
        self.assertEqual(g['positions'].tolist(),list(range(40)))

    def test_missing_cell_does_not_shift_later_events(self):
        times=[round(i*1e6/300) for i in range(20) if i!=7]
        g=grid(times);r=window_rows(0,g)
        self.assertEqual(g['slots'],20)
        self.assertEqual(g['positions'][7],-1)
        self.assertEqual(g['positions'][8],7)
        self.assertEqual(r[0]['missing_25pct'],1)
        self.assertFalse(r[0]['valid_25pct'])

    def test_multiple_candidates_cannot_fill_neighboring_gap(self):
        g=grid([0,3333,3400,10000])
        self.assertEqual(g['positions'].tolist(),[0,1,-1,3])
        self.assertEqual(g['candidates'].tolist(),[1,2,0,1])
        self.assertEqual(len(set(g['positions'][g['positions']>=0])),3)
        g=grid([0,9900,10100])
        self.assertEqual(g['positions'][3],1)  # exact tie -> earlier event

    def test_phase_is_not_refitted_for_second_window(self):
        times=[round(i*1e6/300)+(1200 if i>=20 else 0) for i in range(40)]
        g=grid(times);r=window_rows(0,g)
        self.assertTrue(r[0]['valid_25pct'])
        self.assertFalse(r[20]['valid_25pct'])
        self.assertEqual(r[20]['missing_25pct'],20)
        self.assertTrue(r[20]['valid_50pct'])

    def test_last_observation_has_its_nearest_cell_but_no_extra_padding(self):
        times=[round(i*1e6/300) for i in range(20)];times[-1]-=100
        g=grid(times)
        self.assertEqual(g['slots'],20)
        self.assertTrue(window_rows(0,g)[0]['valid_25pct'])

    def test_a_fixed_phase_offset_keeps_actual_times_and_halfopen_cells(self):
        times=[round(i*1e6/300) for i in range(40)]
        g=grid_segment(times,np.arange(40),np.arange(40),750000)
        self.assertAlmostEqual(g['anchor_us'],-1e6/1200)
        self.assertEqual(g['positions'][0],0)
        self.assertTrue(np.array_equal(g['actual_us'],times))
        self.assertFalse(available(g,.10).any())
        self.assertLessEqual(np.max(np.abs(g['errors_scaled'])),250100)

    def test_segments_cannot_be_joined_to_make_a_window(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);source=base/'source';source.mkdir()
            summary=dict(offline_only=True,model_ready=False,
                source_sha256_from_capture_manifest='fixture',clock_boundaries=1,
                model_contract=dict(required_raw_shape=[3,3,30,20]))
            (source/'summary.json').write_text(json.dumps(summary))
            np.savez(source/'retained-node-events.npz',
                original_event_indices=np.arange(38),clock_segments=np.repeat([0,1],19),
                segment_time_us=np.tile(np.round(np.arange(19)*1e6/300),2).astype('u8'),
                packed_words=np.ones((38,3,64),dtype='u4'))
            r=analyze(source,base/'output')
            self.assertEqual(r['accepted_primary_nonoverlapping_windows'],0)
            self.assertEqual(r['all_reliable_segments']['sliding']['total_windows'],0)
            self.assertIsNone(r['clock_scope']['global_whole_capture_valid_fraction'])
            self.assertFalse(r['model_ready'])


if __name__=='__main__':
    unittest.main()

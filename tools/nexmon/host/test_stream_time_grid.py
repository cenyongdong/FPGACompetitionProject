import unittest

import numpy as np

from stream_time_grid import TimeGridStream, estimate_phase


def replay(times, **kwargs):
    a=TimeGridStream(**kwargs);out=[]
    for i,t in enumerate(times):
        out.extend(a.feed(t,i,payload=i))
    return a,out


class CausalGrid(unittest.TestCase):
    def test_startup_is_excluded_and_no_lookahead(self):
        times=np.round(np.arange(1000)*1e6/300+1500).astype('i8')
        a,w=replay(times)
        b,_=replay(times[:400])
        self.assertEqual(a.calibration,b.calibration)
        self.assertEqual(w[0].observations[0].index,301)
        self.assertTrue(all(x.valid for x in w))
        self.assertTrue(all(o.time_us>a.calibration['calibration_end_us'] for x in w for o in x.observations))
        ids=[o.index for x in w for o in x.observations]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertLessEqual(a.max_buffered_observations,302)

    def test_missing_cell_drops_window_and_extra_cannot_fill(self):
        times=[round(i*1e6/300) for i in range(500) if i!=310]
        times=sorted(times+[round(309*1e6/300)+100])
        _,w=replay(times)
        self.assertFalse(w[0].valid)
        self.assertEqual(w[0].reason,'missing_cell')
        self.assertEqual(sum(o is None for o in w[0].observations),1)
        self.assertTrue(w[1].valid)

    def test_later_shift_is_not_fitted_away(self):
        times=[round(i*1e6/300)+(1200 if i>350 else 0) for i in range(500)]
        _,w=replay(times)
        self.assertTrue(w[0].valid)
        self.assertTrue(any(not x.valid and x.reason=='point_error' for x in w))

    def test_circular_wrap_and_background(self):
        times=sorted([round(i*1e6/300)+3300 for i in range(310)]+[15501,27612,56233])
        fit=estimate_phase(times)
        error=(fit['phase_scaled']-3300*300+500000)%1000000-500000
        self.assertLess(abs(error),301)

    def test_startup_budget_and_invalid_parameters(self):
        a,_=replay(range(1100))
        self.assertTrue(a.failed)
        self.assertFalse(a.prefix)
        self.assertEqual(a.startup_records[0]['reason'],'startup_budget')
        with self.assertRaises(ValueError):
            TimeGridStream(tolerance_fraction=.6)

    def test_clock_reset_and_eof_do_not_pad(self):
        a,w=replay([round(i*1e6/300) for i in range(321)])
        self.assertEqual(len(w),0)  # last cell of first block still open
        tail=a.finish()
        self.assertEqual(tail['complete_cells_in_partial_window'],19)
        a.reset(1)
        self.assertEqual(a.feed(0,400),[])
        with self.assertRaises(ValueError):
            a.feed(40000,401)


if __name__=='__main__':
    unittest.main()

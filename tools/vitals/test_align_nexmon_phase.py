"""Signal preservation and fault-containment tests, not subject/receiver validation."""
import unittest

import numpy as np

from align_nexmon_phase import align_phase, differential_phase, window_quality


def clock(seconds=44):
    return np.rint(np.arange(seconds * 300 + 1) / 300 * 1e9).astype(np.int64)


def analytic(stamps):
    t = stamps / 1e9
    return np.column_stack([.3 * np.sin(2 * np.pi * .25 * t + ch * .1) +
                            .03 * np.sin(2 * np.pi * 1.2 * t + ch * .2)
                            for ch in range(4)])


class AlignmentTests(unittest.TestCase):
    def test_low_band_preserved_with_representation_wrap(self):
        t = clock()
        phase = analytic(t) + 3.1
        pairs = np.stack((np.exp(1j * phase), np.ones_like(phase)), axis=-1)
        wrapped = differential_phase(pairs)
        arrays, q = align_phase(t, wrapped)
        self.assertEqual(q['source_phase_jumps'], [0] * 4)
        self.assertTrue(arrays['valid'].all())
        self.assertTrue((np.diff(arrays['grid_ns']) == 20_000_000).all())
        # Different initial channel branches may differ by a constant 2pi.
        error = np.angle(np.exp(1j * (arrays['phase'] - (analytic(arrays['grid_ns']) + 3.1))))
        self.assertLess(np.sqrt(np.mean(error ** 2)), 1e-4)
        self.assertGreater(q['windows']['locally_qualified_windows'], 0)

    def test_jittered_source_preserves_known_low_band(self):
        t = clock()
        rng = np.random.default_rng(20261022)
        t[1:-1] += rng.integers(-300_000, 300_001, len(t) - 2)
        arrays, q = align_phase(t, analytic(t))
        self.assertTrue(arrays['valid'].all())
        error = arrays['phase'] - analytic(arrays['grid_ns'])
        self.assertLess(np.sqrt(np.mean(error ** 2)), 1e-4)

    def test_anti_alias_rejects_false_1_2hz_from_48_8hz(self):
        t = clock(10)
        phase = np.tile((.1 * np.sin(2 * np.pi * 48.8 * t / 1e9))[:, None], (1, 4))
        arrays, q = align_phase(t, phase)
        self.assertTrue(arrays['valid'].all())
        filtered_rms = np.sqrt(np.mean(arrays['phase'] ** 2))
        raw_rms = np.sqrt(np.mean(phase[::6] ** 2))
        self.assertLess(filtered_rms, raw_rms / 1000)  # >60dB measured attenuation.

    def test_real_jump_is_retained_and_invalidates_filter_support(self):
        t = clock(5)
        phase = analytic(t)
        phase[t >= 2_000_000_000, 0] += .8
        original = phase.copy()
        arrays, q = align_phase(t, phase)
        np.testing.assert_array_equal(phase, original)
        self.assertEqual(q['source_phase_jumps'], [1, 0, 0, 0])
        affected = (arrays['grid_ns'] > 1_600_000_000) & (arrays['grid_ns'] < 2_400_000_000)
        self.assertFalse(arrays['valid'][affected, 0].any())
        self.assertTrue(np.isnan(arrays['phase'][affected, 0]).all())
        self.assertTrue(arrays['valid'][:, 1:].all())

    def test_tiny_fault_between_work_grid_points_is_not_lost(self):
        t = np.sort(np.r_[clock(3), [800_100_000, 800_200_000]])
        phase = analytic(t)
        phase[t == 800_100_000, 0] += .8
        arrays, q = align_phase(t, phase)
        self.assertEqual(q['source_phase_jumps'][0], 2)
        i = np.flatnonzero(arrays['grid_ns'] == 800_000_000)[0]
        self.assertFalse(arrays['valid'][i, 0])

    def test_source_gap_cannot_become_qualified_interpolation(self):
        t = clock(5)
        t = t[(t < 2_000_000_000) | (t > 2_040_000_000)]
        arrays, q = align_phase(t, analytic(t))
        self.assertEqual(q['source_gap_faults'], 1)
        affected = (arrays['grid_ns'] >= 2_000_000_000) & (arrays['grid_ns'] <= 2_040_000_000)
        self.assertFalse(arrays['valid'][affected].any())
        self.assertGreater(q['gap_invalid_output_samples'], 0)

    def test_short_history_is_not_padded_or_repeated(self):
        t = clock(10)
        arrays, q = align_phase(t, analytic(t))
        self.assertLess(len(arrays['grid_ns']), 500)
        self.assertEqual(q['windows']['candidate_windows'], 0)
        self.assertEqual(q['windows']['locally_qualified_windows'], 0)
        self.assertEqual(q['windows']['reason'], 'insufficient_40s_history')

    def test_bad_clock_and_phase_fail_before_filtering(self):
        t = clock(3)
        for bad_t in (t[::-1], np.r_[t[0], t[:-1]], t.astype(float), t - 1):
            with self.assertRaises(ValueError):
                align_phase(bad_t, analytic(t))
        bad = analytic(t)
        bad[5, 0] = np.nan
        with self.assertRaises(ValueError):
            align_phase(t, bad)
        with self.assertRaises(ValueError):
            align_phase(np.array([0, 1000, 181_000_000_000]), np.zeros((3, 4)))

    def test_zero_iq_is_not_a_valid_phase(self):
        pairs = np.ones((10, 4, 2), dtype=complex)
        pairs[2, 1, 0] = 0
        with self.assertRaises(ValueError):
            differential_phase(pairs)


if __name__ == '__main__':
    unittest.main()

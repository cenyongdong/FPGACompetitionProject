"""Check phase equivalence cannot silently approve scalar model inputs."""
import math
import unittest
from numeric_metrics import compare_tokens, gate_result


class NumericPolicyTests(unittest.TestCase):
    def test_periodic_equality_still_requires_scalar_review(self):
        expected = [0.0] * 10800
        actual = expected.copy()
        actual[30] = 2 * math.pi
        metrics = compare_tokens(actual, expected, False)
        self.assertTrue(metrics['phase_circular_pass'])
        self.assertEqual(gate_result('real', metrics)['status'], 'requires_model_input_review')

    def test_true_angle_error_is_not_periodic_equality(self):
        expected = [0.0] * 10800
        actual = expected.copy()
        actual[30] = 2.333
        metrics = compare_tokens(actual, expected, False)
        self.assertFalse(metrics['phase_circular_pass'])
        self.assertEqual(gate_result('real', metrics)['status'], 'failed')
        self.assertEqual(gate_result('artificial_pi_boundary', metrics)['status'], 'known_diagnostic_failure')
        self.assertFalse(gate_result('artificial_pi_boundary', metrics)['blocking'])

    def test_amplitude_does_not_wrap_and_nonfinite_rejected(self):
        expected = [0.0] * 10800
        actual = expected.copy()
        actual[0] = 2 * math.pi
        self.assertFalse(compare_tokens(actual, expected, False)['amplitude_pass'])
        actual[0] = float('nan')
        with self.assertRaises(ValueError):
            compare_tokens(actual, expected, False)


if __name__ == '__main__':
    unittest.main()

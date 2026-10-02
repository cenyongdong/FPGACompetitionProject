"""Failure-oriented report tests: incomplete and contradictory EDA data cannot pass."""
import copy
import json
import unittest
import backend


class ReportGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((backend.RUNS / "build_20261001_120459_3fa8ba/rundir/lite_led_chaser_route.json").read_text())

    def test_missing_timing_field_raises(self):
        raw = copy.deepcopy(self.raw)
        del raw["Design Summary"]["item_data"]["Hold"]["Number of Failing Endpoints"]
        with self.assertRaises(KeyError):
            backend.validate_timing(raw)

    def test_missing_check_category_raises(self):
        raw = copy.deepcopy(self.raw)
        raw["Check Timing"]["item_data"] = [item for item in raw["Check Timing"]["item_data"] if item["Timing Check"] != "no_clock"]
        with self.assertRaises(ValueError):
            backend.validate_timing(raw)

    def test_violation_cannot_inherit_true_summary(self):
        raw = copy.deepcopy(self.raw)
        raw["Design Summary"]["item_data"]["Setup"]["Number of Failing Endpoints"] = 1
        self.assertFalse(backend.validate_timing(raw)["internal_timing_pass"])

    def test_new_unconstrained_output_cannot_pass_led_exception(self):
        raw = copy.deepcopy(self.raw)
        raw["Check Timing"]["no_output_delay"]["item_data"][0]["Name"] = "unknown_interface"
        self.assertFalse(backend.validate_timing(raw)["expected_led_output_exception"])

    def test_nonfinite_slack_raises(self):
        raw = copy.deepcopy(self.raw)
        raw["Design Summary"]["item_data"]["Setup"]["Worst Negative Slack (WNS)"] = "nan ns"
        with self.assertRaises(ValueError):
            backend.validate_timing(raw)


if __name__ == "__main__":
    unittest.main(verbosity=2)

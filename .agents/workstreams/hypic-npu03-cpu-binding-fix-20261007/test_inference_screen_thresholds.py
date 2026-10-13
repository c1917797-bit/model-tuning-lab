"""Negative controls for the historical first-screen gate."""
import unittest
from verify_inference_tuning_loop_case import screen_thresholds

def row(tpot=100, ttft=100):
    return {"tpot_weighted_ms": tpot, "ttft_p95_ms": ttft}

class ScreenTests(unittest.TestCase):
    def test_screen_failure_not_hidden_by_later_fast_repeats(self):
        # Later values 60/60 would make a three-repeat median pass.
        self.assertFalse(screen_thresholds([row()] * 3, row(90))["screen_tpot_pass"])

    def test_mean_not_median_denominator(self):
        result = screen_thresholds([row(50), row(50), row(200)], row(70))
        self.assertTrue(result["screen_tpot_pass"])
        self.assertEqual(result["baseline_tpot_mean_ms"], 100)

    def test_inclusive_thresholds(self):
        result = screen_thresholds([row()] * 3, row(80, 110))
        self.assertTrue(result["screen_tpot_pass"])
        self.assertEqual(result["ttft_verdict"], "pass-for-all-retained-rulers")

    def test_ttft_failure(self):
        result = screen_thresholds([row()] * 3, row(60, 111))
        self.assertEqual(result["ttft_verdict"], "fail-for-all-retained-rulers")

    def test_ambiguous_ttft_not_silently_passed(self):
        result = screen_thresholds([row(ttft=100), row(ttft=200), row(ttft=200)], row(60, 150))
        self.assertEqual(result["ttft_verdict"], "ambiguous-ruler")
        self.assertTrue(result["ttft_original_aggregation_unspecified"])

    def test_invalid_metrics(self):
        for bad in (0, -1, float("nan"), float("inf")):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                screen_thresholds([row()] * 3, row(bad))

    def test_missing_metric(self):
        with self.assertRaises(KeyError):
            screen_thresholds([row()] * 3, {"tpot_weighted_ms": 60})

    def test_incomplete_baselines(self):
        with self.assertRaises(RuntimeError):
            screen_thresholds([row()] * 2, row(60))

if __name__ == "__main__":
    unittest.main()

import math,unittest
from host_audits.r32_gate_cast_decision import decision
class PrespecifiedDecision(unittest.TestCase):
    def test_bounded_support_only(self):
        r=decision(100,90,102)
        self.assertEqual(r["state"],"SUPPORTED_BOUNDED_GATE_CAST_EFFECT")
        self.assertFalse(r["full_goal_complete"])
    def test_control_drift_overrules_apparent_gain(self):
        self.assertEqual(decision(100,70,120)["state"],"INCONCLUSIVE_CONTROL_DRIFT")
    def test_insufficient_gain_is_not_paper_rejection(self):
        r=decision(100,98,100)
        self.assertEqual(r["state"],"INSUFFICIENT_NET_GAIN_AT_SCREEN_THRESHOLD")
        self.assertGreater(r["B_gain_percent"],0)
    def test_actual_regression_retained(self):
        r=decision(100,120,100)
        self.assertLess(r["B_gain_percent"],0)
        self.assertEqual(r["B1_seconds"],120)
    def test_equal_control_results_stable(self):
        r=decision(100,95,100)
        self.assertEqual(r["control_relative_drift_percent"],0)
        self.assertAlmostEqual(r["B_gain_percent"],5)
    def test_invalid_times_rejected(self):
        for v in(float("nan"),float("inf"),0,-1,True,"100"):
            with self.subTest(v=v),self.assertRaises(ValueError):decision(100,v,100)
if __name__=="__main__":unittest.main()

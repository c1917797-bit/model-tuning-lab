"""SYNTHETIC stdlib domain contracts only; never operator or NPU evidence."""
import math
import unittest
from finite_contract import finite_receipt

class Tensor:
    def __init__(self, rows, width=(12,128)):
        self.rows = list(rows)
        self.shape = (len(rows),*width)
    def __getitem__(self, item):
        if not isinstance(item,slice):raise AssertionError("slice only")
        return Tensor(self.rows[item], self.shape[1:])
def finite(t):
    return all(math.isfinite(x) for x in t.rows)

class PaddingContracts(unittest.TestCase):
    def call(self, *, active=1, actual=None, expected=None, state=None,
             complete=None, native=None, metrics=(0.,0.,0.)):
        if actual is None:actual=Tensor([0.,0.])
        if expected is None:expected=Tensor([0.,float("nan")])
        if state is None:state={n:Tensor([0.,0.]) for n in
                           ("base","k_log","u_log","lambda_log","decay","length")}
        return finite_receipt(state,actual,expected,complete or Tensor([0.]),
                              native or Tensor([0.]),active,metrics,finite)
    def test_inactive_native_nan_only_undefined(self):
        expected=Tensor([0.,float("nan")]);before=list(expected.rows)
        r=self.call(expected=expected)
        self.assertTrue(r["finite"]);self.assertEqual(before,expected.rows)
        self.assertFalse(r["native_padding_values_rewritten"])
        self.assertEqual(r["native_expected_undefined_padding_rows"],1)
    def test_zero_active_native_entire_unwritten(self):
        self.assertTrue(self.call(active=0,expected=Tensor([float("nan"),float("inf")]))["finite"])
    def test_active_native_nan_rejected(self):
        self.assertFalse(self.call(expected=Tensor([float("nan"),0.]))["finite"])
    def test_active_native_inf_rejected(self):
        self.assertFalse(self.call(expected=Tensor([float("inf"),0.]))["finite"])
    def test_inactive_candidate_nan_not_ignored(self):
        self.assertFalse(self.call(actual=Tensor([0.,float("nan")]))["finite"])
    def test_zero_active_candidate_nan_not_ignored(self):
        self.assertFalse(self.call(active=0,actual=Tensor([float("nan"),0.]))["finite"])
    def test_all_six_complete_state_buffers(self):
        for name in ("base","k_log","u_log","lambda_log","decay","length"):
            with self.subTest(name=name):
                state={n:Tensor([0.]) for n in ("base","k_log","u_log","lambda_log","decay","length")}
                state[name]=Tensor([float("nan")])
                r=self.call(state=state)
                self.assertFalse(r["finite"])
                self.assertFalse(r["finite_buffer_checks"]["state."+name])
    def test_complete_logical_state_nan_rejected(self):
        self.assertFalse(self.call(complete=Tensor([float("nan")]))["finite"])
    def test_complete_native_state_nan_rejected(self):
        self.assertFalse(self.call(native=Tensor([float("nan")]))["finite"])
    def test_metric_nan_rejected(self):
        self.assertFalse(self.call(metrics=(0.,float("nan"),0.))["finite"])
    def test_shape_mismatch_rejected(self):
        with self.assertRaises(ValueError):self.call(expected=Tensor([0.]))
    def test_active_invalid_rejected(self):
        for value in (-1,3,True,1.0):
            with self.subTest(value=value),self.assertRaises(ValueError):self.call(active=value)
    def test_no_log_coverage_drop(self):
        with self.assertRaises(ValueError):self.call(state={"base":Tensor([0.])})
    def test_full_active_all_expected_checked(self):
        self.assertFalse(self.call(active=2)["finite"])
    def test_pass_thresholds_not_defined_or_changed_here(self):
        self.assertNotIn("OUT_LIMIT",globals())
        self.assertNotIn("STATE_LIMIT",globals())

if __name__=="__main__":unittest.main()

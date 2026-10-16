import unittest
from audit_r19_lazy_performance import validate_lazy_receipts
class Tests(unittest.TestCase):
    def rows(self,enabled):
        return [dict(event="compact_hypic_hooks_installed",c1_lazy_initial_snapshot=enabled) for _ in range(4)]+[dict(event="c1_packed_wave_prepared",requests=["r"]),dict(event="compact_gdn_body_composed",request_id="r",initial_snapshot_skipped=enabled)]
    def test_on(self):self.assertTrue(validate_lazy_receipts(self.rows(True),True)["lazy"])
    def test_off(self):self.assertFalse(validate_lazy_receipts(self.rows(False),False)["lazy"])
    def test_wrong_install(self):
        x=self.rows(True);x[0]["c1_lazy_initial_snapshot"]=False
        with self.assertRaises(ValueError):validate_lazy_receipts(x,True)
    def test_missing_receipt(self):
        with self.assertRaises(ValueError):validate_lazy_receipts(self.rows(True)[:-1],True)
    def test_wrong_or_ambiguous_receipt(self):
        for v in (False,None,1):
            x=self.rows(True);x[-1]["initial_snapshot_skipped"]=v
            with self.assertRaises(ValueError):validate_lazy_receipts(x,True)
    def test_wrong_worker_count(self):
        with self.assertRaises(ValueError):validate_lazy_receipts(self.rows(True)[1:],True)
    def test_native_prefill_fallback_retains(self):
        x=self.rows(True)+[dict(event="mixed_native_gdn_completed",request_id="fallback",initial_snapshot_skipped=False)]
        self.assertTrue(validate_lazy_receipts(x,True)["lazy"])
    def test_wrong_group_cannot_authorize_skip(self):
        x=self.rows(True);x[-1]["step"]=99
        with self.assertRaises(ValueError):validate_lazy_receipts(x,True)

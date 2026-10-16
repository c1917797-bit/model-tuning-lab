import unittest
from audit_r20_metadata_canary_v2 import audit_metadata_receipts
class Tests(unittest.TestCase):
    def rows(self,reads,hits):
        w={r:100+r for r in range(4)}
        return [dict(event="compact_model_rows_completed",rank=r,pid=100+r,step=1,manifest_sha256="m",forward_metadata_snapshot=True,metadata_snapshot_reads=reads,metadata_snapshot_hits=hits,request_ids=["a"])for r in range(4)],w
    def test_pure_three_groups(self):
        e,w=self.rows(9,135);self.assertEqual(audit_metadata_receipts(e,w,"m")["forwards"],4)
    def test_mixed_three_groups(self):
        e,w=self.rows(18,270);audit_metadata_receipts(e,w,"m")
    def test_bad_total(self):
        e,w=self.rows(9,134)
        with self.assertRaises(ValueError):audit_metadata_receipts(e,w,"m")
    def test_bad_group_width(self):
        e,w=self.rows(10,134)
        with self.assertRaises(ValueError):audit_metadata_receipts(e,w,"m")
    def test_no_reuse(self):
        e,w=self.rows(144,0)
        with self.assertRaises(ValueError):audit_metadata_receipts(e,w,"m")
    def test_wrong_pid(self):
        e,w=self.rows(9,135);e[0]["pid"]=999
        with self.assertRaises(ValueError):audit_metadata_receipts(e,w,"m")
    def test_missing_rank(self):
        e,w=self.rows(9,135)
        with self.assertRaises(ValueError):audit_metadata_receipts(e[:-1],w,"m")

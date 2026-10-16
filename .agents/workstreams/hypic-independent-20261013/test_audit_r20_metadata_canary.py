import unittest,copy
from audit_r20_metadata_canary import audit_metadata_receipts
class Tests(unittest.TestCase):
    def setup_rows(self):
        workers={r:100+r for r in range(4)}
        rows=[dict(event="compact_model_rows_completed",rank=r,pid=100+r,step=1,manifest_sha256="m",forward_metadata_snapshot=True,metadata_snapshot_reads=6,metadata_snapshot_hits=282,request_ids=["a","b"])for r in range(4)]
        return rows,workers
    def test_valid(self):
        rows,w=self.setup_rows();self.assertEqual(audit_metadata_receipts(rows,w,"m")["forwards"],4)
    def test_missing_rank(self):
        rows,w=self.setup_rows()
        with self.assertRaises(ValueError):audit_metadata_receipts(rows[:3],w,"m")
    def test_no_reuse(self):
        rows,w=self.setup_rows();rows[0]["metadata_snapshot_hits"]=0
        with self.assertRaises(ValueError):audit_metadata_receipts(rows,w,"m")
    def test_wrong_source(self):
        rows,w=self.setup_rows();rows[0]["manifest_sha256"]="wrong"
        with self.assertRaises(ValueError):audit_metadata_receipts(rows,w,"m")
    def test_duplicate(self):
        rows,w=self.setup_rows();rows.append(copy.deepcopy(rows[0]))
        with self.assertRaises(ValueError):audit_metadata_receipts(rows,w,"m")
    def test_boolean_count(self):
        rows,w=self.setup_rows();rows[0]["metadata_snapshot_reads"]=True
        with self.assertRaises(ValueError):audit_metadata_receipts(rows,w,"m")

import unittest
from audit_c1_pdc_coexistence import audit_pdc_requests

class PdcTests(unittest.TestCase):
    def fixture(self):
        mapping = {f"a{i}": f"a{i}-0" for i in range(16)}
        workers = {r: 50+r for r in range(4)}
        rows = [dict(event="native_request_progress", request_id=rid, rank=r, pid=pid,
                     computed_tokens=7680, scheduled_tokens=2048, step=1,
                     first_observed=True, manifest_sha256="m")
                for rid in mapping.values() for r,pid in workers.items()]
        caps = [dict(event="pic_scheduler_boundary_capped", request_id=rid,
                     native_block_size=1536, pic_start=9216, manifest_sha256="m")
                for rid in mapping.values()]
        return rows, caps, mapping, workers
    def test_valid(self):
        self.assertTrue(audit_pdc_requests(*self.fixture(), manifest_sha256="m")["pdc_coexistence_verified"])
    def test_missing_block_receipt(self):
        rows,caps,m,w=self.fixture()
        with self.assertRaises(ValueError):audit_pdc_requests(rows,caps[1:],m,w,manifest_sha256="m")
    def test_no_hit(self):
        rows,caps,m,w=self.fixture();rows[0]["computed_tokens"]=0
        with self.assertRaises(ValueError):audit_pdc_requests(rows,caps,m,w,manifest_sha256="m")
    def test_source_worker_block_and_count(self):
        for field,value in [("manifest_sha256","bad"),("pid",999)]:
            rows,caps,m,w=self.fixture();rows[0][field]=value
            with self.assertRaises(ValueError):audit_pdc_requests(rows,caps,m,w,manifest_sha256="m")
        rows,caps,m,w=self.fixture();caps[0]["native_block_size"]=1
        with self.assertRaises(ValueError):audit_pdc_requests(rows,caps,m,w,manifest_sha256="m")

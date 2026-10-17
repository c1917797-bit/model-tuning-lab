import unittest
from copy import deepcopy
from audit_r21_c2_finite_canary import audit_finite_receipts
class FiniteAudit(unittest.TestCase):
    def fixture(self):
        rows=[]
        for rank in range(4):
            base=dict(rank=rank,pid=60+rank,step=7,layer="layer",manifest_sha256="m")
            rows.append(dict(base,event="c2_layer_precommit_validated",requests=["a","b"],tensors=4,finite=True,actual_slot_commit="not_started"))
            rows.extend(dict(base,event="compact_c2_queries_completed",request_id=rid)for rid in ("a","b"))
        return rows
    def check(self,rows):return audit_finite_receipts(rows,dict(enumerate(range(60,64))),"m")
    def test_valid(self):self.assertEqual(self.check(self.fixture())["request_layer_completions"],8)
    def test_missing_gate(self):
        with self.assertRaises(ValueError):self.check(self.fixture()[1:])
    def test_late_gate(self):
        rows=self.fixture();rows[0],rows[1]=rows[1],rows[0]
        with self.assertRaises(ValueError):self.check(rows)
    def test_missing_completion(self):
        with self.assertRaises(ValueError):self.check(self.fixture()[:-1])
    def test_duplicate_completion(self):
        rows=self.fixture();rows.append(deepcopy(rows[-1]))
        with self.assertRaises(ValueError):self.check(rows)
    def test_wrong_identity(self):
        for field,value in (("pid",999),("manifest_sha256","bad"),("step",0),("rank",9)):
            rows=self.fixture();rows[0][field]=value
            with self.assertRaises(ValueError):self.check(rows)
    def test_wrong_gate(self):
        for field,value in (("finite",False),("tensors",2),("actual_slot_commit","completed"),("requests",["a","a"])):
            rows=self.fixture();rows[0][field]=value
            with self.assertRaises(ValueError):self.check(rows)
if __name__=="__main__":unittest.main()

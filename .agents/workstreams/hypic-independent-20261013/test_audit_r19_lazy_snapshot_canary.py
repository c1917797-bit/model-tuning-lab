import unittest,copy
from audit_r19_lazy_snapshot_canary import audit_snapshot_receipts
class AuditTests(unittest.TestCase):
    def rows(self):
        out=[]
        for r in range(4):
            for l in range(48):
                for step,skip in ((1,False),(2,True)):
                    e=dict(rank=r,pid=10+r,manifest_sha256="m",step=step,layer=str(l),request_id="r"+str(step))
                    if not skip:out.append(dict(e,event="c1_packed_wave_shadow_checked"))
                    out.append(dict(e,event="compact_gdn_body_composed",initial_snapshot_skipped=skip,finite=True))
        return out
    def audit(self,rows):return audit_snapshot_receipts(rows,{r:10+r for r in range(4)},"m")
    def test_exact_join(self):self.assertEqual(self.audit(self.rows())["receipts"],384)
    def test_shadow_must_retain(self):
        x=self.rows();x[1]["initial_snapshot_skipped"]=True
        with self.assertRaises(ValueError):self.audit(x)
    def test_nonshadow_must_skip(self):
        x=self.rows();x[2]["initial_snapshot_skipped"]=False
        with self.assertRaises(ValueError):self.audit(x)
    def test_missing_layer(self):
        with self.assertRaises(ValueError):self.audit(self.rows()[:-1])
    def test_duplicate(self):
        x=self.rows()
        with self.assertRaises(ValueError):self.audit(x+[copy.deepcopy(x[1])])
    def test_wrong_identity_and_ambiguous_flag(self):
        for field,value in (("pid",99),("manifest_sha256","bad"),("step",True),("initial_snapshot_skipped",1),("finite",False)):
            x=self.rows();x[1][field]=value
            with self.assertRaises(ValueError):self.audit(x)

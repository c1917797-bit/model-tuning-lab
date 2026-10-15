import copy,unittest
from test_audit_c1_packed_wave import PackedAuditTests
from audit_c1_packed_performance import audit_packed_performance

class PerformanceAuditTests(unittest.TestCase):
    def fixture(self):
        e,w,l=PackedAuditTests().fixture()
        e=[x for x in e if x["event"]!="c1_packed_wave_shadow_checked"]
        for x in e:
            if x["event"]=="compact_hypic_hooks_installed":
                x.update(c1_performance_mode=True,c1_layer_shadow_validation=False,c1_first_divergence=False)
        return e,w,l
    def audit(self,e,w,l):
        return audit_packed_performance(e,w,manifest_sha256="m",linear_layers=l,requests=["a","b"])
    def test_timed_receipts(self):
        e,w,l=self.fixture()
        self.assertTrue(self.audit(e,w,l)["packed_performance_receipts_verified"])
    def test_invalid_modes_and_private_order(self):
        for kind in ("mode","shadow","finite","generation","order","coverage"):
            e,w,l=self.fixture()
            if kind=="mode":e[0]["c1_performance_mode"]=False
            elif kind=="shadow":e.append({"event":"c1_packed_wave_shadow_checked"})
            elif kind=="finite":next(x for x in e if x["event"]=="c1_layer_precommit_validated")["finite"]=False
            elif kind=="generation":next(x for x in e if x["event"]=="compact_gdn_body_composed")["generation"]=2
            elif kind=="order":
                i=next(i for i,x in enumerate(e) if x["event"]=="compact_gdn_body_composed")
                e.insert(i-2,e.pop(i))
            else:e.pop(next(i for i,x in enumerate(e) if x["event"]=="compact_gdn_body_composed"))
            with self.assertRaises(ValueError):self.audit(e,w,l)

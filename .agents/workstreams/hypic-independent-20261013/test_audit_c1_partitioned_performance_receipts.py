"""Retain finite/ownership/generation/order checks under actual partition counters."""
import unittest
import test_c1_performance_audit as fixtures
from audit_c1_partitioned_performance_receipts import audit_partitioned_performance_receipts

class PartitionReceiptTests(unittest.TestCase):
    def fixture(self):
        e,w,l=fixtures.PerformanceAuditTests().fixture()
        for x in e:
            if x["event"]=="c1_packed_wave_prepared":
                x.update(state_passes=2,state_schedule="partitioned",
                    state_window_visits=x["windows"],state_token_visits=x["packed_tokens"],
                    seed_mode="actual_prefix_terminal")
        return e,w,l
    def audit(self,e,w,l):
        return audit_partitioned_performance_receipts(e,w,manifest_sha256="m",
            linear_layers=l,requests=["a","b"],seed_mode="actual_prefix_terminal")
    def test_two_partition_dispatches(self):
        e,w,l=self.fixture();self.assertTrue(self.audit(e,w,l)["packed_performance_receipts_verified"])
    def test_prefix_only_dispatch(self):
        e,w,l=self.fixture()
        for x in e:
            if x["event"]=="c1_packed_wave_prepared":x["state_passes"]=1
        self.assertTrue(self.audit(e,w,l)["packed_performance_receipts_verified"])
    def test_retained_gate_rejections(self):
        for kind in ("mode","shadow","finite","generation","order","coverage","slot_alias","double_visits","missing_visits","wrong_seed","boolean_count"):
            with self.subTest(kind=kind):
                e,w,l=self.fixture()
                prep=next(x for x in e if x["event"]=="c1_packed_wave_prepared")
                if kind=="mode":e[0]["c1_performance_mode"]=False
                elif kind=="shadow":e.append({"event":"c1_packed_wave_shadow_checked"})
                elif kind=="finite":next(x for x in e if x["event"]=="c1_layer_precommit_validated")["finite"]=False
                elif kind=="generation":next(x for x in e if x["event"]=="compact_gdn_body_composed")["generation"]=2
                elif kind=="order":
                    i=next(i for i,x in enumerate(e) if x["event"]=="compact_gdn_body_composed")
                    e.insert(i-2,e.pop(i))
                elif kind=="coverage":e.pop(next(i for i,x in enumerate(e) if x["event"]=="compact_gdn_body_composed"))
                elif kind=="slot_alias":
                    commit=next(x for x in e if x["event"]=="compact_gdn_body_composed")
                    other=next(x for x in e if x["event"]in ("compact_gdn_body_composed","mixed_native_gdn_completed")
                        and x["rank"]==commit["rank"] and x["step"]==commit["step"]
                        and x["layer"]==commit["layer"] and x["request_id"]!=commit["request_id"])
                    other["slot"]=commit["slot"]
                elif kind=="double_visits":prep["state_token_visits"]*=2
                elif kind=="missing_visits":prep["state_window_visits"]=0
                elif kind=="wrong_seed":prep["seed_mode"]="dummy"
                else:prep["state_window_visits"]=True
                with self.assertRaises(ValueError):self.audit(e,w,l)

if __name__=="__main__":unittest.main()

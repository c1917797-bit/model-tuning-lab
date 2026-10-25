"""Actual parent/native id counterexample plus retained strict negative gates."""
import copy,unittest
from host_audits.r32b_gate_cast_audit import audit_gate_cast_evidence
from host_audits.test_r32_gate_cast_audit import fixture
API="cmpl-b95c439efa3c12cd"
RID=API+"-0-9829bf5c"
def actual(arm="A1"):
    f=list(fixture(arm));f[1]=[API]
    for e in f[0]:
        if e["event"]=="c1_gate_cast_placement_observed":e["request_ids"]=[RID]
    for rank,pid in f[2]["workers"].items():
        f[0].append({"event":"compact_gdn_body_composed","rank":rank,"pid":pid,"request_id":RID})
    return f
class NativeIdJoin(unittest.TestCase):
    def test_real_parent_suffix_format_and_both_arms(self):
        for arm in("A1","B1","A2"):
            r=audit_gate_cast_evidence(*actual(arm))
            self.assertEqual(r["response_internal_join"],{API:RID})
            self.assertEqual(r["timed_observations"],4)
    def test_native_request_without_short_span_is_not_invented_exposure(self):
        f=actual();other="cmpl-no-short-span";f[1].append(other)
        f[0].append({"event":"compact_gdn_body_composed","request_id":other+"-0-cafe1234"})
        r=audit_gate_cast_evidence(*f)
        self.assertEqual(len(r["response_internal_join"]),2)
        self.assertEqual(r["timed_observations"],4)
    def test_missing_or_ambiguous_native_id_rejected(self):
        for ambiguity in(False,True):
            f=actual()
            if ambiguity:f[0].append({"event":"compact_gdn_body_composed","request_id":API+"-0-different"})
            else:f[1]=["cmpl-unrelated"]
            with self.subTest(ambiguity=ambiguity),self.assertRaises(ValueError):audit_gate_cast_evidence(*f)
    def test_prefix_collision_without_separator_rejected(self):
        f=actual();f[1]=[API[:-1]]
        with self.assertRaises(ValueError):audit_gate_cast_evidence(*f)
    def test_warmup_gate_retained(self):
        f=actual();next(e for e in f[0]if e["event"]=="c1_gate_cast_placement_observed")["first_shape_already_validated"]=False
        with self.assertRaises(ValueError):audit_gate_cast_evidence(*f)
    def test_numeric_cpu_wrong_pid_and_manifest_rejected(self):
        for event,key,value in(("c1_gate_cast_first_shape_checked","passed",False),
            ("c1_gate_cast_first_shape_checked","device","cpu"),
            ("c1_gate_cast_placement_observed","pid",999),
            ("c1_gate_cast_placement_observed","manifest_sha256","b"*64)):
            f=actual();next(e for e in f[0]if e["event"]==event)[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):audit_gate_cast_evidence(*f)
    def test_dispatch_control_and_rank_activation_retained(self):
        f=actual("B1");next(e for e in f[0]if e["event"]=="c1_gate_cast_placement_observed")["gate_conversion_dispatch_sites"]=16
        with self.assertRaises(ValueError):audit_gate_cast_evidence(*f)
if __name__=="__main__":unittest.main()

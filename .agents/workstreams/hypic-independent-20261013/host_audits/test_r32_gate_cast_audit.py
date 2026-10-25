"""Negative controls for real R32 source-executed evidence validator."""
import copy,unittest
from host_audits.r32_gate_cast_audit import audit_gate_cast_evidence

MANIFEST="a"*64
def fixture(arm="A1"):
    wanted=arm=="B1";workers={r:58+r for r in range(4)};events=[]
    for rank,pid in workers.items():
        base={"rank":rank,"pid":pid,"manifest_sha256":MANIFEST,"hoisted":wanted}
        events.append(dict(base,event="c1_gate_cast_placement_installed"))
        events.append(dict(base,event="c1_gate_cast_first_shape_checked",device="npu:"+str(rank),passed=True,full_private_output_and_state=True))
        events.append(dict(base,event="c1_gate_cast_placement_observed",length=8,gate_conversion_dispatch_sites=2 if wanted else 16,request_ids=["measured"],first_shape_already_validated=True))
    return events,["measured"],{"workers":workers},MANIFEST,arm
class IndependentEvidence(unittest.TestCase):
    def test_both_valid_arms(self):
        for arm in("A1","B1","A2"):
            report=audit_gate_cast_evidence(*fixture(arm))
            self.assertEqual(report["observations"],4);self.assertEqual(report["actual_npu_private_shape_checks"],4)
    def test_wrong_pid_rejected(self):
        f=list(fixture());f[0][-1]["pid"]=999
        with self.assertRaises(ValueError):audit_gate_cast_evidence(*f)
    def test_wrong_conversion_count_rejected(self):
        f=list(fixture("B1"));f[0][-1]["gate_conversion_dispatch_sites"]=16
        with self.assertRaises(ValueError):audit_gate_cast_evidence(*f)
    def test_wrong_boolean_or_manifest_rejected(self):
        for key,value in(("hoisted",1),("manifest_sha256","b"*64)):
            f=list(fixture("B1"));f[0][-1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):audit_gate_cast_evidence(*f)
    def test_unwarmed_timed_shape_rejected(self):
        f=list(fixture());f[0][-1]["first_shape_already_validated"]=False
        with self.assertRaises(ValueError):audit_gate_cast_evidence(*f)
    def test_cpu_or_failed_numeric_shadow_rejected(self):
        for key,value in(("device","cpu"),("passed",False),("full_private_output_and_state",False)):
            f=list(fixture());f[0][-2][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):audit_gate_cast_evidence(*f)
    def test_missing_rank_install_or_shadow_rejected(self):
        for name in("c1_gate_cast_placement_installed","c1_gate_cast_first_shape_checked"):
            f=list(fixture());f[0]=[e for e in f[0]if not(e["event"]==name and e["rank"]==3)]
            with self.subTest(name=name),self.assertRaises(ValueError):audit_gate_cast_evidence(*f)
if __name__=="__main__":unittest.main()

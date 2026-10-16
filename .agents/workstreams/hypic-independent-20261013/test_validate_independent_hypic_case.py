import copy,hashlib,tempfile,unittest
from pathlib import Path
from validate_independent_hypic_case import check_scope,verify_bindings,replay_phase,SKILLS,STATUS
from unittest.mock import patch
import subprocess
class CaseTests(unittest.TestCase):
    def case(self):
        return dict(status=STATUS,full_goal_accepted=False,skill_mapping=[{"skill":s} for s in SKILLS],
            skill_sources={s:"a"*64 for s in SKILLS},remaining=["fullmatrix","quality","lifecycle"],
            evidence={"summary.json":{"sha256":"a"*64},"contract.json":{"sha256":"b"*64}},
            new_valid_phase=dict(requests=40,independent_audit_exit=0,summary="summary.json",
                contract="contract.json",optimization_accepted=False,quality_accepted=False,lifecycle_accepted=False))
    def test_partial_scope(self):self.assertEqual(check_scope(self.case())["requests"],40)
    def test_no_full_goal_lift(self):
        c=self.case();c["full_goal_accepted"]=True
        with self.assertRaises(ValueError):check_scope(c)
    def test_no_speedup_lift(self):
        c=self.case();c["new_valid_phase"]["optimization_accepted"]=True
        with self.assertRaises(ValueError):check_scope(c)
    def test_no_quality_lift(self):
        c=self.case();c["new_valid_phase"]["quality_accepted"]=True
        with self.assertRaises(ValueError):check_scope(c)
    def test_missing_skill(self):
        c=self.case();c["skill_mapping"].pop()
        with self.assertRaises(ValueError):check_scope(c)
    def test_boolean_audit_exit_rejected(self):
        c=self.case();c["new_valid_phase"]["independent_audit_exit"]=False
        with self.assertRaises(ValueError):check_scope(c)
    def test_boolean_request_count_rejected(self):
        c=self.case();c["new_valid_phase"]["requests"]=True
        with self.assertRaises(ValueError):check_scope(c)
    def test_remaining_required(self):
        c=self.case();c["remaining"]=[]
        with self.assertRaises(ValueError):check_scope(c)
    def test_full40_required(self):
        c=self.case();c["new_valid_phase"]["requests"]=39
        with self.assertRaises(ValueError):check_scope(c)
    def test_evidence_hash_required(self):
        c=self.case();del c["evidence"]["summary.json"]
        with self.assertRaises(ValueError):check_scope(c)
    def test_checksum_and_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.json";p.write_text("{}");binding={"a.json":{"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}}
            verify_bindings(d,binding);p.write_text('{"changed":true}')
            with self.assertRaises(ValueError):verify_bindings(d,binding)
    def test_no_escape(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):verify_bindings(d,{"../other":{"sha256":"a"*64}})
    def test_bad_hash(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):verify_bindings(d,{"a":{"sha256":"notahash"}})
    def test_replay_uses_explicit_case_cwd_and_no_live_device_probe(self):
        with patch("validate_independent_hypic_case.subprocess.check_output",return_value='{"verified":true}') as call:
            self.assertTrue(replay_phase("/owned/case","/owned/case/contract.json")["verified"])
            args,kwargs=call.call_args
            self.assertEqual(kwargs["cwd"],"/owned/case")
            self.assertNotIn("--run",args[0]);self.assertNotIn("--live-release",args[0])
            self.assertEqual(kwargs["timeout"],600)
    def test_replay_timeout_is_not_silently_accepted(self):
        with patch("validate_independent_hypic_case.subprocess.check_output",side_effect=subprocess.TimeoutExpired("audit",600)):
            with self.assertRaises(subprocess.TimeoutExpired):replay_phase("/owned/case","/owned/case/contract.json")
if __name__=="__main__":unittest.main()

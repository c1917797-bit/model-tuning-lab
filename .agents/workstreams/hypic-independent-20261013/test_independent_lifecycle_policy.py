import ast,copy,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from independent_lifecycle_policy import lifecycle_mode,validate_lifecycle_sources,semantic_payload,check_semantic,lifecycle_payloads
class Tests(unittest.TestCase):
    def contract(self,stage="enabled"):
        c=dict(lifecycle_stage=stage,enable_prefix_caching=False,enable_thinking=False,enforce_eager=True,completion=True,
            lifecycle_private_output_tokens=64,max_output_tokens=64,formal_token_artifact={"frozen":True})
        if stage=="uninstalled":c["baseline_host_source_sha256"]={"a":"hash"}
        else:c["cache_diagnostic"]={"compact_manifest":"manifest.json","source_sha256":{"a":"hash"}}
        return c
    def test_enabled(self):self.assertEqual(lifecycle_mode(self.contract()),("enabled",True))
    def test_disabled(self):self.assertEqual(lifecycle_mode(self.contract("disabled")),("disabled",False))
    def test_uninstalled(self):self.assertEqual(lifecycle_mode(self.contract("uninstalled")),("uninstalled",False))
    def test_bad_stage(self):
        c=self.contract();c["lifecycle_stage"]="other"
        with self.assertRaises(ValueError):lifecycle_mode(c)
    def test_formal_modes_rejected(self):
        for k in ("formal_quality","formal_quality_canary","formal_performance"):
            c=self.contract();c[k]=True
            with self.assertRaises(ValueError):lifecycle_mode(c)
    def test_uninstalled_mount_rejected(self):
        c=self.contract("uninstalled");c["cache_diagnostic"]={"compact_manifest":"x"}
        with self.assertRaises(ValueError):lifecycle_mode(c)
    def test_disabled_no_manifest_rejected(self):
        c=self.contract("disabled");c["cache_diagnostic"]={}
        with self.assertRaises(ValueError):lifecycle_mode(c)
    def test_output_rule(self):
        c=self.contract();c["max_output_tokens"]=1024
        with self.assertRaises(ValueError):lifecycle_mode(c)
    def test_source_binding(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/"a";p.write_text("bound");c=self.contract()
            c["cache_diagnostic"]["source_sha256"]={"a":hashlib.sha256(p.read_bytes()).hexdigest()}
            self.assertEqual(validate_lifecycle_sources(c,d),1);p.write_text("changed")
            with self.assertRaises(ValueError):validate_lifecycle_sources(c,d)
    def test_payload_bounding(self):
        p=[dict(prompt=[i],max_tokens=1024,ignore_eos=True)for i in range(3)]
        with patch("independent_formal_canary.load_formal_canary",return_value=p):
            out=lifecycle_payloads({"bound":True})
        self.assertEqual([x["max_tokens"]for x in out],[1,64,64]);self.assertEqual(p[1]["max_tokens"],1024)
    def test_semantic(self):
        self.assertTrue(check_semantic(dict(id="id",choices=[dict(message=dict(content="4"))],usage=dict(completion_tokens=1))))
        self.assertFalse(semantic_payload()["chat_template_kwargs"]["enable_thinking"])
    def test_semantic_wrong(self):
        with self.assertRaises(ValueError):check_semantic(dict(id="id",choices=[dict(message=dict(content="5"))],usage=dict(completion_tokens=1)))
    def test_declared_controller_spans_only(self):
        old=Path("formal_r15_tp4.py").read_text();new=Path("lifecycle_r16_tp4.py").read_text()
        changes=[["    from independent_execution_deadline import deadline_epoch,deadline_reached","    from independent_lifecycle_policy import lifecycle_mode,validate_lifecycle_sources\n    stage,treatment_on=lifecycle_mode(contract)\n    validate_lifecycle_sources(contract,HERE)\n    from independent_execution_deadline import deadline_epoch,deadline_reached"],["        from independent_formal_canary import load_formal_canary\n        formal_payloads=load_formal_canary(formal_artifact)","        from independent_lifecycle_policy import lifecycle_payloads\n        formal_payloads=lifecycle_payloads(formal_artifact)"],["\"-e\",\"INDEPENDENT_COMPACT_HYPIC=1\",","\"-e\",\"INDEPENDENT_COMPACT_HYPIC=\"+(\"1\" if treatment_on else \"0\"),"],["\"--host\",\"0.0.0.0\",","\"--host\",\"127.0.0.1\","],["        valid=True","        from independent_lifecycle_worker_controls import capture_worker_controls\n        control_snapshot=snapshot(cid);retain_snapshot(control_snapshot)\n        control_record={\"event\":\"lifecycle-worker-startup-controls\",\"stage\":stage,\"container_id\":cid,\n            \"snapshot_utc\":control_snapshot[\"utc\"],\"workers\":capture_worker_controls(control_snapshot,cid)}\n        write(raw,\"lifecycle-worker-controls.json\",control_record);journal.append(control_record)\n        from independent_lifecycle_policy import semantic_payload,check_semantic\n        semantic_body=semantic_payload();require_guard()\n        semantic_response=request(port,semantic_body,completion=False,timeout=120)\n        semantic_record={\"event\":\"lifecycle-semantic\",\"stage\":stage,\"payload\":semantic_body,\"response\":semantic_response}\n        write(raw,\"lifecycle-semantic.json\",semantic_record);journal.append(semantic_record)\n        require_guard();check_semantic(semantic_response)\n        valid=True"]]
        changes.append(['        release["final_physical_processes"]=final["processes"]','        release["final_physical_processes"]=final["processes"]\n        release["utc"]=final["utc"]'])
        for before,after in changes:
            self.assertEqual(new.count(after),1);new=new.replace(after,before)
        new=new.replace('CONTRACT = HERE / "LIFECYCLE_R16_CONTRACT.json"','CONTRACT = HERE / "NATIVE_SMOKE_CONTRACT.json"')
        a=ast.parse(old);b=ast.parse(new)
        self.assertEqual(ast.dump(ast.Module(body=a.body[1:],type_ignores=[])),ast.dump(ast.Module(body=b.body[1:],type_ignores=[])))
if __name__=="__main__":unittest.main()

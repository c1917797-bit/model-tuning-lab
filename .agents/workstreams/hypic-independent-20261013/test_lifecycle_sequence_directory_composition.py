"""Synthetic three-directory composition, with only input loading mocked."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_audit_lifecycle_terminal as fixtures
from audit_lifecycle_sequence import audit_sequence

def rewrite(path,mutate):
    d=json.loads(path.read_text());mutate(d);path.write_text(json.dumps(d))

class Tests(unittest.TestCase):
    def scenario(self,mutate=lambda base,raws,contracts:None):
        with tempfile.TemporaryDirectory()as td:
            base=Path(td);src=base/"lifecycle_r16_tp4.py";src.write_text("# fixture controller, never executed\n")
            digest=hashlib.sha256(src.read_bytes()).hexdigest();sources={"lifecycle_r16_tp4.py":digest}
            (base/"m.json").write_text(json.dumps({"source_sha256":sources}))
            paths=[];raws=[];payloads=None
            for i,stage in enumerate(("disabled","enabled","uninstalled")):
                a=fixtures.fixture(stage)
                c,result,journal,samples,start,release,records,semantic,controls,launch,payloads=a
                raw=base/("raw-"+stage);raw.mkdir();raws.append(raw)
                cid=str(i+1)*64;start["container_id"]=cid;release.update(owned_container=cid,utc="2026-10-16T12:0"+str(2*i+1)+":00Z");controls["container_id"]=cid
                for owner in samples[0]["owners"]:owner["cgroup"]="/docker/"+cid
                c.update(raw_root=str(raw),controller_sha256=digest,model="/model",model_config_sha256="hash",cpu_set="112-191",hccl_ports=[26300,26400],absolute_stop_utc="2026-10-17T06:48:09Z")
                diagnostic=c.get("cache_diagnostic")
                if diagnostic:diagnostic["source_sha256"]=copy.deepcopy(sources)
                else:c["baseline_host_source_sha256"]=copy.deepcopy(sources)
                launch.update(controller_sha256=digest,diagnostic_sources=copy.deepcopy(diagnostic))
                launch["argv"]=[x.replace("/pkg:/probe:ro",str(base)+":/probe:ro")for x in launch["argv"]]
                pre=dict(utc="2026-10-16T12:0"+str(2*i)+":00Z",processes=[],foreign=[])
                journal=[dict(event="preflight",snapshot=pre)]+[dict(r,event="response")for r in records]+[semantic]+[dict(event="isolation",snapshot=s)for s in samples]+[controls,dict(event="terminal",result=result)]
                for name,obj in {"result.json":result,"responses.json":records,"isolation.json":samples,"service-start.json":start,"release.json":release,"launch.json":launch,"lifecycle-semantic.json":semantic,"lifecycle-worker-controls.json":controls}.items():(raw/name).write_text(json.dumps(obj))
                (raw/"events.jsonl").write_text("".join(json.dumps(e)+"\n"for e in journal))
                if stage=="enabled":fixtures.write_hot_fixture(base,raw,sources)
                cp=base/(stage+".json");cp.write_text(json.dumps(c));paths.append(cp)
            mutate(base,raws,paths)
            with patch("audit_lifecycle_terminal.lifecycle_payloads",return_value=payloads):return audit_sequence(paths)
    def test_full_three_directory_chain(self):
        r=self.scenario();self.assertTrue(r["lifecycle_sequence_audited"]);self.assertEqual([a["stage"]for a in r["stage_audits"]],["disabled","enabled","uninstalled"])
        self.assertEqual(len(r["container_ids"]),3);self.assertEqual(len(r["artifacts"]),3);self.assertFalse(r["live_release_verified"])
    def test_shared_source_tampering(self):
        with self.assertRaisesRegex(ValueError,"source drift"):self.scenario(lambda base,raws,c:(base/"lifecycle_r16_tp4.py").write_text("changed"))
    def test_enabled_missing_worker_file(self):
        with self.assertRaises(ValueError):self.scenario(lambda base,raws,c:(raws[1]/"diagnostics"/"compact-worker-0.jsonl").unlink())
    def test_uninstalled_mount_residue(self):
        with self.assertRaises(ValueError):self.scenario(lambda base,raws,c:rewrite(raws[2]/"launch.json",lambda d:d["argv"].extend(["-v",str(base)+":/probe:ro"])))
    def test_model_protocol_drift(self):
        with self.assertRaisesRegex(ValueError,"same source/image/model"):self.scenario(lambda base,raws,c:rewrite(c[2],lambda d:d.update(model="/different")))
    def test_release_start_overlap_consistent_artifacts(self):
        def mutate(base,raws,c):
            value="2026-10-16T12:04:00Z"
            rewrite(raws[0]/"release.json",lambda d:d.update(utc=value))
            rewrite(raws[0]/"result.json",lambda d:d["release"].update(utc=value))
            p=raws[0]/"events.jsonl";rows=[json.loads(x)for x in p.read_text().splitlines()]
            rows[-1]["result"]["release"]["utc"]=value;p.write_text("".join(json.dumps(e)+"\n"for e in rows))
        with self.assertRaisesRegex(ValueError,"chronology"):self.scenario(mutate)
if __name__=="__main__":unittest.main()

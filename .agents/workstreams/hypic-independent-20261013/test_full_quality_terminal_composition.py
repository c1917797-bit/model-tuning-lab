"""Synthetic full381 native-arm raw-directory composition; scorer mocked."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_audit_full_quality_cohort as fixtures
from independent_segment_selection import token_digest
from audit_full_quality_terminal import audit
class Tests(unittest.TestCase):
    def score(self,task,text,reference):return text,text==reference
    def fixture(self,root):
        rows,unit,journal=fixtures.Tests().fixture()
        digests={i:token_digest([i]*16)for i in range(127)}
        for row in rows:
            i=row["index"];row["token_ids"]=[100000+i]*8+[i]*16+[200000+i]*8
            row["segment"]["tokens_sha256"]=digests[i]
        for item in unit["results"]:item["segment_sha256"]=digests[item["index"]]
        for e in journal:
            if "segment_sha256"in e:
                i=e.get("index",int(e["segment_sha256"])if e["event"]=="quality-public-producer"else 0)
                e["segment_sha256"]=digests[i]
        def write(path,obj):
            path.write_text(json.dumps(obj));return hashlib.sha256(path.read_bytes()).hexdigest()
        ih=write(root/"inputs.json",dict(schema="hypic-quality-inputs/v1",requests=rows,repetitions=3,
            generation=dict(max_tokens=1024,temperature=0,seed=0,ignore_eos=False,enable_thinking=False)))
        ch=write(root/"catalog.json",dict(schema="hypic-public-catalog/v1",public_segments=[[i]*16 for i in range(127)]))
        (root/"formal_quality_r16_tp4.py").write_text("# synthetic bound controller, not executed\n")
        ctrl=hashlib.sha256((root/"formal_quality_r16_tp4.py").read_bytes()).hexdigest()
        raw=root/"raw";raw.mkdir()
        c=dict(formal_quality=True,physical_npus=[0,1,2,3],tp=4,image="image",enable_thinking=False,max_output_tokens=1024,
            enable_prefix_caching=False,raw_root=str(raw),controller_sha256=ctrl,
            baseline_host_source_sha256={"formal_quality_r16_tp4.py":ctrl},
            quality_workload=dict(inputs=dict(path=str(root/"inputs.json"),sha256=ih),
                catalog=dict(path=str(root/"catalog.json"),sha256=ch),ruler_path="MOCKED",batch_samples=8))
        cp=root/"contract.json";write(cp,c)
        start=dict(container_id="a"*64,image="image",devices=["/dev/davinci"+str(i)for i in range(4)])
        release=dict(owned_container="a"*64,removed=True,port_free=True,final_physical_processes=[])
        samples=[dict(foreign=[],owners=[dict(npu=i,owned=True,ownership_status="owned-cgroup",cgroup="/docker/"+"a"*64)for i in range(4)])]
        result=dict(valid=True,error=None,guard_errors=[],responses=381,isolation_samples=1,release=release)
        journal.extend([dict(event="isolation",snapshot=samples[0]),dict(event="terminal",result=result)])
        for n,obj in (("quality-unit.json",unit),("responses.json",unit["results"]),("result.json",result),
            ("isolation.json",samples),("service-start.json",start),("release.json",release),
            ("launch.json",dict(argv=["vllm","serve","/model"],diagnostic_sources=None))):write(raw/n,obj)
        (raw/"events.jsonl").write_text("".join(json.dumps(e)+"\n"for e in journal))
        return cp,raw
    def run_audit(self,cp):
        with patch("audit_full_quality_terminal.load_ruler",return_value={"score_case":self.score}):return audit(cp)
    def test_full_native381_composition(self):
        with tempfile.TemporaryDirectory()as d:
            cp,raw=self.fixture(Path(d));r=self.run_audit(cp)
            self.assertTrue(r["full_quality_arm_audited"]);self.assertEqual(r["cohort"]["requests"],381)
            self.assertEqual(r["cohort"]["correct"],189);self.assertIsNone(r["hot"])
            self.assertFalse(r["live_release_verified"]);self.assertEqual(r["quality_acceptance"],"NOT_DECIDED")
    def test_native_treatment_environment_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            cp,raw=self.fixture(Path(d));p=raw/"launch.json";x=json.loads(p.read_text())
            x["argv"].append("INDEPENDENT_COMPACT_HYPIC=1");p.write_text(json.dumps(x))
            with self.assertRaisesRegex(ValueError,"treatment"):self.run_audit(cp)
    def test_source_drift_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            cp,raw=self.fixture(Path(d));(Path(d)/"formal_quality_r16_tp4.py").write_text("changed")
            with self.assertRaisesRegex(ValueError,"source"):self.run_audit(cp)
    def test_membership_rehashed_drift_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            cp,raw=self.fixture(Path(d));c=json.loads(cp.read_text());p=Path(c["quality_workload"]["inputs"]["path"])
            x=json.loads(p.read_text());x["requests"][0]["token_ids"][8]+=1;p.write_text(json.dumps(x))
            c["quality_workload"]["inputs"]["sha256"]=hashlib.sha256(p.read_bytes()).hexdigest();cp.write_text(json.dumps(c))
            with self.assertRaisesRegex(ValueError,"membership"):self.run_audit(cp)
if __name__=="__main__":unittest.main()

import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from audit_lifecycle_terminal import audit,audit_terminal_records
import test_audit_lifecycle_startup_controls as startup_fixture
import test_audit_lifecycle_requests as request_fixture

def write_hot_fixture(base,raw,sources,mutate_hot=lambda e:None):
    manifest={"source_sha256":copy.deepcopy(sources)}
    mp=base/"m.json";mp.write_text(json.dumps(manifest));mh=hashlib.sha256(mp.read_bytes()).hexdigest()
    diag=raw/"diagnostics";diag.mkdir();events=[]
    for rank in range(4):
        pid=50+rank;common=dict(rank=rank,pid=pid,manifest_sha256=mh)
        events.append(dict(common,event="compact_hypic_hooks_installed"))
        for layer in range(48):events.append(dict(common,event="compact_public_state_published",layer="gdn"+str(layer)))
        for layer in range(16):events.append(dict(common,event="compact_public_kv_published",layer="kv"+str(layer)))
        for i in (1,2):
            rid="r"+str(i)+"-runtime";step=i+2
            events.append(dict(common,event="native_request_progress",request_id=rid,step=step,scheduled_tokens=32768))
            events.append(dict(common,event="compact_model_rows_completed",request_ids=[rid],step=step,original_rows=32768,retained_rows=16392))
            for layer in range(48):events.append(dict(common,event="compact_gdn_body_composed",request_id=rid,step=step,layer="gdn"+str(layer),skipped_body_tokens=16376,retained_rows=16392,finite=True))
            for layer in range(16):events.append(dict(common,event="compact_c2_queries_completed",request_id=rid,step=step,layer="kv"+str(layer),skipped_body_queries=16376,retained_rows=16392))
    mutate_hot(events)
    for rank in range(4):(diag/("compact-worker-"+str(rank)+".jsonl")).write_text("".join(json.dumps(e)+"\n"for e in events if e["rank"]==rank))

def fixture(stage="disabled"):
    controls,c,samples,start,launch=startup_fixture.Tests().fixture(stage)
    c.update(physical_npus=[0,1,2,3],tp=4,image="image",enable_prefix_caching=False,enable_thinking=False,enforce_eager=True,completion=True,lifecycle_private_output_tokens=64,max_output_tokens=64,formal_token_artifact={"path":"/unused","sha256":"x"},port=8233)
    if stage=="uninstalled":c["baseline_host_source_sha256"]={"lifecycle_r16_tp4.py":"placeholder"}
    else:c["cache_diagnostic"]["source_sha256"]={"lifecycle_r16_tp4.py":"placeholder"}
    start.update(image="image",devices=["/dev/davinci"+str(i)for i in range(4)])
    records,journal,semantic,_,payloads=request_fixture.Tests().fixture(stage)
    release=dict(owned_container=start["container_id"],removed=True,port_free=True,final_physical_processes=[])
    result=dict(valid=True,error=None,guard_errors=[],responses=3,isolation_samples=len(samples),release=release)
    journal+=[dict(event="isolation",snapshot=copy.deepcopy(x))for x in samples]
    journal+=[copy.deepcopy(controls),dict(event="terminal",result=copy.deepcopy(result))]
    return c,result,journal,samples,start,release,records,semantic,controls,launch,payloads

class Records(unittest.TestCase):
    def test_stages(self):
        for s in ("disabled","enabled","uninstalled"):self.assertEqual(audit_terminal_records(*fixture(s)[:6])[0],s)
    def reject(self,mutate):
        a=fixture();mutate(*a[:6])
        with self.assertRaises(ValueError):audit_terminal_records(*a[:6])
    def test_terminal_false(self):self.reject(lambda c,r,j,s,start,rel:r.update(valid=False))
    def test_guard_failure(self):self.reject(lambda c,r,j,s,start,rel:r.update(guard_errors=[1]))
    def test_foreign(self):
        def mutate(c,r,j,s,start,rel):
            s[0]["foreign"]=[1]
            for e in j:
                if e.get("event")=="isolation":e["snapshot"]=copy.deepcopy(s[0])
        self.reject(mutate)
    def test_isolation_journal(self):self.reject(lambda c,r,j,s,start,rel:s.append(copy.deepcopy(s[0])))
    def test_wrong_release_cid(self):
        def mutate(c,r,j,s,start,rel):
            rel["owned_container"]="b"*64;r["release"]=copy.deepcopy(rel);j[-1]["result"]=copy.deepcopy(r)
        self.reject(mutate)
    def test_residual_process(self):
        def mutate(c,r,j,s,start,rel):
            rel["final_physical_processes"]=[[0,123]];r["release"]=copy.deepcopy(rel);j[-1]["result"]=copy.deepcopy(r)
        self.reject(mutate)
    def test_wrong_devices(self):self.reject(lambda c,r,j,s,start,rel:start.update(devices=["/dev/davinci4"]))
    def test_wrong_image(self):self.reject(lambda c,r,j,s,start,rel:start.update(image="other"))
    def test_duplicate_terminal(self):self.reject(lambda c,r,j,s,start,rel:j.append(copy.deepcopy(j[-1])))

class DirectoryComposition(unittest.TestCase):
    def run_fixture(self,stage="disabled",mutate=lambda a:None,with_hot=False,mutate_hot=lambda e:None):
        with tempfile.TemporaryDirectory()as td:
            base=Path(td);raw=base/"raw";raw.mkdir()
            a=fixture(stage);c,result,journal,samples,start,release,records,semantic,controls,launch,payloads=a
            src=base/"lifecycle_r16_tp4.py";src.write_text("# synthetic fixture, never executed\n")
            digest=hashlib.sha256(src.read_bytes()).hexdigest();c.update(raw_root=str(raw),controller_sha256=digest)
            diagnostic=c.get("cache_diagnostic")
            sources=diagnostic["source_sha256"]if diagnostic else c["baseline_host_source_sha256"];sources["lifecycle_r16_tp4.py"]=digest
            launch.update(controller_sha256=digest,diagnostic_sources=copy.deepcopy(diagnostic))
            launch["argv"]=[x.replace("/pkg:/probe:ro",str(base)+":/probe:ro")for x in launch["argv"]]
            mutate(a)
            for name,obj in {"result.json":result,"responses.json":records,"isolation.json":samples,"service-start.json":start,"release.json":release,"launch.json":launch,"lifecycle-semantic.json":semantic,"lifecycle-worker-controls.json":controls}.items():(raw/name).write_text(json.dumps(obj))
            (raw/"events.jsonl").write_text("".join(json.dumps(e)+"\n"for e in journal))
            cp=base/"contract.json";cp.write_text(json.dumps(c))
            if with_hot:write_hot_fixture(base,raw,sources,mutate_hot)
            with patch("audit_lifecycle_terminal.lifecycle_payloads",return_value=payloads):return audit(cp)
    def test_disabled_directory(self):self.assertTrue(self.run_fixture()["lifecycle_stage_audited"])
    def test_uninstalled_directory(self):self.assertEqual(self.run_fixture("uninstalled")["stage"],"uninstalled")
    def test_enabled_missing_hot_rejected(self):
        with self.assertRaises(ValueError):self.run_fixture("enabled")
    def test_response_tamper(self):
        with self.assertRaises(ValueError):self.run_fixture(mutate=lambda a:a[6][0]["payload"]["prompt"].append(99))
    def test_controls_tamper(self):
        with self.assertRaises(ValueError):self.run_fixture(mutate=lambda a:a[8]["workers"][0]["controls"].update(INDEPENDENT_COMPACT_HYPIC="1"))
    def test_enabled_directory_actual_audit_composition(self):
        r=self.run_fixture("enabled",with_hot=True)
        self.assertEqual(len(r["hot"]["covered"]),2);self.assertEqual(len(r["physical"]["ranks"]),4)
    def test_enabled_directory_missing_layer(self):
        def mutate(e):e.remove(next(x for x in e if x["event"]=="compact_gdn_body_composed"))
        with self.assertRaises(ValueError):self.run_fixture("enabled",with_hot=True,mutate_hot=mutate)
    def test_enabled_directory_nonfinite(self):
        def mutate(e):next(x for x in e if x["event"]=="compact_gdn_body_composed")["finite"]=False
        with self.assertRaises(ValueError):self.run_fixture("enabled",with_hot=True,mutate_hot=mutate)
    def test_enabled_directory_manifest_drift(self):
        def mutate(e):e[0]["manifest_sha256"]="wrong"
        with self.assertRaises(ValueError):self.run_fixture("enabled",with_hot=True,mutate_hot=mutate)
    def test_enabled_directory_namespace_drift(self):
        def mutate(e):
            for x in e:
                if x["rank"]==0:x["pid"]=999
        with self.assertRaises(ValueError):self.run_fixture("enabled",with_hot=True,mutate_hot=mutate)
if __name__=="__main__":unittest.main()

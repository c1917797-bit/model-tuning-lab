"""Synthetic381 treatment auditor composition; scorer and physical proof mocked."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_full_quality_terminal_composition as native_fixture
from audit_full_quality_terminal import audit
class Tests(unittest.TestCase):
    def fixture(self,root):
        cp,raw=native_fixture.Tests().fixture(root);c=json.loads(cp.read_text())
        inputs=json.loads(Path(c["quality_workload"]["inputs"]["path"]).read_text());rows=inputs["requests"]
        cfg=dict(public_catalog_artifact=dict(sha256=c["quality_workload"]["catalog"]["sha256"],segments=127),
            evidence_profile="quality-hot",scheduler_admission_enabled=True)
        (root/"config.json").write_text(json.dumps(cfg))
        sources=dict(c["baseline_host_source_sha256"]);sources["config.json"]=hashlib.sha256((root/"config.json").read_bytes()).hexdigest()
        manifest=dict(config="config.json",source_sha256=sources)
        (root/"manifest.json").write_text(json.dumps(manifest));mh=hashlib.sha256((root/"manifest.json").read_bytes()).hexdigest()
        c["cache_diagnostic"]=dict(compact_manifest="manifest.json",source_sha256=dict(sources,**{"manifest.json":mh}))
        cp.write_text(json.dumps(c));(raw/"diagnostics").mkdir()
        results=json.loads((raw/"quality-unit.json").read_text())["results"]
        for rank in range(4):
            shared=dict(rank=rank,pid=100+rank,manifest_sha256=mh)
            events=[dict(shared,event="compact_hypic_hooks_installed"),dict(shared,event="quality_evidence_policy_selected",
                profile="quality-hot",all_private_C1_C2_hot_receipts_retained=True,all_public_generation_eviction_receipts_retained=True)]
            for row in rows:
                index=row["index"]
                for pool,n,kind in (("linear",48,"compact_public_state_published"),("kv",16,"compact_public_kv_published")):
                    for l in range(n):
                        events.append(dict(shared,event=kind,pool=pool,key=f"{index}-{pool}{l}",layer=pool+str(l),
                            tokens_sha256=row["segment"]["tokens_sha256"],generation=index*100+l+1))
            for item in results:
                index=item["index"];step=item["repetition"]*1000+index+1;rid=item["request_id"]+"-runtime"
                events.append(dict(shared,event="native_request_progress",request_id=rid,step=step,scheduled_tokens=32,computed_tokens=0))
                events.append(dict(shared,event="compact_model_rows_completed",request_ids=[rid],step=step,original_rows=32,retained_rows=24))
                for pool,n,kind,field in (("linear",48,"compact_gdn_body_composed","skipped_body_tokens"),("kv",16,"compact_c2_queries_completed","skipped_body_queries")):
                    for l in range(n):
                        events.append(dict(shared,event=kind,request_id=rid,step=step,layer=pool+str(l),generation=index*100+l+1,
                            retained_rows=24,finite=True,**{field:8}))
            (raw/"diagnostics"/f"compact-worker-{rank}.jsonl").write_text("".join(json.dumps(e)+"\n"for e in events))
        return cp,raw
    def run_audit(self,cp):
        with patch("audit_full_quality_terminal.load_ruler",return_value={"score_case":native_fixture.Tests().score}),patch(
            "audit_full_quality_terminal.audit_physical_workers",return_value={"explicit_synthetic_mock":True}):
            return audit(cp)
    def test_complete381_fourworker_composition(self):
        with tempfile.TemporaryDirectory()as d:
            cp,raw=self.fixture(Path(d));r=self.run_audit(cp)
            self.assertEqual(r["cohort"]["requests"],381);self.assertEqual(r["hot"]["generation_links"],381*4*64)
            self.assertTrue(r["full_quality_arm_audited"]);self.assertEqual(r["quality_acceptance"],"NOT_DECIDED")
            self.assertFalse(r["live_release_verified"])
    def mutate(self,raw,fn):
        p=raw/"diagnostics"/"compact-worker-0.jsonl";events=[json.loads(x)for x in p.read_text().splitlines()]
        fn(events);p.write_text("".join(json.dumps(e)+"\n"for e in events))
    def test_missing_one_hot_layer_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            cp,raw=self.fixture(Path(d))
            self.mutate(raw,lambda e:e.remove(next(x for x in e if x["event"]=="compact_gdn_body_composed")))
            with self.assertRaises(ValueError):self.run_audit(cp)
    def test_wrong_material_generation_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            cp,raw=self.fixture(Path(d))
            self.mutate(raw,lambda e:next(x for x in e if x["event"]=="compact_gdn_body_composed").update(generation=999999))
            with self.assertRaises(ValueError):self.run_audit(cp)
if __name__=="__main__":unittest.main()

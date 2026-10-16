"""Synthetic full-directory auditor wiring; physical checker mocked, never NPU proof."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from audit_catalog_canary_terminal import audit
from test_audit_catalog_canary_cohort import Tests as _Cohort
# Avoid importing a TestCase into unittest discovery's module namespace.
_fixture=_Cohort.fixture
del _Cohort
class Tests(unittest.TestCase):
    def build(self,root):
        unit,journal,rows=_fixture(None)
        from independent_segment_selection import token_digest
        digests={i:token_digest([i]*16)for i in range(127)}
        for row in rows:
            i=row["index"];row["token_ids"]=[100000+i]*8+[i]*16+[200000+i]*8
            row["segment"]["tokens_sha256"]=digests[i]
        for item in unit["results"]:item["segment_sha256"]=digests[item["index"]]
        for event in journal:
            if "segment_sha256"in event:event["segment_sha256"]=digests[event["index"]]
        shared=lambda rank:dict(rank=rank,pid=100+rank,manifest_sha256=self.mh)
        worker=[]
        for rank in range(4):
            s=shared(rank)
            worker.append(dict(s,event="compact_hypic_hooks_installed"))
            worker.append(dict(s,event="quality_evidence_policy_selected",profile="quality-hot",
                all_private_C1_C2_hot_receipts_retained=True,all_public_generation_eviction_receipts_retained=True))
            def publish(index,pool,l,generation=None):
                return dict(s,event="compact_public_state_published" if pool=="linear" else "compact_public_kv_published",
                    pool=pool,key=f"{index}-{pool}{l}",layer=pool+str(l),tokens_sha256=digests[index],
                    generation=index*100+l+1 if generation is None else generation)
            for phase in range(3):
                indexes=list(range(8)) if phase==0 else list(range(8,16)) if phase==1 else [0]
                if phase==1:worker.append(dict(publish(0,"kv",0),event="compact_public_material_evicted"))
                for index in indexes:
                    if phase<2:
                        for pool,n in (("linear",48),("kv",16)):
                            worker.extend(publish(index,pool,l)for l in range(n))
                    else:worker.append(publish(0,"kv",0,10000))
                for index in indexes:
                    rid=f"private-{phase}-{index}-runtime";step=phase*8+index+1 if phase<2 else 100
                    worker.append(dict(s,event="native_request_progress",request_id=rid,step=step,scheduled_tokens=32,computed_tokens=0))
                    worker.append(dict(s,event="compact_model_rows_completed",request_ids=[rid],step=step,original_rows=32,retained_rows=24))
                    for pool,n,kind,field in (("linear",48,"compact_gdn_body_composed","skipped_body_tokens"),("kv",16,"compact_c2_queries_completed","skipped_body_queries")):
                        for l in range(n):
                            gen=10000 if phase==2 and pool=="kv" and l==0 else index*100+l+1
                            worker.append(dict(s,event=kind,request_id=rid,step=step,layer=pool+str(l),generation=gen,retained_rows=24,finite=True,**{field:8}))
        def write(path,obj):
            path.write_text(json.dumps(obj));return hashlib.sha256(path.read_bytes()).hexdigest()
        inputs=dict(schema="hypic-quality-inputs/v1",requests=rows,generation=dict(max_tokens=1024,temperature=0,seed=0,ignore_eos=False,enable_thinking=False),repetitions=3)
        ih=write(root/"inputs.json",inputs);ch=write(root/"catalog.json",dict(schema="hypic-public-catalog/v1",public_segments=[[i]*16 for i in range(127)]))
        cfg=dict(scheduler_admission_enabled=True,evidence_profile="quality-hot",prompt_snapshot_probe_batches=0,
            c1_layer_shadow_validation=True,c1_first_divergence=True,public_catalog_artifact=dict(sha256=ch,segments=127))
        cfgh=write(root/"config.json",cfg)
        (root/"formal_quality_r16_tp4.py").write_text("# synthetic bound controller, not executed\n")
        ctrl=hashlib.sha256((root/"formal_quality_r16_tp4.py").read_bytes()).hexdigest()
        # Manifest bytes must exist before generating worker source identities.
        manifest=dict(config="config.json",source_sha256={"config.json":cfgh,"formal_quality_r16_tp4.py":ctrl})
        mh=write(root/"manifest.json",manifest)
        worker=[dict(e,manifest_sha256=mh)for e in worker]
        raw=root/"raw";raw.mkdir();(raw/"diagnostics").mkdir()
        for rank in range(4):
            (raw/"diagnostics"/f"compact-worker-{rank}.jsonl").write_text("".join(json.dumps(e)+"\n"for e in worker if e["rank"]==rank))
        c=dict(formal_quality_canary=True,physical_npus=[0,1,2,3],tp=4,image="image",raw_root=str(raw),controller_sha256=ctrl,
            cache_diagnostic=dict(compact_manifest="manifest.json",source_sha256=dict(manifest["source_sha256"],**{"manifest.json":mh})),
            quality_workload=dict(inputs=dict(path=str(root/"inputs.json"),sha256=ih),catalog=dict(path=str(root/"catalog.json"),sha256=ch),batch_samples=8,canary_indexes=list(range(16))))
        cp=root/"contract.json";write(cp,c)
        start=dict(container_id="a"*64,image="image",devices=["/dev/davinci"+str(i)for i in range(4)])
        release=dict(owned_container="a"*64,removed=True,port_free=True,final_physical_processes=[])
        samples=[dict(foreign=[])]
        result=dict(valid=True,error=None,guard_errors=[],responses=17,isolation_samples=1,release=release)
        journal.extend([dict(event="isolation",snapshot=samples[0]),dict(event="terminal",result=result)])
        for name,obj in (("catalog-canary-unit.json",unit),("responses.json",unit["results"]),("result.json",result),("isolation.json",samples),("service-start.json",start),("release.json",release)):write(raw/name,obj)
        (raw/"events.jsonl").write_text("".join(json.dumps(e)+"\n"for e in journal))
        return cp,raw
    mh="placeholder"
    def test_full_composition_synthetic_only(self):
        with tempfile.TemporaryDirectory()as d:
            cp,raw=self.build(Path(d))
            with patch("audit_catalog_canary_terminal.audit_physical_workers",return_value={"synthetic_mock":True})as physical:
                r=audit(cp)
            self.assertTrue(r["bounded_catalog_canary_valid"]);self.assertFalse(r["live_release_verified"])
            self.assertEqual(r["hot"]["denominator"],17);self.assertEqual(len(r["rebuild"]["transitions"]),4)
            physical.assert_called_once()
    def test_full_composition_rejects_lost_worker(self):
        with tempfile.TemporaryDirectory()as d:
            cp,raw=self.build(Path(d));(raw/"diagnostics"/"compact-worker-3.jsonl").unlink()
            with self.assertRaises(ValueError):audit(cp)
    def test_independent_membership_rejects_rehashed_input(self):
        with tempfile.TemporaryDirectory()as d:
            cp,raw=self.build(Path(d));c=json.loads(cp.read_text())
            p=Path(c["quality_workload"]["inputs"]["path"]);payload=json.loads(p.read_text())
            payload["requests"][0]["token_ids"][8]+=9999;p.write_text(json.dumps(payload))
            c["quality_workload"]["inputs"]["sha256"]=hashlib.sha256(p.read_bytes()).hexdigest();cp.write_text(json.dumps(c))
            with self.assertRaisesRegex(ValueError,"membership"):audit(cp)
    def test_contract_selection_drift(self):
        with tempfile.TemporaryDirectory()as d:
            cp,raw=self.build(Path(d));c=json.loads(cp.read_text())
            c["quality_workload"]["canary_indexes"]=list(reversed(range(16)));cp.write_text(json.dumps(c))
            with self.assertRaisesRegex(ValueError,"cohort"):audit(cp)
if __name__=="__main__":unittest.main()

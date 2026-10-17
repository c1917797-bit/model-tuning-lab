"""Independent complete bounded catalog Canary audit; never full quality."""
import hashlib,json,subprocess
from pathlib import Path
from audit_catalog_canary_cohort import audit_canary_cohort
from audit_catalog_quality_hot import audit_catalog_hot
from audit_catalog_rebuild_chain import audit_rebuild_chain
from audit_physical_worker_namespaces import audit_physical_workers
from independent_quality_workload import read_bound

def audit_terminal_records(c,result,records,journal,samples,start,release):
    if result.get("valid")is not True or result.get("error")is not None or result.get("guard_errors") or result.get("responses")!=17:
        raise ValueError("complete successful17 terminal required")
    if [e for e in journal if e.get("event")=="terminal"]!=[dict(event="terminal",result=result)]:
        raise ValueError("terminal journal mismatch")
    captured=[e["snapshot"]for e in journal if e.get("event")=="isolation"]
    if not samples or samples!=captured or len(samples)!=result.get("isolation_samples") or any(s["foreign"]for s in samples):
        raise ValueError("continuous clean isolation mismatch")
    if release!=result.get("release") or release.get("owned_container")!=start.get("container_id") or release.get("removed")is not True or release.get("port_free")is not True or release.get("final_physical_processes"):
        raise ValueError("exact own release mismatch")
    if not isinstance(start.get("container_id"),str) or len(start["container_id"])!=64 or start.get("image")!=c["image"] or set(start.get("devices",[]))!={"/dev/davinci"+str(i)for i in range(4)}:
        raise ValueError("exact image/container/physical0-3 scope required")
    if len(records)!=17:raise ValueError("complete responses artifact required")

def audit(contract_path,*,live_release=False):
    cp=Path(contract_path).resolve();base=cp.parent;c=json.loads(cp.read_text());raw=Path(c["raw_root"])
    if c.get("formal_quality_canary")is not True or c.get("formal_quality",False)is not False or c.get("formal_performance",False)is not False or c["physical_npus"]!=[0,1,2,3] or c["tp"]!=4:
        raise ValueError("exclusive physical0-3 TP4 bounded catalog Canary required")
    sources=c["cache_diagnostic"]["source_sha256"]
    for name,digest in sources.items():
        original=base/name;p=original.resolve()
        if original.is_symlink() or not p.is_relative_to(base) or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
            raise ValueError("bound source drift: "+name)
    if sources.get("formal_quality_r16_tp4.py")!=c["controller_sha256"]:raise ValueError("quality controller identity mismatch")
    mp=base/c["cache_diagnostic"]["compact_manifest"];mh=hashlib.sha256(mp.read_bytes()).hexdigest();manifest=json.loads(mp.read_text())
    for n,h in manifest["source_sha256"].items():
        if sources.get(n)!=h:raise ValueError("manifest/contract source map mismatch")
    cfg=json.loads((base/manifest["config"]).read_text())
    if cfg.get("scheduler_admission_enabled")is not True or cfg.get("evidence_profile")!="quality-hot" or cfg.get("prompt_snapshot_probe_batches",0)!=0:
        raise ValueError("explicit catalog admission/complete hot evidence/no timing probe required")
    if cfg.get("c1_performance_mode",False)is not False or cfg.get("c1_layer_shadow_validation")is not True or cfg.get("c1_first_divergence")is not True:
        raise ValueError("bounded diagnostic correctness shadows required")
    spec=c["quality_workload"];inputs=read_bound(spec["inputs"]);catalog=read_bound(spec["catalog"])
    from independent_segment_catalog import SegmentCatalog
    from independent_catalog_quality_canary import catalog_canary_plan
    if inputs.get("schema")!="hypic-quality-inputs/v1" or catalog.get("schema")!="hypic-public-catalog/v1":
        raise ValueError("frozen input/catalog schema mismatch")
    rows=inputs["requests"];plan=catalog_canary_plan(rows,selection=spec.get("canary_selection","capacity"))
    if spec.get("batch_samples")!=8 or spec.get("canary_indexes")!=list(plan["initial_indexes"]):
        raise ValueError("contract diagnostic cohort mismatch")
    stage=SegmentCatalog(catalog["public_segments"])
    for row in rows:
        segment=row["segment"]
        if tuple(row["token_ids"][segment["start"]:segment["end"]])!=stage.tokens(segment["tokens_sha256"]):
            raise ValueError("independent selected segment membership mismatch")
    if inputs.get("generation")!={"max_tokens":1024,"temperature":0,"seed":0,"ignore_eos":False,"enable_thinking":False} or inputs.get("repetitions")!=3:
        raise ValueError("frozen naturalEOS ruler mismatch")
    a=cfg.get("public_catalog_artifact",{})
    if a.get("sha256")!=spec["catalog"]["sha256"] or a.get("segments")!=len(stage.entries):raise ValueError("runtime/diagnostic catalog mismatch")
    result=json.loads((raw/"result.json").read_text());records=json.loads((raw/"responses.json").read_text())
    journal=[json.loads(x)for x in (raw/"events.jsonl").read_text().splitlines()]
    samples=json.loads((raw/"isolation.json").read_text());start=json.loads((raw/"service-start.json").read_text());release=json.loads((raw/"release.json").read_text())
    audit_terminal_records(c,result,records,journal,samples,start,release)
    unit=json.loads((raw/"catalog-canary-unit.json").read_text())
    if unit["results"]!=records:raise ValueError("unit/response artifact mismatch")
    cohort=audit_canary_cohort(unit,journal,inputs["requests"],selection=spec.get("canary_selection","capacity"))
    worker=[];paths=sorted((raw/"diagnostics").glob("compact-worker-*.jsonl"))
    if len(paths)!=4:raise ValueError("exact four worker evidence files required")
    for p in paths:
        if p.is_symlink() or p.stat().st_size>128*1024**2:raise ValueError("regular bounded worker evidence required")
        worker.extend(json.loads(x)for x in p.read_text().splitlines())
    hot=audit_catalog_hot(worker,records,inputs["requests"],manifest_sha256=mh,expected_count=17)
    chain=audit_rebuild_chain(worker,manifest_sha256=mh,initial_api=cohort["initial_api"],rebuild_api=cohort["rebuild_api"],tokens_sha256=cohort["segment_sha256"])
    installs=[e for e in worker if e.get("event")=="compact_hypic_hooks_installed"]
    policies=[e for e in worker if e.get("event")=="quality_evidence_policy_selected"]
    if len(installs)!=4 or {e["pid"]for e in installs}!=set(hot["worker_pids"].values()) or any(e.get("manifest_sha256")!=mh for e in installs):
        raise ValueError("four-worker source-bound activation missing")
    if len(policies)!=4 or {e["pid"]for e in policies}!=set(hot["worker_pids"].values()) or any(e.get("manifest_sha256")!=mh or e.get("profile")!="quality-hot" or e.get("all_private_C1_C2_hot_receipts_retained")is not True or e.get("all_public_generation_eviction_receipts_retained")is not True for e in policies):
        raise ValueError("complete four-worker quality evidence policy missing")
    physical=audit_physical_workers(samples,hot["worker_pids"],owned_cid=start["container_id"])
    if live_release:
        from formal_r15_tp4 import snapshot,port_free
        q=subprocess.run(["docker","inspect",start["container_id"]],capture_output=True,text=True)
        if q.returncode==0 or q.stdout.strip()!="[]" or not ("No such object"in q.stderr or "No such container"in q.stderr):raise ValueError("exact container absence unproved")
        if snapshot()["processes"]:raise ValueError("physical0-3 not empty")
        port_free(c["port"])
    return {"bounded_catalog_canary_valid":True,"cohort":cohort,"hot":hot,"rebuild":chain,"physical":physical,
            "source_bindings":len(sources),"isolation_samples":len(samples),"live_release_verified":live_release,
            "scope":"17 diagnostic requests and real catalog eviction/rebuild; NOT full127x3 quality, matched speed, or lifecycle acceptance"}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

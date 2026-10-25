"""HOST-only R28 successor for the genuine R23 full-quality controller.

Preserves the reviewed generic full381 terminal/cohort/catalog/physical audit.
Only controller identity/report binding changes; no device execution is added.
Natural EOS permits stop and length, with every response independently scored.
"""
import hashlib,json,subprocess,sys
from pathlib import Path

# Direct CLI execution lives one directory below the unchanged workstream.
WORKSTREAM = Path(__file__).resolve().parent.parent
if str(WORKSTREAM) not in sys.path:
    sys.path.insert(0, str(WORKSTREAM))

from audit_full_quality_cohort import audit_full_quality_cohort
from audit_catalog_quality_hot import audit_catalog_hot
from audit_physical_worker_namespaces import audit_physical_workers
from independent_quality_workload import read_bound
from independent_quality_ruler import load_ruler
from independent_segment_catalog import SegmentCatalog

from audit_full_quality_terminal import audit_quality_terminal_records

CONTROLLER_NAME = "formal_quality_r23_tp4.py"
CONTROLLER_SHA256 = "cd9718501d8fc22e3df5d4e77de1833fee30e30f35525df7e21ad06b288a2cdd"
BASE_CONTROLLER_NAME = "formal_quality_r16_tp4.py"
BASE_CONTROLLER_SHA256 = "1bd415fbc61f6534503c4f403945aac245ceb88a9f78f5e26dc8b7992e0943f8"


def audit_controller_identity(base, contract, sources, launch):
    """Bind the genuine retained R23 controller; never alias its hash to R16.

    R23 is a complete controller, not an import of R16. If the historical R16
    source remains in the frozen closure, it retains its own real identity.
    This HOST-only successor is bound separately from the runtime allowlist.
    """
    if (contract.get("controller_sha256") != CONTROLLER_SHA256
            or sources.get(CONTROLLER_NAME) != CONTROLLER_SHA256):
        raise ValueError("actual R23 quality controller binding required")
    original = Path(base) / CONTROLLER_NAME
    if (original.is_symlink()
            or hashlib.sha256(original.read_bytes()).hexdigest() != CONTROLLER_SHA256):
        raise ValueError("actual R23 quality controller source drift")
    if (BASE_CONTROLLER_NAME in sources
            and sources[BASE_CONTROLLER_NAME] != BASE_CONTROLLER_SHA256):
        raise ValueError("retained R16 base source identity mismatch")
    if launch.get("controller_sha256") != CONTROLLER_SHA256:
        raise ValueError("R23 launch controller report mismatch")
    return {"filename": CONTROLLER_NAME, "sha256": CONTROLLER_SHA256,
            "launch_report_matched": True,
            "retained_r16_base_bound": BASE_CONTROLLER_NAME in sources}


def audit(contract_path,*,live_release=False):
    cp=Path(contract_path).resolve();base=cp.parent;c=json.loads(cp.read_text());raw=Path(c["raw_root"])
    if c.get("formal_quality")is not True or c.get("formal_quality_canary",False)is not False or c.get("formal_performance",False)is not False or c.get("physical_npus")!=[0,1,2,3] or c.get("tp")!=4:
        raise ValueError("exclusive full quality physical0-3 TP4 contract required")
    if c.get("enable_thinking")is not False or c.get("max_output_tokens")!=1024 or c.get("enable_prefix_caching")is not False:
        raise ValueError("frozen nonthinking1024 noPDC quality ruler required")
    diagnostic=c.get("cache_diagnostic")
    sources=diagnostic["source_sha256"]if diagnostic else c["baseline_host_source_sha256"]
    for name,digest in sources.items():
        original=base/name;p=original.resolve()
        if original.is_symlink() or not p.is_relative_to(base) or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError("source drift: "+name)
    launch=json.loads((raw/"launch.json").read_text())
    controller=audit_controller_identity(base,c,sources,launch)
    spec=c["quality_workload"]
    if set(spec)!={"inputs","catalog","ruler_path","batch_samples"} or spec["batch_samples"]!=8:
        raise ValueError("full frozen quality specification required")
    inputs=read_bound(spec["inputs"]);catalog=read_bound(spec["catalog"])
    if inputs.get("schema")!="hypic-quality-inputs/v1" or catalog.get("schema")!="hypic-public-catalog/v1" or inputs.get("repetitions")!=3 or inputs.get("generation")!={"max_tokens":1024,"temperature":0,"seed":0,"ignore_eos":False,"enable_thinking":False}:
        raise ValueError("input/catalog/generation schema mismatch")
    rows=inputs["requests"];stage=SegmentCatalog(catalog["public_segments"])
    for row in rows:
        s=row["segment"]
        if tuple(row["token_ids"][s["start"]:s["end"]])!=stage.tokens(s["tokens_sha256"]) or len(row["token_ids"])+1024>40960:
            raise ValueError("selected segment membership/model capacity mismatch")
    ruler=load_ruler(spec["ruler_path"])
    result=json.loads((raw/"result.json").read_text());records=json.loads((raw/"responses.json").read_text())
    journal=[json.loads(x)for x in (raw/"events.jsonl").read_text().splitlines()]
    samples=json.loads((raw/"isolation.json").read_text());start=json.loads((raw/"service-start.json").read_text());release=json.loads((raw/"release.json").read_text())
    audit_quality_terminal_records(c,result,records,journal,samples,start,release)
    unit=json.loads((raw/"quality-unit.json").read_text())
    if records!=unit["results"]:raise ValueError("unit/response artifact drift")
    cohort=audit_full_quality_cohort(rows,unit,journal,score=ruler["score_case"],batch_samples=8)
    paths=sorted((raw/"diagnostics").glob("compact-worker-*.jsonl"));hot=None
    if diagnostic:
        mp=base/diagnostic["compact_manifest"];mh=hashlib.sha256(mp.read_bytes()).hexdigest();manifest=json.loads(mp.read_text())
        if any(sources.get(n)!=h for n,h in manifest["source_sha256"].items()):raise ValueError("manifest/contract binding drift")
        cfg=json.loads((base/manifest["config"]).read_text())
        artifact=cfg.get("public_catalog_artifact",{})
        if artifact.get("sha256")!=spec["catalog"]["sha256"] or artifact.get("segments")!=len(stage.entries) or cfg.get("evidence_profile")!="quality-hot" or cfg.get("scheduler_admission_enabled")is not True:
            raise ValueError("exact runtime catalog/admission/hot policy required")
        if len(paths)!=4:raise ValueError("fourworker evidence files required")
        worker=[]
        for p in paths:
            if p.is_symlink() or p.stat().st_size>128*1024**2:raise ValueError("bounded regular evidence required")
            worker.extend(json.loads(x)for x in p.read_text().splitlines())
        hot=audit_catalog_hot(worker,records,rows,manifest_sha256=mh,expected_count=381)
        installs=[e for e in worker if e.get("event")=="compact_hypic_hooks_installed"]
        policies=[e for e in worker if e.get("event")=="quality_evidence_policy_selected"]
        for events in (installs,policies):
            if len(events)!=4 or {e["pid"]for e in events}!=set(hot["worker_pids"].values()) or any(e.get("manifest_sha256")!=mh for e in events):
                raise ValueError("fourworker source/activation/policy mismatch")
        if any(e.get("profile")!="quality-hot" or e.get("all_private_C1_C2_hot_receipts_retained")is not True or e.get("all_public_generation_eviction_receipts_retained")is not True for e in policies):
            raise ValueError("unfiltered hot/generation evidence required")
        physical=audit_physical_workers(samples,hot["worker_pids"],owned_cid=start["container_id"])
    else:
        if paths or launch.get("diagnostic_sources") or any("INDEPENDENT_COMPACT_HYPIC=1"in x or "PYTHONPATH=/probe/"in x for x in launch["argv"]):
            raise ValueError("baseline treatment must be absent")
        seen=set()
        for s in samples:
            for owner in s.get("owners",[]):
                if owner.get("owned")is True and owner.get("ownership_status")=="owned-cgroup" and start["container_id"]in owner.get("cgroup",""):
                    seen.add(owner["npu"])
        if seen!=set(range(4)):raise ValueError("native baseline physical0-3 ownership incomplete")
        physical={"native_owned_physical_cards":sorted(seen),"rank_assignment_claimed":False}
    if live_release:
        from formal_r15_tp4 import snapshot,port_free
        q=subprocess.run(["docker","inspect",start["container_id"]],capture_output=True,text=True)
        if q.returncode==0 or q.stdout.strip()!="[]" or not ("No such object"in q.stderr or "No such container"in q.stderr):raise ValueError("exact container absence unproved")
        if snapshot()["processes"]:raise ValueError("physical0-3 not empty")
        port_free(c["port"])
    return {"host_auditor":"r28-quality-terminal","controller_identity":controller,"full_quality_arm_audited":True,"arm":"hypic"if diagnostic else "baseline","cohort":cohort,
        "hot":hot,"physical":physical,"source_bindings":len(sources),"isolation_samples":len(samples),"live_release_verified":live_release,
        "quality_acceptance":"NOT_DECIDED","scope":"complete singlearm127x3 source/cohort/rescoring/hot(if treatment)/isolation/release; paired task-quality and deployment decision separate"}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))


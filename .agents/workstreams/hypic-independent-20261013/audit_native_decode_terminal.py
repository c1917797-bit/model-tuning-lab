"""Reproducible terminal16 audit; offline receipts and fresh release are separate."""
import hashlib,json,statistics,subprocess
from pathlib import Path
from audit_full40_hot_coverage import audit_profile16_hot
from audit_native_decode_batch import audit_native_decode_batch,audit_native_decode_disabled
from audit_physical_worker_namespaces import audit_physical_workers

def require(value,message):
    if not value:raise ValueError(message)

def audit_terminal(contract_path,*,live_release=False):
    contract_path=Path(contract_path);base=contract_path.parent
    c=json.loads(contract_path.read_text());raw=Path(c["raw_root"])
    require(c["physical_npus"]==[0,1,2,3] and c["tp"]==4,"physical/model scope")
    res=json.loads((raw/"result.json").read_text())
    unit=json.loads((raw/"compiled-cache-unit.json").read_text())
    require(res.get("valid") is True and res.get("error") is None and not res.get("guard_errors"),"successful terminal required")
    results=unit.get("results",[])
    require(res.get("responses")==16 and unit.get("valid") is True and len(results)==16,"complete diagnostic16 required")
    require(len({x["index"] for x in results})==16,"unique diagnostic indices")
    for x in results:
        require(x.get("ok") is True and x["response"]["usage"]["prompt_tokens"]==32768 and x["response"]["usage"]["completion_tokens"]==64,"exact response token counts")
    require(unit["input_sha256"]==c["formal_token_artifact"]["sha256"],"input identity drift")
    journal=[json.loads(x) for x in (raw/"events.jsonl").read_text().splitlines()]
    require([x for x in journal if x["event"]=="terminal"]==[{"event":"terminal","result":res}],"exact terminal journal")
    records=[{k:v for k,v in x.items() if k not in ("event","scored")} for x in journal if x["event"]=="profile-response"]
    require(records==results and all(x.get("scored") is False for x in journal if x["event"]=="profile-response"),"diagnostic journal/client mismatch")
    samples=[x["snapshot"] for x in journal if x["event"]=="isolation"]
    require(samples and len(samples)==res["isolation_samples"] and samples==json.loads((raw/"isolation.json").read_text()),"isolation denominator")
    require(not any(x["foreign"] for x in samples),"foreign physical process")
    sources=c["cache_diagnostic"]["source_sha256"]
    require(bool(sources),"complete source map required")
    for name,digest in sources.items():
        require((base/name).resolve().is_relative_to(base.resolve()),"source outside workstream")
        require(hashlib.sha256((base/name).read_bytes()).hexdigest()==digest,"source drift: "+name)
    require(hashlib.sha256((base/"cache_reuse_tp4_diagnostic.py").read_bytes()).hexdigest()==c["controller_sha256"],"controller drift")
    manifest_path=base/c["cache_diagnostic"]["compact_manifest"]
    manifest=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    m=json.loads(manifest_path.read_text());cfg=json.loads((base/m["config"]).read_text())
    enabled=cfg["native_decode_batch"];require(type(enabled) is bool,"explicit native batch flag")
    events=[]
    for path in (raw/"diagnostics").glob("compact-worker-*.jsonl"):
        events.extend(json.loads(x) for x in path.read_text().splitlines())
    hot=audit_profile16_hot(events,[x["response"]["id"] for x in results],manifest_sha256=manifest)
    require(hot["accepted_hot_coverage"],"complete16 fourrank48/16hot required")
    batch=(audit_native_decode_batch if enabled else audit_native_decode_disabled)(
        events,hot["worker_pids"],manifest_sha256=manifest)
    start=json.loads((raw/"service-start.json").read_text())
    release=json.loads((raw/"release.json").read_text())
    require(release==res["release"] and release["owned_container"]==start["container_id"],"exact owned release identity")
    require(release["removed"] is True and release["port_free"] is True and not release["final_physical_processes"],"release receipt incomplete")
    require(start["image"]==c["image"] and set(start["devices"])=={"/dev/davinci"+str(i) for i in range(4)},"image/physical declaration drift")
    physical=audit_physical_workers(samples,hot["worker_pids"],owned_cid=start["container_id"])
    fresh=None
    if live_release:
        from cache_reuse_tp4_diagnostic import snapshot,port_free
        q=subprocess.run(["docker","inspect",start["container_id"]],capture_output=True,text=True)
        require(q.returncode!=0 and json.loads(q.stdout)==[] and ("No such object" in q.stderr or "No such container" in q.stderr),"exact container still present or inspect unavailable")
        fresh=snapshot();require(not fresh["processes"],"physical0-3 not empty")
        port_free(c["port"])
    shadows=[x for x in events if x.get("event")=="native_decode_batch_shadow_checked"]
    return {"terminal_evidence_valid":True,"live_release_verified":live_release,
            "enabled":enabled,"source_bindings":len(sources),"manifest_sha256":manifest,
            "hot":hot,"native_batch":batch,"physical":physical,
            "isolation_samples":len(samples),"shadow_groups":len(shadows),
            "max_scaled":max((v["max_scaled"] for x in shadows for v in x["metrics"]),default=None),
            "elapsed_median_seconds":statistics.median(x["response"]["diagnostic_elapsed_seconds"] for x in results),
            "raw_sha256":{name:hashlib.sha256((raw/name).read_bytes()).hexdigest() for name in ("result.json","events.jsonl","compiled-cache-unit.json","release.json")},
            "scope":"bounded16 source/hot/native switch/numerical-control/isolation/release receipts; fresh physical release ONLY when live_release_verified; not formal performance/quality/goal completion"}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit_terminal(a.contract,live_release=a.live_release)))

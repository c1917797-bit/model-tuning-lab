"""Single-stage lifecycle terminal audit; no three-state or quality promotion."""
import hashlib,json,re,subprocess
from pathlib import Path
from independent_lifecycle_policy import lifecycle_mode,validate_lifecycle_sources,lifecycle_payloads
from audit_lifecycle_requests import audit_lifecycle_requests
from audit_delivery_lifecycle_startup_controls import audit_startup_controls
from audit_full40_hot_coverage import _audit_hot
from audit_physical_worker_namespaces import audit_physical_workers

def audit_terminal_records(c,result,journal,samples,start,release):
    if c.get("delivery_adapter")is not True:raise ValueError("explicit delivery adapter lifecycle required")
    stage,on=lifecycle_mode(c);cid=start.get("container_id")
    if not isinstance(cid,str) or not re.fullmatch("[0-9a-f]{64}",cid):
        raise ValueError("exact owned lifecycle CID required")
    if result.get("valid")is not True or result.get("error")is not None or result.get("guard_errors") or result.get("responses")!=3:
        raise ValueError("successful complete lifecycle terminal required")
    if [e for e in journal if e.get("event")=="terminal"]!=[dict(event="terminal",result=result)]:
        raise ValueError("lifecycle terminal journal drift")
    if not samples or samples!=[e["snapshot"]for e in journal if e.get("event")=="isolation"] or len(samples)!=result.get("isolation_samples") or any(e.get("foreign")for e in samples):
        raise ValueError("continuous clean lifecycle isolation required")
    if release!=result.get("release") or release.get("owned_container")!=cid or release.get("removed")is not True or release.get("port_free")is not True or release.get("final_physical_processes")!=[] or release.get("error"):
        raise ValueError("exact own lifecycle release required")
    if c.get("physical_npus")!=[0,1,2,3] or c.get("tp")!=4 or start.get("image")!=c.get("image") or set(start.get("devices",[]))!={"/dev/davinci"+str(i)for i in range(4)}:
        raise ValueError("same image physical0-3 TP4 required")
    return stage,on

def audit(contract_path,*,live_release=False):
    cp=Path(contract_path).resolve();base=cp.parent;c=json.loads(cp.read_text());raw=Path(c["raw_root"])
    source_count=validate_lifecycle_sources(c,base);diagnostic=c.get("cache_diagnostic")
    sources=diagnostic["source_sha256"]if diagnostic else c["baseline_host_source_sha256"]
    if sources.get("lifecycle_delivery_r16_tp4.py")!=c.get("controller_sha256"):
        raise ValueError("lifecycle controller source binding mismatch")
    def read(name):
        p=raw/name
        if p.is_symlink() or p.stat().st_size>128*1024**2:raise ValueError("bounded regular lifecycle artifact required")
        return json.loads(p.read_text())
    result=read("result.json");records=read("responses.json");samples=read("isolation.json")
    start=read("service-start.json");release=read("release.json");launch=read("launch.json")
    ep=raw/"events.jsonl"
    if ep.is_symlink() or ep.stat().st_size>128*1024**2:raise ValueError("bounded regular journal required")
    journal=[json.loads(x)for x in ep.read_text().splitlines()]
    stage,on=audit_terminal_records(c,result,journal,samples,start,release)
    if launch.get("controller_sha256")!=c["controller_sha256"] or launch.get("diagnostic_sources")!=diagnostic:
        raise ValueError("actual launch source identity mismatch")
    transport=audit_lifecycle_requests(records,journal,read("lifecycle-semantic.json"),stage,lifecycle_payloads(c["formal_token_artifact"]))
    controls=read("lifecycle-worker-controls.json")
    if [e for e in journal if e.get("event")=="lifecycle-worker-startup-controls"]!=[controls]:
        raise ValueError("worker controls durable journal drift")
    startup=audit_startup_controls(controls,c,samples,start,launch,package_root=str(base))
    worker=[];paths=sorted((raw/"diagnostics").glob("compact-worker-*.jsonl"))
    for p in paths:
        if p.is_symlink() or p.stat().st_size>128*1024**2:raise ValueError("bounded regular worker evidence required")
        worker.extend(json.loads(x)for x in p.read_text().splitlines())
    hot=None;physical=None
    if on:
        if len(paths)!=4:raise ValueError("four worker source-bound package required")
        original=base/diagnostic["compact_manifest"];manifest_path=original.resolve()
        if original.is_symlink() or not manifest_path.is_relative_to(base):raise ValueError("regular local lifecycle manifest required")
        manifest=json.loads(manifest_path.read_text());mh=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        if any(sources.get(n)!=h for n,h in manifest["source_sha256"].items()):
            raise ValueError("four worker source-bound package required")
        hot=_audit_hot(worker,transport["completion_ids"][1:],manifest_sha256=mh,expected_count=2)
        if not hot["accepted_hot_coverage"]:raise ValueError("enabled lifecycle both requests require four-rank48/16 hot proof")
        installs=[e for e in worker if e.get("event")=="compact_hypic_hooks_installed"]
        if len(installs)!=4 or {e.get("pid")for e in installs}!=set(hot["worker_pids"].values()) or any(e.get("manifest_sha256")!=mh for e in installs):
            raise ValueError("source-bound four-worker installation required")
        physical=audit_physical_workers(samples,hot["worker_pids"],owned_cid=start["container_id"])
    elif paths or worker:
        raise ValueError("disabled/uninstalled stage emitted active treatment evidence")
    if live_release:
        from formal_r15_tp4 import snapshot,port_free
        q=subprocess.run(["docker","inspect",start["container_id"]],capture_output=True,text=True)
        if q.returncode==0 or q.stdout.strip()!="[]" or not ("No such object"in q.stderr or "No such container"in q.stderr):
            raise ValueError("exact own lifecycle container absence unproved")
        if snapshot()["processes"]:raise ValueError("physical0-3 not empty at release audit")
        port_free(c["port"])
    return {"lifecycle_stage_audited":True,"stage":stage,"transport":transport,"startup":startup,
        "hot":hot,"physical":physical,"source_bindings":source_count,"isolation_samples":len(samples),
        "live_release_verified":live_release,"scope":"one bounded lifecycle stage only; three-stage rollback and prior performance/quality gates separate"}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

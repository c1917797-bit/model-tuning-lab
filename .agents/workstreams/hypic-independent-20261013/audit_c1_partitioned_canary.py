"""Independent R18 two-request numerical/partition/source/physical/release audit."""
import hashlib,json,math
from pathlib import Path
from audit_prompt_snapshot_canary import audit as audit_snapshot

def audit_partition_rows(events,workers,manifest):
    if set(workers)!=set(range(4)):raise ValueError("four exact workers required")
    selected=[e for e in events if e.get("event")=="c1_packed_wave_prepared"]
    done=[e for e in events if e.get("event")=="compact_gdn_body_composed"]
    shadows=[e for e in events if e.get("event")=="c1_packed_wave_shadow_checked"]
    groups={};numeric={r:set() for r in workers};hot={r:set() for r in workers}
    def identity(e):
        r=e.get("rank")
        if type(r)is not int or r not in workers or e.get("pid")!=workers[r] or e.get("manifest_sha256")!=manifest:
            raise ValueError("partition worker/source identity mismatch")
        if type(e.get("step"))is not int or e["step"]<=0 or not isinstance(e.get("layer"),str):
            raise ValueError("partition actual layer/step required")
        return r,e["step"],e["layer"]
    for e in selected:
        key=identity(e)
        if key in groups:raise ValueError("duplicate partition group")
        if e.get("state_schedule")!="partitioned" or type(e.get("state_passes"))is not int or e["state_passes"] not in (1,2) or e.get("actual_slot_commit")!="not_started":
            raise ValueError("partition schedule/commit proof missing")
        for count in ("windows","packed_tokens","state_window_visits","state_token_visits"):
            if type(e.get(count))is not int or e[count]<1:raise ValueError("positive exact partition counts required")
        if e["state_window_visits"]!=e["windows"] or e["state_token_visits"]!=e["packed_tokens"]:
            raise ValueError("partition did not visit each live row once")
        requests=e.get("requests")
        if not requests or len(requests)!=len(set(requests)):raise ValueError("unique group requests required")
        groups[key]=set(requests)
    for e in done:
        key=identity(e);rid=e.get("request_id")
        if rid not in groups.get(key,set()):raise ValueError("completed request missing exact partition step")
        if e.get("finite")is not True:raise ValueError("actual completed finite proof required")
        hot[key[0]].add(key[2])
    for e in shadows:
        key=identity(e)
        if e.get("request_id") not in groups.get(key,set()):raise ValueError("shadow missing partition request")
        metrics=e.get("metrics",[])
        if (e.get("passed")is not True or e.get("private_buffers")is not True
                or e.get("actual_slot_commit")!="not_started" or e.get("atol")!=.01 or e.get("rtol")!=.003
                or len(metrics)!=3 or {m.get("tensor") for m in metrics}!={"output","state","conv"}):
            raise ValueError("unchanged full-private numerical shadow required")
        for m in metrics:
            if m.get("passed")is not True or any(type(m.get(k)) not in (float,int) or not math.isfinite(m[k]) or m[k]<0 for k in ("max_abs","rms","max_scaled")) or m["max_scaled"]>1:
                raise ValueError("failed/nonfinite numerical residual")
        numeric[key[0]].add(key[2])
    if not groups or any(len(hot[r])!=48 or numeric[r]!=hot[r] for r in workers):
        raise ValueError("48-layer numerical and actual partition coverage per rank required")
    return dict(groups=len(groups),completed_receipts=len(done),numeric_shadows=len(shadows),
        four_rank_layers={r:len(hot[r]) for r in workers},sampled_numeric_not_full_quality=True)

def audit(contract_path,*,live_release=False):
    cp=Path(contract_path).resolve();base=cp.parent;c=json.loads(cp.read_text())
    report=audit_snapshot(cp,live_release=live_release)
    mp=base/c["cache_diagnostic"]["compact_manifest"];mh=hashlib.sha256(mp.read_bytes()).hexdigest()
    m=json.loads(mp.read_text());cfg=json.loads((base/m["config"]).read_text())
    if cfg.get("c1_partitioned_render")is not True or cfg.get("c1_async_material_verify",False)is not False:
        raise ValueError("explicit partitioned numerical treatment required")
    events=[]
    for p in sorted((Path(c["raw_root"])/"diagnostics").glob("compact-worker-*.jsonl")):
        events.extend(json.loads(x) for x in p.read_text().splitlines())
    installs=[e for e in events if e.get("event")=="compact_hypic_hooks_installed"]
    if len(installs)!=4 or any(e.get("c1_partitioned_render")is not True for e in installs):
        raise ValueError("four-worker partition activation missing")
    workers={int(k):v for k,v in report["hot"]["worker_pids"].items()}
    report["partition"]=audit_partition_rows(events,workers,mh)
    report["scope"]="two-request actual partition/shadow/source/physical/isolation/release; no formal speed/fullquality/lifecycle"
    return report

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

"""R19 actual skipped initial snapshots plus unchanged R18 bounded numeric gates."""
import hashlib,json
from pathlib import Path
from audit_c1_partitioned_canary import audit as audit_partition

def audit_snapshot_receipts(events,workers,manifest):
    if set(workers)!=set(range(4)):raise ValueError("four exact workers required")
    def key(e):
        r=e.get("rank")
        if type(r)is not int or r not in workers or e.get("pid")!=workers[r] or e.get("manifest_sha256")!=manifest:
            raise ValueError("snapshot identity drift")
        if type(e.get("step"))is not int or e["step"]<1 or not isinstance(e.get("layer"),str) or not isinstance(e.get("request_id"),str):
            raise ValueError("actual request/layer/step required")
        return r,e["step"],e["layer"],e["request_id"]
    shadows={key(e) for e in events if e.get("event")=="c1_packed_wave_shadow_checked"}
    rows=[e for e in events if e.get("event")=="compact_gdn_body_composed"]
    skipped={r:set() for r in workers};kept={r:set() for r in workers};seen=set()
    for e in rows:
        k=key(e)
        if k in seen:raise ValueError("duplicate snapshot receipt")
        seen.add(k)
        flag=e.get("initial_snapshot_skipped")
        if type(flag)is not bool:raise ValueError("explicit actual snapshot receipt required")
        if flag is (k in shadows):raise ValueError("serial shadow must keep initial; prepared nonshadow must skip")
        if e.get("finite")is not True:raise ValueError("finite completed receipt required")
        (skipped if flag else kept)[k[0]].add(k[2])
    if not rows or any(len(skipped[r])!=48 or len(kept[r])!=48 for r in workers):
        raise ValueError("all48 layers must prove both skip and serial-shadow retention")
    return dict(receipts=len(rows),skipped_layers={r:len(skipped[r]) for r in workers},
                retained_shadow_layers={r:len(kept[r]) for r in workers})

def audit(path,*,live_release=False):
    cp=Path(path);c=json.loads(cp.read_text());base=cp.parent
    report=audit_partition(cp,live_release=live_release)
    mp=base/c["cache_diagnostic"]["compact_manifest"];m=json.loads(mp.read_text())
    mh=hashlib.sha256(mp.read_bytes()).hexdigest()
    cfg=json.loads((base/m["config"]).read_text())
    if cfg.get("c1_lazy_initial_snapshot")is not True:raise ValueError("explicit lazy snapshot config required")
    events=[]
    for p in (Path(c["raw_root"])/"diagnostics").glob("compact-worker-*.jsonl"):
        events.extend(json.loads(x) for x in p.read_text().splitlines())
    installs=[e for e in events if e.get("event")=="compact_hypic_hooks_installed"]
    if len(installs)!=4 or any(e.get("c1_lazy_initial_snapshot")is not True for e in installs):
        raise ValueError("four-worker lazy activation required")
    workers={int(r):pid for r,pid in report["hot"]["worker_pids"].items()}
    report["lazy_snapshot"]=audit_snapshot_receipts(events,workers,mh)
    report["scope"]="two-request bounded numeric/actualskip/source/isolation/release; not speed/fullquality"
    return report
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

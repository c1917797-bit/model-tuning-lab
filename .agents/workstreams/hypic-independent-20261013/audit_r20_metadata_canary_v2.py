"""R20 successor audit:48-layer read conservation, not single-group assumption."""
import hashlib,json
from pathlib import Path
from audit_r19_lazy_snapshot_canary import audit as audit_numeric

def audit_metadata_receipts(events,workers,manifest):
    if set(workers)!=set(range(4)):raise ValueError("four exact workers required")
    seen=set();coverage={r:set() for r in workers};rows=0
    for e in events:
        if e.get("event")!="compact_model_rows_completed":continue
        rank=e.get("rank");step=e.get("step")
        if (type(rank)is not int or rank not in workers or e.get("pid")!=workers[rank]
                or e.get("manifest_sha256")!=manifest or type(step)is not int or step<1):
            raise ValueError("metadata receipt identity mismatch")
        if (rank,step)in seen:raise ValueError("duplicate forward receipt")
        seen.add((rank,step))
        reads=e.get("metadata_snapshot_reads");hits=e.get("metadata_snapshot_hits")
        if (e.get("forward_metadata_snapshot")is not True or type(reads)is not int
                or reads<1 or type(hits)is not int or hits<reads
                or reads+hits not in (3*48,6*48)
                or reads % ((reads+hits)//48)!=0):
            raise ValueError("actual bounded metadata reads and reuse required")
        ids=e.get("request_ids")
        if not isinstance(ids,list)or not ids or any(not isinstance(x,str)or not x for x in ids):
            raise ValueError("forward request coverage required")
        coverage[rank].update(ids);rows+=1
    if not rows or any(not x for x in coverage.values()):
        raise ValueError("fourrank metadata reuse missing")
    return {"forwards":rows,"request_ids":{str(r):sorted(v)for r,v in coverage.items()}}

def audit(path,*,live_release=False):
    cp=Path(path);c=json.loads(cp.read_text());base=cp.parent
    report=audit_numeric(cp,live_release=live_release)
    mp=base/c["cache_diagnostic"]["compact_manifest"];m=json.loads(mp.read_text())
    cfg=json.loads((base/m["config"]).read_text())
    if cfg.get("forward_metadata_snapshot")is not True:raise ValueError("metadata config absent")
    events=[]
    for f in (Path(c["raw_root"])/"diagnostics").glob("compact-worker-*.jsonl"):
        events.extend(json.loads(x)for x in f.read_text().splitlines())
    installs=[e for e in events if e.get("event")=="compact_hypic_hooks_installed"]
    if len(installs)!=4 or any(e.get("forward_metadata_snapshot")is not True for e in installs):
        raise ValueError("fourrank metadata activation absent")
    workers={int(r):pid for r,pid in report["hot"]["worker_pids"].items()}
    report["metadata_snapshot"]=audit_metadata_receipts(events,workers,hashlib.sha256(mp.read_bytes()).hexdigest())
    report["scope"]="bounded numeric and actual metadata reuse; not speed/full quality"
    return report

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

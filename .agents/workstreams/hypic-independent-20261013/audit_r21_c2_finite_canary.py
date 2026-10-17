"""R21 C2 finite precommit receipts plus unchanged R20 numerical/ownership gates."""
import hashlib,json
from pathlib import Path
from audit_r20_metadata_canary_v2 import audit as audit_base

def audit_finite_receipts(events,workers,manifest):
    if set(workers)!=set(range(4)):raise ValueError("exact four workers required")
    gates={};completed=set();covered=set()
    for e in events:
        kind=e.get("event")
        if kind not in ("c2_layer_precommit_validated","compact_c2_queries_completed"):continue
        rank=e.get("rank");step=e.get("step");layer=e.get("layer")
        if (type(rank)is not int or rank not in workers or e.get("pid")!=workers[rank]
                or e.get("manifest_sha256")!=manifest or type(step)is not int or step<1
                or not isinstance(layer,str)or not layer):
            raise ValueError("finite receipt identity mismatch")
        key=(rank,step,layer)
        if kind=="c2_layer_precommit_validated":
            ids=e.get("requests");n=e.get("tensors")
            if (key in gates or key in completed or not isinstance(ids,list)or not ids
                    or len(ids)!=len(set(ids))or any(not isinstance(x,str)or not x for x in ids)
                    or type(n)is not int or n!=2*len(ids)
                    or e.get("finite")is not True or e.get("actual_slot_commit")!="not_started"):
                raise ValueError("invalid finite precommit coverage/order")
            gates[key]=set(ids)
        else:
            rid=e.get("request_id");item=key+(rid,)
            if key not in gates or rid not in gates[key]or item in covered:
                raise ValueError("completion lacks unique preceding finite gate")
            covered.add(item);completed.add(key)
    expected={key+(rid,)for key,ids in gates.items()for rid in ids}
    if not gates or expected!=covered or {x[0]for x in gates}!=set(workers):
        raise ValueError("incomplete finite gate/completion join")
    return {"layers":len(gates),"request_layer_completions":len(covered),
            "scope":"all observed hot C2 completions have exact preceding same-layer/rank/step finite gate"}

def audit(path,*,live_release=False):
    cp=Path(path);c=json.loads(cp.read_text());report=audit_base(cp,live_release=live_release)
    mp=cp.parent/c["cache_diagnostic"]["compact_manifest"];m=json.loads(mp.read_text())
    cfg=json.loads((cp.parent/m["config"]).read_text())
    if cfg.get("c2_layer_finite_gate")is not True:raise ValueError("finite gate config absent")
    events=[]
    for f in (Path(c["raw_root"])/"diagnostics").glob("compact-worker-*.jsonl"):
        events.extend(json.loads(x)for x in f.read_text().splitlines())
    workers={int(r):pid for r,pid in report["hot"]["worker_pids"].items()}
    installs=[e for e in events if e.get("event")=="compact_hypic_hooks_installed"]
    if len(installs)!=4 or any(e.get("c2_layer_finite_gate")is not True for e in installs):
        raise ValueError("fourrank finite gate activation absent")
    report["c2_finite"]=audit_finite_receipts(events,workers,hashlib.sha256(mp.read_bytes()).hexdigest())
    report["scope"]="bounded R21 numerical/finite/ownership/source/isolation/release; not formal speed or full task quality"
    return report

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

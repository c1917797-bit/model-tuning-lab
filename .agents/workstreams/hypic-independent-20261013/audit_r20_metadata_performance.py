"""R20 timed whole-service screen; reuses unchanged numerical/ownership gates."""
import json,hashlib
from pathlib import Path
from audit_r19_lazy_performance import audit as audit_base
from audit_r20_metadata_canary_v2 import audit_metadata_receipts
def audit(path,*,live_release=False):
    cp=Path(path);c=json.loads(cp.read_text());report=audit_base(cp,live_release=live_release)
    if c["lazy_snapshot_treatment"]!="native":
        mp=cp.parent/c["successor_manifest"];m=json.loads(mp.read_text())
        cfg=json.loads((cp.parent/m["config"]).read_text())
        if cfg.get("forward_metadata_snapshot")is not True:raise ValueError("metadata treatment absent")
        events=[]
        for p in (Path(c["raw_root"])/"diagnostics").glob("compact-worker-*.jsonl"):
            events.extend(json.loads(x)for x in p.read_text().splitlines())
        workers={int(r):pid for r,pid in report["hot"]["worker_pids"].items()}
        report["metadata_snapshot"]=audit_metadata_receipts(events,workers,hashlib.sha256(mp.read_bytes()).hexdigest())
    report["scope"]="one R20 full40 timed arm; paired speed/quality/lifecycle separately"
    return report
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

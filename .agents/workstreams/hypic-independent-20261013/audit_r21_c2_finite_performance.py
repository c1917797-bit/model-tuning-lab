"""Prospective R21 full40 arm audit; never launches or accepts task quality."""
import hashlib,json
from pathlib import Path
from audit_r20_metadata_performance import audit as audit_base
from audit_r21_c2_finite_canary import audit_finite_receipts
def audit(path,*,live_release=False):
    cp=Path(path);c=json.loads(cp.read_text());report=audit_base(cp,live_release=live_release)
    if c["lazy_snapshot_treatment"]!="native":
        mp=cp.parent/c["successor_manifest"];m=json.loads(mp.read_text())
        cfg=json.loads((cp.parent/m["config"]).read_text())
        if cfg.get("c2_layer_finite_gate")is not True:raise ValueError("finite treatment absent")
        events=[]
        for f in (Path(c["raw_root"])/"diagnostics").glob("compact-worker-*.jsonl"):
            events.extend(json.loads(x)for x in f.read_text().splitlines())
        workers={int(r):pid for r,pid in report["hot"]["worker_pids"].items()}
        report["c2_finite"]=audit_finite_receipts(events,workers,hashlib.sha256(mp.read_bytes()).hexdigest())
    report["scope"]="one full40 R21 arm; paired/repeated performance and task quality separate"
    return report
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

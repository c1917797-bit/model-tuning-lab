"""Timed lazy-snapshot treatment audit; inherits all R18 full40 validity gates."""
import json,hashlib
from pathlib import Path
from audit_r18_partition_performance import audit as audit_partition
def validate_lazy_receipts(events,enabled):
    if type(enabled)is not bool:raise ValueError("explicit lazy boolean")
    installs=[e for e in events if e.get("event")=="compact_hypic_hooks_installed"]
    if len(installs)!=4 or any(e.get("c1_lazy_initial_snapshot")is not enabled for e in installs):
        raise ValueError("four actual lazy-mode installs required")
    rows=[e for e in events if e.get("event")in ("compact_gdn_body_composed","mixed_native_gdn_completed")]
    def key(e,rid):
        return (e.get("rank"),e.get("pid"),e.get("manifest_sha256"),e.get("step"),e.get("layer"),rid)
    prepared={key(e,rid) for e in events
        if e.get("event")in ("c1_packed_wave_prepared","native_decode_batch_completed")
        for rid in e.get("requests",[])}
    completed=set()
    for e in rows:
        k=key(e,e.get("request_id"));completed.add(k)
        expected=enabled and k in prepared
        if e.get("initial_snapshot_skipped")is not expected:
            raise ValueError("actual prepared/no-shadow snapshot receipts mismatch")
    if not rows or not prepared or not prepared.issubset(completed):
        raise ValueError("prepared request completion coverage missing")
    return dict(lazy=enabled,completed_receipts=len(rows))
def audit(path,*,live_release=False):
    cp=Path(path);c=json.loads(cp.read_text());base=cp.parent
    report=audit_partition(cp,live_release=live_release)
    treatment=c["lazy_snapshot_treatment"]
    if treatment not in ("on","off","native"):raise ValueError("frozen treatment required")
    m=json.loads((base/c["successor_manifest"]).read_text());cfg=json.loads((base/m["config"]).read_text())
    if cfg.get("c1_lazy_initial_snapshot",False)is not(treatment=="on"):
        raise ValueError("bound lazy config mismatch")
    events=[]
    for p in (Path(c["raw_root"])/"diagnostics").glob("compact-worker-*.jsonl"):
        events.extend(json.loads(x) for x in p.read_text().splitlines())
    if treatment!="native":report["lazy"]=validate_lazy_receipts(events,treatment=="on")
    report["scope"]="one same-source R19 timed arm; paired speed/fullquality/lifecycle separately"
    return report
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

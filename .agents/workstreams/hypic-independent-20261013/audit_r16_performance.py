"""Successor full40 audit adds strict no-diagnostic timed snapshot policy."""
import json,hashlib
from pathlib import Path
from audit_r15_terminal import audit_r15

def validate_timed_mode(c,cfg):
    group=c.get("performance_group")
    if group not in ("G1","G3") or c.get("formal_performance")is not True:
        raise ValueError("prospective G1/G3 full40 screen only")
    if cfg.get("prefill_prompt_snapshot")is not True or type(cfg.get("prompt_snapshot_probe_batches"))is not int or cfg["prompt_snapshot_probe_batches"]!=0:
        raise ValueError("timed snapshot treatment requires probe exactly disabled")
    if cfg.get("c1_performance_mode")is not True or cfg.get("c1_layer_shadow_validation")is not False:
        raise ValueError("explicit timed packed mode required")
    if c.get("protocol_notes",{}).get("timed_diagnostics")is not False:
        raise ValueError("diagnostic timing forbidden")
    if group=="G1" and (c.get("cache_diagnostic") or c.get("independent_acceptance",{}).get("require_hypic_markers_absent")is not True):
        raise ValueError("baseline must be algorithm off")
    if group=="G3" and not c.get("cache_diagnostic"):raise ValueError("candidate activation missing")
    return group

def audit(path,*,live_release=False):
    path=Path(path);c=json.loads(path.read_text());base=path.parent
    mp=base/c["successor_manifest"];manifest=json.loads(mp.read_text())
    cfg=json.loads((base/manifest["config"]).read_text());group=validate_timed_mode(c,cfg)
    sources=c.get("baseline_host_source_sha256") or c.get("cache_diagnostic",{}).get("source_sha256",{})
    if sources.get(c["successor_manifest"])!=hashlib.sha256(mp.read_bytes()).hexdigest():
        raise ValueError("common successor manifest binding absent")
    if group=="G3" and c["cache_diagnostic"]["compact_manifest"]!=c["successor_manifest"]:
        raise ValueError("different active successor manifest")
    report=audit_r15(path,live_release=live_release)
    raw=Path(c["raw_root"])
    for f in (raw/"diagnostics").glob("compact-worker-*.jsonl"):
        for line in f.read_text().splitlines():
            e=json.loads(line)
            if e.get("event")=="prompt_snapshot_opportunity":raise ValueError("probe event in timed phase")
            if e.get("event")=="compact_hypic_hooks_installed" and (e.get("prefill_prompt_snapshot")is not True or type(e.get("prompt_snapshot_probe_batches"))is not int or e["prompt_snapshot_probe_batches"]!=0):
                raise ValueError("worker timed snapshot flags contradict contract")
    report["snapshot_timed_policy_verified"]=True
    report["scope"]="one successor full40 timed phase; matched pair/three rounds/full quality/lifecycle remain separate"
    return report
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

"""Full40 R15 raw audit; numerical canary and task quality remain separate."""
import json,hashlib,subprocess
from pathlib import Path
from audit_formal_terminal_r15 import audit_unit
from audit_full40_hot_coverage import audit_full40_hot
from audit_c1_http_identity import resolve_http_ids
from audit_c1_packed_performance import audit_packed_performance
from audit_physical_worker_namespaces import audit_physical_workers

def audit_r15(path,*,live_release=False):
    path=Path(path);c=json.loads(path.read_text());raw=Path(c["raw_root"])
    report=audit_unit(raw,path)
    unit=json.loads((raw/"performance-unit.json").read_text())
    if unit["input_sha256"]!=c["formal_token_artifact"]["sha256"]:
        raise ValueError("immutable input identity mismatch")
    journal=[json.loads(l) for l in (raw/"events.jsonl").read_text().splitlines()]
    samples=[e["snapshot"] for e in journal if e.get("event")=="isolation"]
    if {n for s in samples for n,p in s["processes"]}!={0,1,2,3}:
        raise ValueError("actual physical four-card coverage absent")
    if c.get("cache_diagnostic"):
        mp=path.parent/c["cache_diagnostic"]["compact_manifest"]
        m=json.loads(mp.read_text());cfg=json.loads((path.parent/m["config"]).read_text())
        if cfg.get("c1_performance_mode")is not True or cfg.get("c1_layer_shadow_validation")is not False:
            raise ValueError("explicit timed mode required")
        events=[]
        for f in sorted((raw/"diagnostics").glob("compact-worker-*.jsonl")):
            events.extend(json.loads(l) for l in f.read_text().splitlines())
        digest=hashlib.sha256(mp.read_bytes()).hexdigest()
        ids=[e["metrics"]["request_id"] for e in unit["results"]]
        hot=audit_full40_hot(events,ids,manifest_sha256=digest)
        if hot["accepted_hot_coverage"]is not True:raise ValueError("full40 hot coverage missing")
        actual=sorted({e["request_id"] for e in events if e.get("event")=="compact_gdn_body_composed"})
        mapping=resolve_http_ids(ids,actual,expected_count=40)
        layers=sorted({e["layer"] for e in events if e.get("event")=="compact_public_state_published"})
        workers=hot["worker_pids"]
        geometry={"key_heads":4,"query_heads":4,"value_heads":12,"wy_heads":12,
                  "gate_heads":12,"key_width":128,"value_width":128,"head_layout":"native_grouped"}
        report["packed"]=audit_packed_performance(events,workers,manifest_sha256=digest,
            linear_layers=layers,requests=[mapping[x] for x in ids],state_passes=2,
            seed_mode="actual_prefix_terminal",head_geometry=geometry)
        start=json.loads((raw/"service-start.json").read_text())
        report["physical"]=audit_physical_workers(samples,workers,owned_cid=start["container_id"])
        report["hot"]=hot;report["request_map"]=mapping
    if live_release:
        from formal_r15_tp4 import snapshot,port_free
        cid=json.loads((raw/"service-start.json").read_text())["container_id"]
        q=subprocess.run(["docker","inspect",cid],capture_output=True,text=True)
        if q.returncode==0 or q.stdout.strip()!="[]" or not ("No such object" in q.stderr or "No such container" in q.stderr):
            raise ValueError("exact owned container absence not proven")
        s=snapshot()
        if s["processes"] or s["foreign"]:raise ValueError("physical0-3 not released")
        port_free(c["port"]);report["live_release_verified"]=True
    report["scope"]="one full40 timed phase only; all12 matched phases and full quality/lifecycle still required"
    return report

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True)
    p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit_r15(a.contract,live_release=a.live_release)))

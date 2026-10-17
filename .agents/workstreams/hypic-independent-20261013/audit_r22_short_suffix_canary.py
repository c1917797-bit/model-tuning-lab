"""R22 short-suffix route/completion proof layered on full catalog Canary audit."""
import hashlib,json
from pathlib import Path
from audit_catalog_canary_terminal import audit as audit_base

def audit_routes(events,workers,manifest,*,target_api=None):
    if set(workers)!=set(range(4)):raise ValueError("exact four workers required")
    routes={};completed=set();seen_before=set();installed=set()
    for e in events:
        kind=e.get("event")
        if kind=="compact_hypic_hooks_installed":
            matches=[rank for rank,pid in workers.items()if e.get("pid")==pid]
            rank=matches[0]if len(matches)==1 else None
            if (rank is None or rank in installed or ("rank"in e and e["rank"]!=rank)
                    or e.get("pid")!=workers[rank] or e.get("manifest_sha256")!=manifest
                    or e.get("c1_short_suffix_recurrent")is not True):
                raise ValueError("source-bound fourrank short-suffix activation required")
            installed.add(rank);continue
        if kind not in ("c1_short_suffix_recurrent_route","compact_gdn_body_composed"):continue
        rank=e.get("rank");rid=e.get("request_id");step=e.get("step");layer=e.get("layer")
        if (type(rank)is not int or rank not in workers or e.get("pid")!=workers[rank]
                or e.get("manifest_sha256")!=manifest or type(step)is not int or step<1
                or not isinstance(rid,str)or not rid or not isinstance(layer,str)or not layer):
            raise ValueError("short suffix receipt identity mismatch")
        key=(rank,step,layer,rid)
        if kind=="c1_short_suffix_recurrent_route":
            n=e.get("rows");lo=e.get("packed_start");hi=e.get("packed_end")
            if (key in routes or key in seen_before or type(n)is not int or not 1<=n<=64
                    or type(lo)is not int or type(hi)is not int or not 0<=lo<hi or hi-lo!=n
                    or e.get("source_end",0)-e.get("source_start",0)!=n
                    or e.get("window")!="suffix"or e.get("branch")!="independent_recurrent_le64"
                    or e.get("output_and_terminal")is not True
                    or e.get("actual_slot_commit")!="not_started"):
                raise ValueError("unique precommit short suffix geometry required")
            routes[key]=n
        else:
            if key in seen_before:raise ValueError("duplicate completion")
            seen_before.add(key)
            if key in routes:completed.add(key)
    if installed!=set(workers)or not routes or set(routes)!=completed or {x[0]for x in routes}!=set(workers):
        raise ValueError("complete allrank route/completion coverage required")
    target={x[0]for x in routes if target_api and (x[3]==target_api or x[3].startswith(target_api+"-0-"))}
    return dict(routes=len(routes),covered_ranks=sorted({x[0]for x in routes}),
        row_counts=sorted(set(routes.values())),failed_sample_short_route_ranks=sorted(target),
        scope="actual short suffix output/state route precedes same-rank/step/layer/request completion; not whole quality or exact prior batch reproduction")

def audit(path,*,live_release=False):
    cp=Path(path).resolve();c=json.loads(cp.read_text())
    if c["quality_workload"].get("canary_selection")!="first_batch_regression":
        raise ValueError("same first failed batch selection required")
    report=audit_base(cp,live_release=live_release)
    mp=cp.parent/c["cache_diagnostic"]["compact_manifest"];m=json.loads(mp.read_text())
    cfg=json.loads((cp.parent/m["config"]).read_text())
    if cfg.get("c1_short_suffix_recurrent")is not True:raise ValueError("short suffix config absent")
    raw=Path(c["raw_root"]);events=[]
    for f in sorted((raw/"diagnostics").glob("compact-worker-*.jsonl")):
        events.extend(json.loads(x)for x in f.read_text().splitlines())
    unit=json.loads((raw/"catalog-canary-unit.json").read_text())
    target=[x for x in unit["results"]if x["phase"]==0 and x["index"]==6]
    if len(target)!=1:raise ValueError("original failed sample missing")
    workers={int(r):pid for r,pid in report["hot"]["worker_pids"].items()}
    shadows=[e for e in events if e.get("event")=="c1_packed_wave_shadow_checked"]
    if not shadows or {e.get("rank")for e in shadows}!=set(workers)or any(
            e.get("passed")is not True or e.get("atol")!=.01 or e.get("rtol")!=.003
            or e.get("pid")!=workers.get(e.get("rank"))
            or e.get("manifest_sha256")!=hashlib.sha256(mp.read_bytes()).hexdigest()for e in shadows):
        raise ValueError("unchanged fourrank C1 numerical shadow evidence required")
    from audit_r21_c2_finite_canary import audit_finite_receipts
    report["c2_finite"]=audit_finite_receipts(events,workers,hashlib.sha256(mp.read_bytes()).hexdigest())
    report["c1_shadow"]=dict(observed=len(shadows),passed=True,atol=.01,rtol=.003,
        scope="all observed frozen-policy shadows; not full tensor or task quality equivalence")
    report["short_suffix"]=audit_routes(events,workers,hashlib.sha256(mp.read_bytes()).hexdigest(),
                                        target_api=target[0]["request_id"])
    report["rebuild"]["transition_count"]=len(report["rebuild"].pop("transitions"))
    report["hot"]["covered_count"]=len(report["hot"].pop("covered_runtime_ids"))
    report["scope"]="R22 first-batch regression plus bounded17 catalog mechanism; not381quality, speed, lifecycle or exact old scheduler batch reproduction"
    return report

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true")
    a=p.parse_args();print(json.dumps(audit(a.contract,live_release=a.live_release)))

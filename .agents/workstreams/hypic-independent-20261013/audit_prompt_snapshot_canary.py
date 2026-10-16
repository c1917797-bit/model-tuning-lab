"""Independent source-bound audit for the two-request snapshot integration Canary."""
import hashlib,json,math,subprocess
from pathlib import Path
from audit_full40_hot_coverage import _audit_hot
from audit_physical_worker_namespaces import audit_physical_workers

def audit_probe_rows(events,workers,manifest,private_ids):
    rows=[e for e in events if e.get("event")=="prompt_snapshot_opportunity"]
    if any(type(e.get("rank"))is not int or type(e.get("pid"))is not int for e in rows):
        raise ValueError("strict rank/PID identities required")
    summaries={}
    for rank,pid in workers.items():
        selected=[e for e in rows if e.get("rank")==rank]
        if len(selected)!=2:raise ValueError("exact two bounded probes per rank required")
        steps=set();totals={"original_thread_cpu_ns":0,"prefill_only_thread_cpu_ns":0}
        orders=set()
        for e in selected:
            if e.get("pid")!=pid or e.get("manifest_sha256")!=manifest:
                raise ValueError("probe source/worker mismatch")
            step=e.get("step")
            if type(step)is not int or step<=0 or step in steps:raise ValueError("unique valid probe steps required")
            steps.add(step);ids=e.get("request_ids",[])
            if not ids or len(ids)!=len(set(ids)) or not set(ids)<=set(private_ids):
                raise ValueError("probe request not in completed private cohort")
            if len(e.get("computed_tokens",[]))!=len(ids) or len(e.get("scheduled_tokens",[]))!=len(ids):
                raise ValueError("probe request/count association incomplete")
            if any(type(n)is not int or n<32768 for n in e["computed_tokens"]) or any(type(n)is not int for n in e["scheduled_tokens"]) or e["scheduled_tokens"]!=[1]*len(ids):
                raise ValueError("expected completed single-token decode only")
            if set(e.get("omitted_decode_ids",[]))!=set(ids) or e.get("retained_prefill_ids")!=[]:
                raise ValueError("decode omission evidence incomplete")
            if type(e.get("omitted_prompt_tokens"))is not int or e["omitted_prompt_tokens"]!=32768*len(ids):
                raise ValueError("original prompt denominator mismatch")
            order=tuple(e.get("order",[]))
            if order not in (("original","prefill_only"),("prefill_only","original")):
                raise ValueError("invalid measurement order")
            orders.add(order)
            m=e.get("measurements",{})
            if set(m)!={"original","prefill_only"}:raise ValueError("paired clock evidence missing")
            for name in m:
                if set(m[name])!={"wall_ns","thread_cpu_ns"}:raise ValueError("clock names mismatch")
                if any(type(v)is not int or v<0 for v in m[name].values()):
                    raise ValueError("nonfinite/invalid clock")
                totals[name+"_thread_cpu_ns"]+=m[name]["thread_cpu_ns"]
        summaries[rank]=dict(totals,steps=sorted(steps),orders=[list(x) for x in sorted(orders)])
    if len(rows)!=8 or set(workers)!=set(range(4)):raise ValueError("exact four-rank probe coverage required")
    return summaries

def audit(contract_path,*,live_release=False):
    cp=Path(contract_path).resolve();base=cp.parent;c=json.loads(cp.read_text());raw=Path(c["raw_root"])
    if c["physical_npus"]!=[0,1,2,3] or c["tp"]!=4 or c.get("formal_performance") or c.get("formal_quality"):
        raise ValueError("bounded physical0-3 Canary only")
    sources=c["cache_diagnostic"]["source_sha256"]
    for name,digest in sources.items():
        p=(base/name).resolve()
        if not p.is_relative_to(base) or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
            raise ValueError("source drift: "+name)
    if sources.get("formal_r15_tp4.py")!=c["controller_sha256"]:raise ValueError("controller source binding mismatch")
    mp=base/c["cache_diagnostic"]["compact_manifest"];m=json.loads(mp.read_text());mh=hashlib.sha256(mp.read_bytes()).hexdigest()
    cfg=json.loads((base/m["config"]).read_text())
    if cfg.get("prefill_prompt_snapshot")is not True or cfg.get("prompt_snapshot_probe_batches")!=2:
        raise ValueError("explicit bounded treatment/probe required")
    if cfg.get("c1_layer_shadow_validation")is not True or cfg.get("c1_first_divergence")is not True or cfg.get("c1_performance_mode",False)is not False:
        raise ValueError("correctness shadows must remain enabled in Canary")
    result=json.loads((raw/"result.json").read_text());records=json.loads((raw/"responses.json").read_text())
    events=[json.loads(x) for x in (raw/"events.jsonl").read_text().splitlines()]
    if result.get("valid")is not True or result.get("error")is not None or result.get("guard_errors") or result.get("responses")!=3:
        raise ValueError("successful complete three-response terminal required")
    if [x for x in events if x.get("event")=="terminal"]!=[{"event":"terminal","result":result}]:
        raise ValueError("terminal journal mismatch")
    journal=[{k:v for k,v in x.items() if k!="event"} for x in events if x.get("event")=="response"]
    if journal!=records or len(records)!=3 or {x["index"] for x in records}!={0,1,2}:raise ValueError("request journal mismatch")
    for r in records:
        i=r["index"];usage=r["response"]["usage"]
        if len(r["payload"]["prompt"])!=(16640 if i==0 else 32768) or usage["prompt_tokens"]!=len(r["payload"]["prompt"]) or usage["completion_tokens"]!=(1 if i==0 else 1024):
            raise ValueError("same-size exact request protocol mismatch")
    if len({r["response"]["id"] for r in records})!=3:raise ValueError("duplicate response")
    artifact_path=Path(c["formal_token_artifact"]["path"]);artifact_raw=artifact_path.read_bytes()
    if hashlib.sha256(artifact_raw).hexdigest()!=c["formal_token_artifact"]["sha256"]:
        raise ValueError("input artifact identity drift")
    artifact=json.loads(artifact_raw);public=artifact["public_segment"]
    first=artifact["requests"][0];end=first["segment_end"]
    expected=[public+first["token_ids"][end:end+256],
              artifact["requests"][0]["token_ids"],artifact["requests"][1]["token_ids"]]
    for r in records:
        payload=r["payload"];i=r["index"]
        if (payload["prompt"]!=expected[i] or payload.get("max_tokens")!=(1 if i==0 else 1024)
                or payload.get("ignore_eos")is not True or payload.get("seed")!=0
                or payload.get("temperature")!=0):
            raise ValueError("actual payload differs from frozen input protocol")
    worker_events=[]
    for p in sorted((raw/"diagnostics").glob("compact-worker-*.jsonl")):
        worker_events.extend(json.loads(x) for x in p.read_text().splitlines())
    private=[r["response"]["id"] for r in records if r["index"]in (1,2)]
    hot=_audit_hot(worker_events,private,manifest_sha256=mh,expected_count=2)
    if not hot["accepted_hot_coverage"]:raise ValueError("two-request same-step four-rank48/16 hot proof required")
    installs=[x for x in worker_events if x.get("event")=="compact_hypic_hooks_installed"]
    if len(installs)!=4 or {x["pid"] for x in installs}!=set(hot["worker_pids"].values()) or any(x.get("manifest_sha256")!=mh or x.get("prefill_prompt_snapshot")is not True or x.get("prompt_snapshot_probe_batches")!=2 for x in installs):
        raise ValueError("source-bound four-worker snapshot activation missing")
    runtime_ids={x["request_id"] for x in worker_events if x.get("event")=="compact_gdn_body_composed"
                 and any(x.get("request_id","").startswith(p+"-") for p in private)}
    probe=audit_probe_rows(worker_events,hot["worker_pids"],mh,runtime_ids)
    samples=[x["snapshot"] for x in events if x.get("event")=="isolation"]
    if not samples or samples!=json.loads((raw/"isolation.json").read_text()) or len(samples)!=result["isolation_samples"] or any(x["foreign"] for x in samples):
        raise ValueError("continuous isolation mismatch")
    start=json.loads((raw/"service-start.json").read_text());release=json.loads((raw/"release.json").read_text())
    if release!=result["release"] or release["owned_container"]!=start["container_id"] or release.get("removed")is not True or release.get("port_free")is not True or release.get("final_physical_processes"):
        raise ValueError("exact owned release mismatch")
    if start["image"]!=c["image"] or set(start["devices"])!={"/dev/davinci"+str(i) for i in range(4)}:
        raise ValueError("image/physical scope mismatch")
    physical=audit_physical_workers(samples,hot["worker_pids"],owned_cid=start["container_id"])
    if live_release:
        from formal_r15_tp4 import snapshot,port_free
        q=subprocess.run(["docker","inspect",start["container_id"]],capture_output=True,text=True)
        if q.returncode==0 or q.stdout.strip()!="[]" or not ("No such object" in q.stderr or "No such container" in q.stderr):
            raise ValueError("exact container absence not proved")
        if snapshot()["processes"]:raise ValueError("physical0-3 not empty")
        port_free(c["port"])
    return {"bounded_canary_valid":True,"hot":hot,"probe":probe,"physical":physical,
            "source_bindings":len(sources),"isolation_samples":len(samples),"live_release_verified":live_release,
            "scope":"two-request integrated mechanism and prepare-thread opportunity only; no formal speed, full quality or lifecycle acceptance"}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

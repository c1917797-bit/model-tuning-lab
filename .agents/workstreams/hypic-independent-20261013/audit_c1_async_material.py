"""Independent source-bound audit for the two-request C1 asynchronous material transfer Canary."""
import hashlib,json,math,subprocess
from pathlib import Path
from audit_full40_hot_coverage import _audit_hot
from audit_physical_worker_namespaces import audit_physical_workers

def audit_transfer_rows(events,workers,manifest,private_ids):
    """Join every completed hot layer to a full-byte check of its exact lease."""
    runtime_ids={e["request_id"] for e in events
        if e.get("event")=="compact_gdn_body_composed"
        and any(e.get("request_id","")==p or e.get("request_id","").startswith(p+"-") for p in private_ids)}
    rows=[e for e in events if e.get("event")=="c1_private_material_transfer_verified"]
    publications={}
    for e in events:
        if e.get("event")=="compact_public_state_published":
            key=(e.get("rank"),e.get("layer"),e.get("generation"),e.get("tokens_sha256"))
            publications[key]=e
    leases={}
    for e in rows:
        rank=e.get("rank");pid=e.get("pid");step=e.get("step");generation=e.get("generation")
        if (type(rank)is not int or workers.get(rank)!=pid
                or type(pid)is not int or e.get("manifest_sha256")!=manifest
                or type(step)is not int or step<=0 or type(generation)is not int or generation<=0):
            raise ValueError("copy audit source/worker/step/generation mismatch")
        ids=e.get("request_ids",[])
        if not ids or len(ids)!=len(set(ids)) or not set(ids)<=runtime_ids:
            raise ValueError("copy audit request cohort mismatch")
        if e.get("full_transfer_bytes_compared")is not True or e.get("actual_slot_commit")!="not_started":
            raise ValueError("copy audit full-byte precommit proof missing")
        pub=publications.get((rank,e.get("layer"),generation,e.get("tokens_sha256")))
        if not pub or pub.get("pid")!=pid or pub.get("manifest_sha256")!=manifest:
            raise ValueError("copy audit published generation/source missing")
        metrics=e.get("metrics",[])
        if len(metrics)!=3 or {m.get("tensor")for m in metrics}!={"transition","zero_state","conv_tail"}:
            raise ValueError("copy audit requires all three material tensors")
        for m in metrics:
            shape=m.get("shape",[]);dtype=m.get("dtype")
            if (not shape or any(type(v)is not int or v<=0 for v in shape)
                    or dtype not in ("torch.float32","torch.bfloat16","torch.float16")
                    or m.get("all_bytes_equal")is not True):
                raise ValueError("invalid full material-copy metric")
            count=1
            for dim in shape:count*=dim
            if type(m.get("bytes"))is not int or m["bytes"]!=count*(4 if dtype=="torch.float32"else 2):
                raise ValueError("copy audit byte denominator mismatch")
            expected=([3,2560] if m["tensor"]=="conv_tail" else
                      pub["transition_shape" if m["tensor"]=="transition" else "zero_state_shape"])
            if shape!=expected:raise ValueError("actual27B material shape mismatch")
        key=(rank,step,e.get("layer"),generation)
        if key in leases:raise ValueError("duplicate material copy receipt")
        leases[key]=e
    hot=[e for e in events if e.get("event")=="compact_gdn_body_composed"
         and e.get("request_id")in runtime_ids]
    counts={rank:0 for rank in workers};matched=0
    for e in hot:
        row=leases.get((e.get("rank"),e.get("step"),e.get("layer"),e.get("generation")))
        if (not row or e["request_id"]not in row["request_ids"]
                or e.get("pid")!=row["pid"] or e.get("manifest_sha256")!=manifest):
            raise ValueError("completed C1 hot request lacks exact copied-lease proof")
        counts[e["rank"]]+=1;matched+=1
    if set(workers)!=set(range(4)) or len(private_ids)!=2 or not runtime_ids or any(v<96 for v in counts.values()):
        raise ValueError("two-request fourrank48layer transfer coverage incomplete")
    if any(not any(e.get("rank")==rank for e in rows)for rank in workers):
        raise ValueError("missing worker transfer proof")
    return {"all_completed_hot_receipts_joined":True,"matched_hot_receipts":matched,
        "copy_leases":len(leases),"per_rank_completed_hot":counts,
        "scope":"full bytes for observed C1 material leases, not algorithm numerical equivalence or task quality"}

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
    if cfg.get("c1_async_material_transfer")is not True or cfg.get("c1_async_material_verify")is not True:
        raise ValueError("explicit asynchronous transfer plus full copy verification required")
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
    if (len(installs)!=4 or {x["pid"] for x in installs}!=set(hot["worker_pids"].values())
            or any(x.get("manifest_sha256")!=mh or x.get("c1_async_material_transfer")is not True
                   or x.get("c1_async_material_verify")is not True for x in installs)):
        raise ValueError("source-bound four-worker transfer activation missing")
    transfers=audit_transfer_rows(worker_events,hot["worker_pids"],mh,private)
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
    return {"bounded_canary_valid":True,"hot":hot,"transfers":transfers,"physical":physical,
            "source_bindings":len(sources),"isolation_samples":len(samples),"live_release_verified":live_release,
            "scope":"two-request integrated mechanism and exact material-copy bytes only; no formal speed, full quality or lifecycle acceptance"}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");a=p.parse_args()
    print(json.dumps(audit(a.contract,live_release=a.live_release)))

"""Transparent post-run observational correction; original frozen audit remains failed."""
import hashlib,json
from pathlib import Path
from independent_pdc_progress_audit import audit_initial_prefix

def bind_pic_starts(path, expected_sha256, results, mapping):
    data=Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected_sha256:
        raise ValueError("immutable input hash drift")
    artifact=json.loads(data)
    public=artifact["public_segment"];prefix=artifact["native_prefix"]
    if len(public)!=16384 or len(prefix)!=8192:
        raise ValueError("frozen public/native shape drift")
    if len(results)!=16 or {x["index"] for x in results}!=set(range(16)):
        raise ValueError("exact16 original case indices required")
    cases={x["index"]:x for x in artifact["requests"]}
    starts={}
    for result in results:
        api=result["response"]["id"]
        if api not in mapping:raise ValueError("HTTP input association missing")
        case=cases[result["index"]];tokens=case["token_ids"]
        lo,hi=case["segment_start"],case["segment_end"]
        if (type(lo)is not int or type(hi)is not int or not 8192<=lo<hi<=32768
                or hi-lo!=16384 or len(tokens)!=32768
                or tokens[:8192]!=prefix or tokens[lo:hi]!=public):
            raise ValueError("actual input PIC geometry/token drift")
        starts[mapping[api]]=lo
    if len(starts)!=16:raise ValueError("input/runtime identity collision")
    return starts

def audit_pdc_observed(events,scheduler,mapping,workers,starts,*,manifest_sha256):
    wanted=set(mapping.values())
    if len(mapping)!=16 or len(wanted)!=16 or set(starts)!=wanted:
        raise ValueError("exact16 mapping/geometry required")
    if set(workers)!=set(range(4)) or len(set(workers.values()))!=4:
        raise ValueError("exact four workers required")
    caps=[e for e in scheduler if e.get("event")=="pic_scheduler_boundary_capped"
          and e.get("request_id") in wanted]
    if not caps:raise ValueError("actual source-bound block proof absent")
    for e in caps:
        if (e.get("manifest_sha256")!=manifest_sha256
                or type(e.get("native_block_size"))is not int or e["native_block_size"]!=1536
                or e.get("pic_start")!=starts[e["request_id"]]
                or e.get("pic_end")!=starts[e["request_id"]]+16384):
            raise ValueError("observed block/source/geometry conflict")
    proofs=[]
    for api,rid in mapping.items():
        rows=[e for e in events if e.get("event")=="native_request_progress"
              and e.get("request_id")==rid]
        if any(e.get("manifest_sha256")!=manifest_sha256 or e.get("rank")not in workers
               or e.get("pid")!=workers[e["rank"]] for e in rows):
            raise ValueError("source/worker conflict")
        proofs.append(dict(audit_initial_prefix(rows,rid,pic_start=starts[rid],native_prefix=7680),
                           http_id=api,pic_start=starts[rid]))
    return {"pdc_observational_acceptance":True,"requests":proofs,
            "actual_block_tokens":1536,"block_receipts":len(caps),
            "requests_with_conditional_cap":len({e["request_id"] for e in caps}),
            "original_frozen_audit":"exec-000000000000087b FAIL retained",
            "correction":"cap emits only when proposal changed; per-request hit uses actual first runner progress",
            "scope":"revised observational PDC proof, not original incidental-event gate pass or speed/quality"}

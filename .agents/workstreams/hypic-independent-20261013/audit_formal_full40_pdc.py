"""Prospective full40 PDC proof; does not alter any frozen R14/R15 audit."""
import hashlib,json
from pathlib import Path
from independent_pdc_progress_audit import audit_initial_prefix

def _mapping(mapping):
    if (len(mapping)!=40 or len(set(mapping.values()))!=40
            or any(not isinstance(k,str) or not k.strip() or not isinstance(v,str)
                   or not v.strip() for k,v in mapping.items())):
        raise ValueError("exact40 unique HTTP/runtime identities required")

def bind_full40_pic_starts(path,expected_sha256,results,mapping):
    _mapping(mapping)
    path=Path(path)
    if not path.is_absolute() or path.is_symlink() or path.stat().st_size>33554432:
        raise ValueError("bounded immutable absolute token artifact required")
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected_sha256:
        raise ValueError("immutable input hash drift")
    artifact=json.loads(data);cases=artifact["requests"]
    if (len(cases)!=40 or any(type(c.get("index"))is not int for c in cases)
            or {c["index"] for c in cases}!=set(range(40))):
        raise ValueError("exact40 original input indices required")
    if (len(results)!=40 or any(type(x.get("index"))is not int for x in results)
            or {x["index"] for x in results}!=set(range(40))
            or any(x.get("ok")is not True for x in results)):
        raise ValueError("exact40 successful scored records required")
    public=artifact["public_segment"];prefix=artifact["native_prefix"]
    if len(public)!=16384 or len(prefix)!=8192:
        raise ValueError("frozen public/native shape drift")
    by_index={x["index"]:x for x in cases};starts={};api_seen=set()
    for result in results:
        api=result["metrics"]["request_id"]
        if api not in mapping or api in api_seen:raise ValueError("HTTP identity mismatch")
        api_seen.add(api);case=by_index[result["index"]];tokens=case["token_ids"]
        lo,hi=case["segment_start"],case["segment_end"]
        if (type(lo)is not int or type(hi)is not int or not 8192<=lo<hi<=32768
                or hi-lo!=16384 or len(tokens)!=32768 or tokens[:8192]!=prefix
                or tokens[lo:hi]!=public):
            raise ValueError("actual input PIC geometry/token drift")
        starts[mapping[api]]=lo
    if api_seen!=set(mapping):raise ValueError("HTTP input denominator mismatch")
    return starts

def audit_full40_pdc(events,scheduler,mapping,workers,starts,*,manifest_sha256):
    _mapping(mapping);wanted=set(mapping.values())
    if (set(starts)!=wanted or any(type(x)is not int or not 8192<=x<=16384
                                   for x in starts.values())):
        raise ValueError("exact40 bound geometries required")
    if (set(workers)!=set(range(4)) or any(type(x)is not int for x in workers)
            or any(type(p)is not int or p<=0 for p in workers.values())
            or len(set(workers.values()))!=4):
        raise ValueError("four unique rank/PID identities required")
    if not isinstance(manifest_sha256,str) or len(manifest_sha256)!=64:
        raise ValueError("source-bound manifest required")
    caps=[e for e in scheduler if e.get("event")=="pic_scheduler_boundary_capped"
          and e.get("request_id")in wanted]
    if not caps:raise ValueError("actual source-bound1536 block proof absent")
    for e in caps:
        if (e.get("manifest_sha256")!=manifest_sha256
                or type(e.get("native_block_size"))is not int
                or e["native_block_size"]!=1536
                or e.get("pic_start")!=starts[e["request_id"]]
                or e.get("pic_end")!=starts[e["request_id"]]+16384):
            raise ValueError("observed block/source/geometry conflict")
    proofs=[]
    for api,rid in mapping.items():
        rows=[e for e in events if e.get("event")=="native_request_progress"
              and e.get("request_id")==rid]
        if any(e.get("manifest_sha256")!=manifest_sha256
               or type(e.get("rank"))is not int or e["rank"]not in workers
               or e.get("pid")!=workers[e["rank"]] for e in rows):
            raise ValueError("source/worker conflict")
        proof=audit_initial_prefix(rows,rid,pic_start=starts[rid],native_prefix=7680)
        proofs.append(dict(proof,http_id=api,pic_start=starts[rid]))
    return {"full40_pdc_observed":True,"requests":proofs,"actual_block_tokens":1536,
            "block_receipts":len(caps),
            "requests_with_conditional_cap":len({e["request_id"] for e in caps}),
            "scope":"all40 initial native runner reuse/fourrank/source/geometry; not timing, quality or standalone G2 proof"}

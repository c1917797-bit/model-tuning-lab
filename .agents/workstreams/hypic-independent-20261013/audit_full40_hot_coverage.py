"""Full40 mixed-batch hot coverage; no transport/timing/release acceptance."""
from collections import defaultdict

def audit_full40_hot(events, response_ids, *, manifest_sha256):
    return _audit_hot(events,response_ids,manifest_sha256=manifest_sha256,expected_count=40)

def audit_profile16_hot(events, response_ids, *, manifest_sha256):
    result=_audit_hot(events,response_ids,manifest_sha256=manifest_sha256,expected_count=16)
    result["scope"]="diagnostic16 same-step all-rank/all-layer coverage only; never formal full40 acceptance"
    return result

def _audit_hot(events, response_ids, *, manifest_sha256, expected_count):
    response_ids=tuple(response_ids)
    if len(response_ids)!=expected_count or len(set(response_ids))!=expected_count or any(not x for x in response_ids):
        raise ValueError("exact"+str(expected_count)+" unique HTTP response IDs required")
    relevant={"compact_public_state_published","compact_public_kv_published",
        "compact_gdn_body_composed","compact_c2_queries_completed",
        "compact_model_rows_completed","native_request_progress"}
    rows=[x for x in events if x.get("event") in relevant]
    public=defaultdict(set); layers=defaultdict(dict); models=defaultdict(list)
    progress=defaultdict(list); pids=defaultdict(set)
    for x in rows:
        if x.get("manifest_sha256")!=manifest_sha256:
            raise ValueError("manifest identity drift")
        rank=x.get("rank");pid=x.get("pid")
        if type(rank) is not int or rank not in range(4) or type(pid) is not int or pid<=0:
            raise ValueError("invalid rank/PID")
        pids[rank].add(pid);kind=x["event"]
        if kind.startswith("compact_public_"):
            public[(rank,kind)].add(x["layer"]);continue
        key=(rank,x.get("request_id"),x.get("step"))
        if kind=="compact_model_rows_completed":
            for rid in x["request_ids"]:models[(rank,rid,x["step"])].append(x)
        elif kind=="native_request_progress":progress[key].append(x)
        else:
            layerkey=(kind,x["layer"])
            if layerkey in layers[key]:raise ValueError("duplicate hot layer/step")
            layers[key][layerkey]=x
    if set(pids)!=set(range(4)) or any(len(x)!=1 for x in pids.values()) or len({next(iter(x)) for x in pids.values()})!=4:
        raise ValueError("four stable independent worker identities required")
    for rank in range(4):
        if len(public[(rank,"compact_public_state_published")])!=48 or len(public[(rank,"compact_public_kv_published")])!=16:
            raise ValueError("complete public layer inventory missing")
    covered=[];missing=[]
    for api_id in response_ids:
        ids={key[1] for key in layers if key[1] and key[1].startswith(api_id+"-")}
        if len(ids)!=1:missing.append(api_id);continue
        rid=ids.pop();valid=True;steps=[]
        for rank in range(4):
            keys=[key for key in layers if key[:2]==(rank,rid)]
            if len(keys)!=1:valid=False;continue
            key=keys[0];xs=layers[key];steps.append(key[2])
            if len(models[key])!=1 or len(progress[key])!=1:valid=False;continue
            native=progress[key][0];model=models[key][0]
            if native["pid"]!=model["pid"]:raise ValueError("native/model worker mismatch")
            batchhot=[k for k in layers if k[0]==rank and k[2]==key[2] and k[1] in model["request_ids"]]
            scheduled=[progress[k][0]["scheduled_tokens"] for k in batchhot if len(progress[k])==1]
            if (type(model.get("original_rows")) is not int or type(model.get("retained_rows")) is not int
                or model["retained_rows"]<sum(n-16376 for n in scheduled)
                or model["original_rows"]-model["retained_rows"]<16376*len(batchhot)):
                raise ValueError("aggregate model pruning contradicts hot layer receipts")
            for kind,publickind,skipfield,count in [
                ("compact_gdn_body_composed","compact_public_state_published","skipped_body_tokens",48),
                ("compact_c2_queries_completed","compact_public_kv_published","skipped_body_queries",16)]:
                selected=[x for (k,l),x in xs.items() if k==kind]
                if len(selected)!=count or {x["layer"] for x in selected}!=public[(rank,publickind)]:
                    valid=False;continue
                if any(x["pid"]!=native["pid"] or x[skipfield]!=16376 or x["retained_rows"]!=native["scheduled_tokens"]-16376 for x in selected):
                    raise ValueError("actual scheduled body-skip mismatch")
                if kind=="compact_gdn_body_composed" and any(x.get("finite") is not True for x in selected):
                    raise ValueError("nonfinite or missing state proof")
        if len(set(steps))!=1:valid=False
        (covered if valid else missing).append(api_id)
    return {"accepted_hot_coverage":len(covered)==expected_count,"denominator":expected_count,
        "covered":covered,"missing":missing,
        "worker_pids":{rank:next(iter(xs)) for rank,xs in pids.items()},
        "scope":"full40 same-step all-rank/all-layer body-skip coverage only; HTTP/source/physical/isolation/performance/quality separate"}

"""Join long chunk mechanism receipts with exact native scheduled-step counts."""
from audit_compact_mechanism import audit_mechanism

def audit_long_mechanism(events,acceptance,*,manifest_sha256):
    models=[x for x in events if x.get("event")=="compact_model_rows_completed"]
    request_ids={rid for x in models for rid in x["request_ids"]}
    if len(request_ids)!=acceptance["private_requests"]:
        raise ValueError("full private request mechanism denominator missing")
    progress=[x for x in events if x.get("event")=="native_request_progress"]
    reports=[]
    public=[x for x in events if x.get("event") in
        ("compact_public_state_published","compact_public_kv_published")]
    for rid in sorted(request_ids):
        selected=[x for x in models if rid in x["request_ids"]]
        if len(selected)!=4 or {x["rank"] for x in selected}!=set(range(4)):
            raise ValueError("exact fourrank long model receipts required")
        if any(x["request_ids"]!=[rid] for x in selected):
            raise ValueError("serial Canary model request association mismatch")
        scheduled=set()
        for model in selected:
            native=[x for x in progress if (x.get("request_id"),x.get("rank"),x.get("step"))==
                (rid,model["rank"],model["step"])]
            if len(native)!=1:raise ValueError("exact native scheduled-step receipt required")
            native=native[0]
            if native.get("manifest_sha256")!=manifest_sha256 or native["pid"]!=model["pid"]:
                raise ValueError("native/model source-worker mismatch")
            if native["scheduled_tokens"]!=model["original_rows"]:
                raise ValueError("model row count differs from native scheduled step")
            scheduled.add(native["scheduled_tokens"])
        if len(scheduled)!=1:raise ValueError("ranks disagree on scheduled rows")
        original=scheduled.pop()
        unit=dict(acceptance,private_requests=1,original_rows=original,
            model_retained_rows=original-acceptance["skipped_body_rows"])
        mechanisms=[x for x in events if x.get("event") in
            ("compact_gdn_body_composed","compact_c2_queries_completed") and x.get("request_id")==rid]
        reports.append(audit_mechanism(public+selected+mechanisms,unit,manifest_sha256=manifest_sha256))
    if any(x["worker_pids"]!=reports[0]["worker_pids"] for x in reports):
        raise ValueError("long worker mapping changed")
    if len(set(reports[0]["worker_pids"].values()))!=4:
        raise ValueError("four distinct worker identities required")
    return {"private_requests":len(reports),"requests":reports,
        "scope":"chunk-step mechanism only; HTTP association/PDC/physical/source/release audits remain separate"}

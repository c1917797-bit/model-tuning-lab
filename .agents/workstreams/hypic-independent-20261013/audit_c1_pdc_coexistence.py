"""Independent PDC coexistence receipt join; never a speed or quality score."""
from independent_pdc_progress_audit import audit_initial_prefix

def audit_pdc_requests(events, scheduler_events, mapping, workers, *, manifest_sha256):
    if len(mapping) != 16 or len(set(mapping.values())) != 16:
        raise ValueError("exact16 bijection required")
    if set(workers) != set(range(4)) or len(set(workers.values())) != 4:
        raise ValueError("four worker identities required")
    result = []
    for api, rid in mapping.items():
        caps = [e for e in scheduler_events if e.get("event") == "pic_scheduler_boundary_capped"
                and e.get("request_id") == rid]
        if not caps or any(e.get("manifest_sha256") != manifest_sha256
                           or type(e.get("native_block_size")) is not int
                           or e["native_block_size"] != 1536 for e in caps):
            raise ValueError("actual source-bound1536 scheduler block proof missing")
        starts = {e.get("pic_start") for e in caps}
        if len(starts) != 1 or any(type(s) is not int or s < 8192 for s in starts):
            raise ValueError("actual PIC start drift")
        rows = [e for e in events if e.get("event") == "native_request_progress"
                and e.get("request_id") == rid]
        if any(e.get("manifest_sha256") != manifest_sha256 or e.get("rank") not in workers
               or e.get("pid") != workers[e["rank"]] for e in rows):
            raise ValueError("source/worker mismatch")
        proof = audit_initial_prefix(rows, rid, pic_start=next(iter(starts)), native_prefix=7680)
        result.append(dict(proof, http_id=api, native_block_size=1536))
    return {"pdc_coexistence_verified": True, "requests": result,
            "scope": "all16/all4rank actual initial prefix reuse; packed/base audit separate"}

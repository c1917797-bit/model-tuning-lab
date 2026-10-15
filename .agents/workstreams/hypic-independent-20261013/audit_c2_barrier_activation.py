"""Join R6 explicit activation to independently audited hot worker identities."""
def audit_barrier_activation(events, worker_pids, *, manifest_sha256):
    if set(worker_pids)!=set(range(4)) or len(set(worker_pids.values()))!=4:
        raise ValueError("four audited hot-worker identities required")
    rows=[x for x in events if x.get("event")=="compact_hypic_hooks_installed"]
    if len(rows)!=4 or {x.get("pid") for x in rows}!=set(worker_pids.values()):
        raise ValueError("exact one activation per audited worker required")
    for x in rows:
        if x.get("manifest_sha256")!=manifest_sha256:
            raise ValueError("activation source drift")
        if x.get("c2_layer_completion_barrier") is not True or x.get("default_disabled") is not True:
            raise ValueError("explicit opt-in barrier evidence missing")
    return {"barrier_activation_verified":True,"workers":worker_pids,
        "scope":"installation identity joined to supplied hot worker identities; hot execution/physical/numerical/performance audits separate"}

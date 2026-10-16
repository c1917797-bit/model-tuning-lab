"""Select only demonstrably evicted catalog material; pure host-side evidence."""
from independent_current_material_readiness import current_materials_ready

def choose_evicted_rebuild(events,manifest_sha256,candidates):
    events=list(events);candidates=tuple(candidates)
    if not candidates or len({c["index"] for c in candidates})!=len(candidates):
        raise ValueError("distinct frozen rebuild candidates required")
    # This also validates every publication/eviction ownership and generation.
    readiness={c["index"]:current_materials_ready(events,manifest_sha256,c["tokens_sha256"]) for c in candidates}
    alive={};evicted=set()
    for event in events:
        kind=event.get("event")
        if kind not in ("compact_public_state_published","compact_public_kv_published","compact_public_material_evicted"):continue
        slot=(event["rank"],event["pool"],event["key"])
        if kind=="compact_public_material_evicted":
            previous=alive.pop(slot)
            evicted.add(previous["tokens_sha256"])
        else:alive[slot]=event
    for c in candidates:
        if not readiness[c["index"]] and c["tokens_sha256"] in evicted:
            return c["index"]
    raise ValueError("no previously published, actually evicted and currently nonready frozen candidate")

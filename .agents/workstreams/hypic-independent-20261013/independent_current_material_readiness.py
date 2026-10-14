"""Reconstruct current retained material generations, not historical counters."""
from independent_material_readiness import materials_ready

def current_materials_ready(events,manifest_sha256,tokens_sha256):
    alive={}
    for event in events:
        kind=event.get("event")
        if kind not in ("compact_public_state_published","compact_public_kv_published",
            "compact_public_material_evicted"):continue
        if event.get("manifest_sha256")!=manifest_sha256:
            raise ValueError("current material manifest drift")
        rank=event.get("rank");pool=event.get("pool");key=event.get("key");generation=event.get("generation")
        if type(rank) is not int or rank not in range(4) or pool not in ("linear","kv") or not key:
            raise ValueError("current material key/worker identity missing")
        if type(generation) is not int or generation<=0:
            raise ValueError("current material generation missing")
        slot=(rank,pool,key)
        if kind=="compact_public_material_evicted":
            previous=alive.get(slot)
            if previous is None or previous["generation"]!=generation or previous.get("pid")!=event.get("pid"):
                raise ValueError("eviction generation/worker mismatch")
            del alive[slot]
        else:
            if slot in alive:raise ValueError("immutable retained key republished")
            expected="linear" if kind=="compact_public_state_published" else "kv"
            if pool!=expected:raise ValueError("publication pool mismatch")
            alive[slot]=event
    return materials_ready(alive.values(),manifest_sha256,tokens_sha256)

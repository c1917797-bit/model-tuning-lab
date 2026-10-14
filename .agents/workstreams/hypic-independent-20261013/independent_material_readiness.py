"""Readiness counters from source-bound worker receipts, not final acceptance."""
def materials_ready(events,manifest_sha256):
    groups={}
    for x in events:
        kind=x.get("event")
        if kind not in ("compact_public_state_published","compact_public_kv_published"):continue
        if x.get("manifest_sha256")!=manifest_sha256:
            raise ValueError("material source manifest mismatch")
        rank=x.get("rank");pid=x.get("pid");layer=x.get("layer")
        if type(rank) is not int or rank not in range(4) or type(pid) is not int or pid<=0 or not layer:
            raise ValueError("material worker/layer identity invalid")
        bucket=groups.setdefault(rank,{"pids":set(),"linear":set(),"kv":set()})
        bucket["pids"].add(pid);bucket["linear" if kind=="compact_public_state_published" else "kv"].add(layer)
    if set(groups)!=set(range(4)):return False
    pids=[]
    for g in groups.values():
        if len(g["pids"])!=1:raise ValueError("rank material worker changed")
        if len(g["linear"])>48 or len(g["kv"])>16:raise ValueError("unexpected layer inventory")
        if len(g["linear"])!=48 or len(g["kv"])!=16:return False
        pids.extend(g["pids"])
    if len(set(pids))!=4:raise ValueError("independent worker mapping missing")
    return True

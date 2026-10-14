"""Readiness counters from source-bound worker receipts, not final acceptance."""
def materials_ready(events,manifest_sha256,tokens_sha256=None):
    events=list(events)
    material_events=[x for x in events if x.get("event") in
                     ("compact_public_state_published","compact_public_kv_published")]
    digests={x.get("tokens_sha256") for x in material_events}
    if tokens_sha256 is None:
        if len(digests)>1:
            raise ValueError("explicit segment identity required for multiple materials")
        tokens_sha256=next(iter(digests),None)
        if material_events and (not isinstance(tokens_sha256,str) or not tokens_sha256):
            raise ValueError("material segment identity missing")
    elif not isinstance(tokens_sha256,str) or not tokens_sha256:
        raise ValueError("invalid requested segment identity")
    groups={}
    for x in events:
        kind=x.get("event")
        if kind not in ("compact_public_state_published","compact_public_kv_published"):continue
        if x.get("manifest_sha256")!=manifest_sha256:
            raise ValueError("material source manifest mismatch")
        if x.get("tokens_sha256")!=tokens_sha256:continue
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

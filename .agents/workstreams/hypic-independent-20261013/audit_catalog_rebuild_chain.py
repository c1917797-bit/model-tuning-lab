"""Independent proof of real eviction -> new publication -> private reuse."""
def audit_rebuild_chain(events,*,manifest_sha256,initial_api,rebuild_api,tokens_sha256):
    if not initial_api or not rebuild_api or initial_api==rebuild_api:
        raise ValueError("distinct initial/rebuilt API identities required")
    hotk={"compact_gdn_body_composed":"linear","compact_c2_queries_completed":"kv"}
    publication={};evicted={};initial={};rebuilt={};republished={}
    for position,e in enumerate(events):
        kind=e.get("event")
        if kind not in set(hotk)|{"compact_public_state_published","compact_public_kv_published","compact_public_material_evicted"}:continue
        rank=e.get("rank");pool=e.get("pool")
        if e.get("manifest_sha256")!=manifest_sha256 or type(rank)is not int or rank not in range(4):
            raise ValueError("source/rank drift")
        if kind in ("compact_public_state_published","compact_public_kv_published"):
            pool="linear" if kind=="compact_public_state_published" else "kv"
            publication[(rank,pool,e["generation"])]=(position,e)
            slot=(rank,pool,e["key"])
            if slot in evicted:
                oldpos,old=evicted[slot]
                if e.get("tokens_sha256")==tokens_sha256:
                    if e["generation"]<=old["generation"] or old.get("pid")!=e.get("pid"):
                        raise ValueError("new generation and same worker required")
                    republished[slot]=(position,e)
            continue
        if kind=="compact_public_material_evicted":
            previous=publication.get((rank,pool,e.get("generation")))
            if previous is None or previous[1].get("key")!=e.get("key") or previous[1].get("pid")!=e.get("pid"):
                raise ValueError("eviction lacks exact prior producer")
            if previous[1].get("tokens_sha256")==tokens_sha256:
                slot=(rank,pool,e["key"])
                oldhot=initial.get((rank,pool,previous[1]["layer"]))
                if oldhot is None or oldhot[1]["generation"]!=e["generation"]:
                    raise ValueError("evicted material was not used by initial private request")
                evicted[slot]=(position,e)
            continue
        rid=e.get("request_id","")
        which=initial if rid.startswith(initial_api+"-") else rebuilt if rid.startswith(rebuild_api+"-") else None
        if which is None:continue
        pool=hotk[kind];key=(rank,pool,e["layer"])
        if key in which:raise ValueError("duplicate initial/rebuild layer")
        pub=publication.get((rank,pool,e.get("generation")))
        if pub is None or pub[1].get("tokens_sha256")!=tokens_sha256 or pub[1].get("layer")!=e["layer"] or pub[1].get("pid")!=e.get("pid"):
            raise ValueError("private reuse lacks exact same-worker/segment publication")
        which[key]=(position,e)
    transitions=[]
    for rank in range(4):
        for pool,count in (("linear",48),("kv",16)):
            first={k for k in initial if k[:2]==(rank,pool)}
            last={k for k in rebuilt if k[:2]==(rank,pool)}
            if len(first)!=count or first!=last:raise ValueError("complete initial/rebuild layer cohorts required")
        local=[]
        for slot,(epos,old) in evicted.items():
            if slot[0]!=rank:continue
            p=publication[(rank,slot[1],old["generation"])][1]
            fresh=republished.get(slot);hot=rebuilt.get((rank,slot[1],p["layer"]))
            if fresh is None or hot is None or not epos<fresh[0]<hot[0] or fresh[1]["generation"]!=hot[1]["generation"]:
                raise ValueError("eviction -> new producer -> private reuse chain missing")
            local.append(dict(rank=rank,pool=slot[1],key=slot[2],old_generation=old["generation"],new_generation=fresh[1]["generation"]))
        if not local:raise ValueError("real selected-material eviction required on every rank")
        transitions.extend(local)
    return {"accepted_rebuild_chain":True,"ranks":4,"transitions":transitions,
            "scope":"selected segment initial hot -> actual eviction -> new generation -> rebuilt hot; transport/complete17/physical/release audited separately"}

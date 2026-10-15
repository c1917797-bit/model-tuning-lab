"""Independent source/coordinate audit of canonical prefix-terminal routes."""
def audit_prefix_routes(events,*,manifest_sha256,required_layers=None):
    installs=[e for e in events if e.get("event")=="compact_hypic_hooks_installed"]
    if (len(installs)!=4 or len({e.get("pid") for e in installs})!=4
            or any(e.get("manifest_sha256")!=manifest_sha256
                   or e.get("c1_short_prefix_terminal_policy")!="canonical_recurrent_le64"
                   or e.get("c1_packed_wave")is not True for e in installs)):
        raise ValueError("four source-bound canonical prefix installations required")
    pids={e["pid"] for e in installs};seen=set();routes=[];groups={}
    for index,e in enumerate(events):
        if e.get("event")!="c1_prefix_terminal_route":continue
        fields=("rank","pid","step","layer")
        group=tuple(e.get(k) for k in fields)
        lo=e.get("source_start");hi=e.get("source_end")
        pl=e.get("packed_start");ph=e.get("packed_end");n=e.get("rows");job=e.get("job")
        rid=e.get("request_id")
        if (type(e.get("rank"))is not int or e["rank"] not in range(4)
                or e.get("pid") not in pids or type(e.get("step"))is not int or e["step"]<0
                or not isinstance(e.get("layer"),str) or not e["layer"]
                or e.get("manifest_sha256")!=manifest_sha256
                or e.get("policy")!="canonical_recurrent_le64" or e.get("window")!="prefix"
                or e.get("actual_slot_commit")!="not_started"
                or not isinstance(rid,str) or not rid
                or any(type(x)is not int for x in (lo,hi,pl,ph,n,job))
                or not 0<=lo<hi<=40960 or not 0<=pl<ph<=40960
                or hi-lo!=n or ph-pl!=n or job<0
                or e.get("branch")!=("independent_recurrent_le64" if n<=64 else "official_chunk64")):
            raise ValueError("actual canonical prefix route source/geometry/branch mismatch")
        key=group+(rid,job)
        if key in seen:raise ValueError("duplicate actual prefix route")
        seen.add(key);routes.append(e);groups.setdefault(group,set()).add(rid)
        matching=[x for x in events[index+1:] if
            x.get("event") in ("c1_packed_wave_prepared","c1_packed_wave_shadow_checked")
            and tuple(x.get(k) for k in fields)==group
            and rid in x.get("requests",x.get("group_requests",[]))
            and x.get("manifest_sha256")==manifest_sha256]
        if not matching:raise ValueError("route lacks subsequent same-source prepared/shadow group")
    if not routes:raise ValueError("actual prefix route evidence missing")
    for group,names in groups.items():
        matches=[e for e in events if e.get("event") in
                 ("c1_packed_wave_prepared","c1_packed_wave_shadow_checked") and
                 tuple(e.get(k) for k in ("rank","pid","step","layer"))==group]
        needed=set().union(*(set(e.get("requests",e.get("group_requests",[]))) for e in matches))
        if names!=needed:raise ValueError("prefix routes do not cover exact hot group")
    if required_layers is not None:
        expected={(rank,layer) for rank in range(4) for layer in required_layers}
        if {(r["rank"],r["layer"]) for r in routes}!=expected:
            raise ValueError("full four-worker/all-linear-layer prefix routes required")
    return dict(verified=True,routes=len(routes),
        recurrent_routes=sum(e["rows"]<=64 for e in routes),
        chunk_routes=sum(e["rows"]>64 for e in routes),
        scope="source-bound actual prefix-terminal branches; not numerical or full request acceptance")

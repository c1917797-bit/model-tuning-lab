"""Catalog quality hot audit: exact segment/generation and same-step four-rank joins."""
from collections import defaultdict
def audit_catalog_hot(events,results,input_rows,*,manifest_sha256,expected_count):
    if type(expected_count)is not int or not 1<=expected_count<=381 or len(results)!=expected_count:
        raise ValueError("explicit complete quality/canary denominator required")
    inputs={r["index"]:r for r in input_rows}
    if len(inputs)!=len(input_rows):raise ValueError("duplicate frozen sample index")
    cases={}
    for r in results:
        api=r.get("request_id");row=inputs.get(r.get("index"))
        if type(r.get("index"))is not int or r.get("ok")is not True or not isinstance(api,str) or not api or api in cases or row is None:
            raise ValueError("complete unique successful response cohort required")
        seg=row["segment"]
        if r.get("segment_sha256")!=seg["tokens_sha256"] or seg["end"]-seg["start"]<=8:
            raise ValueError("case segment identity mismatch")
        cases[api]=(seg["tokens_sha256"],seg["end"]-seg["start"])
    hotk={"compact_gdn_body_composed":"linear","compact_c2_queries_completed":"kv"}
    actual={e.get("request_id") for e in events if e.get("event")in hotk}
    runtime={}
    for api in cases:
        hits=[rid for rid in actual if isinstance(rid,str) and rid.startswith(api+"-")]
        if len(hits)!=1:raise ValueError("unique API/runtime request association required")
        runtime[hits[0]]=cases[api]
    if len(runtime)!=len(cases) or set(runtime)!=actual:raise ValueError("unaccounted/aliased hot requests")
    pids=defaultdict(set);published={};live={};inventory=defaultdict(set)
    groups=defaultdict(dict);native=defaultdict(list);models=defaultdict(list);evictions=0
    relevant=set(hotk)|{"compact_public_state_published","compact_public_kv_published",
        "compact_public_material_evicted","native_request_progress","compact_model_rows_completed"}
    for e in events:
        kind=e.get("event")
        if kind not in relevant:continue
        rank=e.get("rank");pid=e.get("pid");step=e.get("step")
        if e.get("manifest_sha256")!=manifest_sha256 or type(rank)is not int or rank not in range(4) or type(pid)is not int or pid<=0:
            raise ValueError("source/rank/PID drift")
        pids[rank].add(pid)
        if kind in ("compact_public_state_published","compact_public_kv_published"):
            pool="linear" if kind=="compact_public_state_published" else "kv"
            gen=e.get("generation");key=e.get("key");layer=e.get("layer");digest=e.get("tokens_sha256")
            if type(gen)is not int or gen<=0 or not isinstance(key,str) or not key or not isinstance(layer,str) or not layer:
                raise ValueError("complete publication identity required")
            g=(rank,pool,gen);k=(rank,pool,key)
            if g in published or k in live:raise ValueError("duplicate generation/immutable publication")
            published[g]=(key,layer,digest);live[k]=gen;inventory[(rank,pool,digest)].add(layer)
            continue
        if kind=="compact_public_material_evicted":
            pool=e.get("pool");gen=e.get("generation");key=e.get("key");k=(rank,pool,key)
            if pool not in ("linear","kv") or type(gen)is not int or live.get(k)!=gen:
                raise ValueError("eviction not associated with live exact generation")
            del live[k];evictions+=1;continue
        if type(step)is not int or step<=0:raise ValueError("valid source-bound step required")
        if kind=="native_request_progress":
            native[(rank,e.get("request_id"),step)].append(e);continue
        if kind=="compact_model_rows_completed":
            models[(rank,step)].append(e);continue
        rid=e.get("request_id");pool=hotk[kind];gen=e.get("generation")
        if rid not in runtime or type(gen)is not int or gen<=0:
            raise ValueError("hot request/material generation missing")
        pub=published.get((rank,pool,gen))
        if pub is None:raise ValueError("hot material has no prior producer generation")
        key,layer,digest=pub;expected_digest,length=runtime[rid]
        if live.get((rank,pool,key))!=gen or layer!=e.get("layer") or digest!=expected_digest:
            raise ValueError("stale/evicted/wrong-layer/wrong-segment material")
        skipfield="skipped_body_tokens" if pool=="linear" else "skipped_body_queries"
        if type(e.get(skipfield))is not int or e[skipfield]!=length-8:
            raise ValueError("selected segment body skip mismatch")
        if pool=="linear" and e.get("finite")is not True:raise ValueError("finite C1 state proof required")
        k=(rank,rid,step);lk=(pool,layer)
        if lk in groups[k]:raise ValueError("duplicate hot layer")
        groups[k][lk]=e
    if set(pids)!=set(range(4)) or any(len(x)!=1 for x in pids.values()) or len({next(iter(x)) for x in pids.values()})!=4:
        raise ValueError("four stable independent workers required")
    covered=[]
    for rid,(digest,length) in runtime.items():
        steps=[]
        for rank in range(4):
            keys=[k for k in groups if k[:2]==(rank,rid)]
            if len(keys)!=1:raise ValueError("one complete hot step per request/rank required")
            k=keys[0];steps.append(k[2]);g=groups[k]
            if len(native[k])!=1 or len(models[(rank,k[2])])!=1:raise ValueError("native/model same-step association incomplete")
            n=native[k][0];model=models[(rank,k[2])][0]
            if type(n.get("scheduled_tokens"))is not int or n["scheduled_tokens"]<=length-8 or type(n.get("computed_tokens"))is not int or n["computed_tokens"]<0:
                raise ValueError("valid native scheduled/computed token counts required")
            if model["request_ids"].count(rid)!=1:raise ValueError("request missing from actual pruned model batch")
            for pool,count in (("linear",48),("kv",16)):
                layers={layer for p,layer in g if p==pool}
                if len(layers)!=count or layers!=inventory[(rank,pool,digest)]:
                    raise ValueError("all selected-segment layers required")
                for (p,l),e in g.items():
                    if p==pool and (type(e.get("retained_rows"))is not int or e["retained_rows"]!=n["scheduled_tokens"]-(length-8)):
                        raise ValueError("scheduled/retained row proof mismatch")
        if len(set(steps))!=1:raise ValueError("TP ranks disagree on hot step")
        covered.append(rid)
    for (rank,step),ms in models.items():
        batch=[(rid,runtime[rid][1]-8) for r,rid,s in groups if r==rank and s==step]
        if not batch:continue
        if len(ms)!=1:raise ValueError("duplicate model completion")
        m=ms[0]
        if any(m["request_ids"].count(rid)!=1 for rid,_ in batch):raise ValueError("model membership mismatch")
        if type(m.get("original_rows"))is not int or type(m.get("retained_rows"))is not int or m["original_rows"]-m["retained_rows"]!=sum(skip for _,skip in batch):
            raise ValueError("actual model body pruning differs from layer receipts")
    return {"accepted_catalog_hot_coverage":True,"denominator":expected_count,
        "covered_runtime_ids":sorted(covered),"worker_pids":{r:next(iter(v)) for r,v in pids.items()},
        "generation_links":sum(len(g) for g in groups.values()),"evictions_observed":evictions,
        "scope":"catalog segment/generation/same-step four-rank48/16 model pruning only; transport/scoring/physical/release separate"}

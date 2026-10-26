"""Independent R39 original journal/transport warmup-count audit."""
def audit_target_warmups(journal,unit,contract):
    count=contract["r39_target_warmup_count"];descriptors=contract["r39_warm_descriptors"]
    if type(count)is not int or count not in(0,2)or len(descriptors)!=2:raise ValueError("explicit warmup contrast required")
    names=[e.get("event")for e in journal]
    if names.count("r38-begin")!=1 or names.count("r38-end")!=1:raise ValueError("one original measured unit required")
    begin=names.index("r38-begin");warm=[e for e in journal if e.get("event")=="r39-target-warmup"]
    starts=[e for e in journal if e.get("event")=="r39-target-warmup-begin"]
    if(len(warm)!=count or len(starts)!=count or "r39-target-warmup-failed"in names
       or unit.get("r39_target_warmup_count")!=count or unit.get("r39_warm_descriptors")!=descriptors):
        raise ValueError("actual exact warmup count/source/lifecycle differs")
    stripped=[{k:v for k,v in e.items()if k not in("event","scored")}for e in warm]
    if stripped!=unit.get("r39_target_warmups"):raise ValueError("journal/unit actual warm responses differ")
    ids=[];seconds=0.
    preps=[i for i,n in enumerate(names)if n=="warmup"]
    if len(preps)!=4:raise ValueError("common four preparation requests required")
    for ordinal,(start,row)in enumerate(zip(starts,warm)):
        si=next(i for i,e in enumerate(journal)if e is start)
        ei=next(i for i,e in enumerate(journal)if e is row)
        if(not max(preps)<si<ei<begin or row.get("ordinal")!=ordinal
           or start.get("scored")is not False or row.get("scored")is not False
           or start.get("descriptor")!=descriptors[ordinal]or row.get("descriptor")!=descriptors[ordinal]
           or(ordinal and si<=next(i for i,e in enumerate(journal)if e is warm[ordinal-1]))):
            raise ValueError("two ordered full target warmups before timer required")
        m=row.get("metrics",{});elapsed=row.get("elapsed_seconds")
        if(m.get("completion_tokens")!=1024 or m.get("usage",{}).get("prompt_tokens")!=32768
           or m.get("finish_reason")!="length"or type(m.get("request_id"))is not str or not m["request_id"]
           or type(elapsed)not in(int,float)or not 0<elapsed<1800):
            raise ValueError("actual full1024 natural timing/transport warm proof required")
        ids.append(m["request_id"]);seconds+=elapsed
    measured=[r.get("metrics",{}).get("request_id")for r in unit["results"]]
    if(len(set(ids))!=count or set(ids).intersection(measured)
       or unit.get("r39_target_warmup_seconds")!=seconds):
        raise ValueError("warm identities/extra latency/measurement exclusion differs")
    return {"actual_target_warmup_count":count,"warm_request_ids":ids,"extra_target_warmup_seconds":seconds,
        "common_cache_preparations":4,"extra_warm_latency_excluded_from_measured_unit_but_recorded":True,
        "scope":"Explicit one-variable protocol contrast; no algorithm change or native speed acceptance."}

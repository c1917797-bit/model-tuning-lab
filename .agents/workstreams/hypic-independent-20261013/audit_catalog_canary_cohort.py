"""Strict bounded17 diagnostic cohort audit, never full quality acceptance."""
import hashlib
from independent_catalog_quality_canary import catalog_canary_plan
def audit_canary_cohort(unit,journal,rows):
    plan=catalog_canary_plan(rows)
    if unit.get("requests")!=17 or unit.get("successful")!=17 or unit.get("full_quality")is not False or unit.get("initial_indexes")!=list(plan["initial_indexes"]):
        raise ValueError("exact bounded17 diagnostic unit required")
    results=unit.get("results",[])
    if len(results)!=17:raise ValueError("complete17 responses required")
    selections=[e for e in journal if e.get("event")=="catalog-canary-rebuild-selected"]
    if len(selections)!=1:raise ValueError("exact rebuild selection required")
    selected=selections[0].get("index")
    if selected not in plan["rebuild_candidates"] or selections[0].get("segment_sha256")!=rows[selected]["segment"]["tokens_sha256"] or selections[0].get("scored")is not False:
        raise ValueError("frozen rebuild selection mismatch")
    expected=[list(x) for x in plan["batches"]]+[[selected]]
    cohorts={};private_ids=set()
    for r in results:
        phase=r.get("phase");index=r.get("index")
        if type(phase)is not int or phase not in range(3) or type(index)is not int or index not in expected[phase] or (phase,index) in cohorts:
            raise ValueError("complete unique frozen phase/sample inventory required")
        row=rows[index];text=r.get("response_text");rid=r.get("request_id")
        if r.get("ok")is not True or r.get("attempts")!=1 or r.get("retries")!=0 or r.get("sample_id")!=row["sample_id"] or r.get("segment_sha256")!=row["segment"]["tokens_sha256"]:
            raise ValueError("response identity/attempt/segment mismatch")
        if not isinstance(rid,str) or not rid or rid in private_ids or not isinstance(text,str) or r.get("response_sha256")!=hashlib.sha256(text.encode()).hexdigest():
            raise ValueError("unique request and exact output hash required")
        count=r.get("completion_tokens")
        if type(count)is not int or not 0<=count<=1024 or r.get("finish_reason")not in ("stop","length"):
            raise ValueError("naturalEOS/max1024 output evidence required")
        cohorts[(phase,index)]=r;private_ids.add(rid)
    if set(cohorts)!={(p,i) for p in range(3) for i in expected[p]}:raise ValueError("missing frozen cohort")
    phase=-1;producers=[];responses=set();producer_ids=set();selection_seen=False
    for e in journal:
        kind=e.get("event")
        if not isinstance(kind,str) or not kind.startswith("catalog-canary-"):continue
        if e.get("scored")is not False:raise ValueError("diagnostic request falsely scored")
        if kind=="catalog-canary-rebuild-selected":
            if phase!=1 or producers!=expected[1] or responses!=set(expected[1]):raise ValueError("rebuild selected before second batch completed")
            selection_seen=True;continue
        if kind=="catalog-canary-phase-start":
            nextphase=e.get("phase")
            if nextphase!=phase+1 or nextphase not in range(3) or e.get("indexes")!=expected[nextphase]:
                raise ValueError("frozen phase order mismatch")
            if phase>=0 and (producers!=expected[phase] or responses!=set(expected[phase])):raise ValueError("incomplete prior phase")
            if nextphase==2 and not selection_seen:raise ValueError("selection must precede rebuild")
            phase=nextphase;producers=[];responses=set();continue
        if phase<0 or e.get("phase")!=phase:raise ValueError("request outside current phase")
        index=e.get("index")
        if kind=="catalog-canary-producer":
            if len(producers)>=len(expected[phase]) or index!=expected[phase][len(producers)] or responses:raise ValueError("producer order mismatch")
            r=e.get("response",{});rid=r.get("id");usage=r.get("usage",{});choices=r.get("choices",[])
            if not isinstance(rid,str) or not rid or rid in producer_ids or rid in private_ids or usage.get("prompt_tokens")!=rows[index]["segment"]["end"]-rows[index]["segment"]["start"] or type(usage.get("completion_tokens"))is not int or not 0<=usage["completion_tokens"]<=1 or len(choices)!=1 or choices[0].get("finish_reason")not in ("stop","length"):
                raise ValueError("unique bounded public producer response required")
            if e.get("segment_sha256")!=rows[index]["segment"]["tokens_sha256"]:raise ValueError("producer segment mismatch")
            producers.append(index);producer_ids.add(rid)
        elif kind=="catalog-canary-response":
            if producers!=expected[phase] or index in responses or index not in expected[phase]:raise ValueError("private response before complete batch or duplicate")
            actual={k:v for k,v in e.items() if k not in ("event","scored")}
            if actual!=cohorts[(phase,index)]:raise ValueError("journal/unit response drift")
            responses.add(index)
        else:raise ValueError("unknown catalog diagnostic event")
    if phase!=2 or producers!=expected[2] or responses!=set(expected[2]) or len(producer_ids)!=17:
        raise ValueError("incomplete terminal diagnostic cohort")
    initial=cohorts[(0,selected)];rebuilt=cohorts[(2,selected)]
    return {"accepted_canary_cohort":True,"private_responses":17,"unscored_producers":17,
            "rebuild_index":selected,"initial_api":initial["request_id"],"rebuild_api":rebuilt["request_id"],
            "segment_sha256":rows[selected]["segment"]["tokens_sha256"],
            "scope":"frozen diagnostic cohort/response journal only; source/hot-generation/eviction/physical/release separate; not127x3"}

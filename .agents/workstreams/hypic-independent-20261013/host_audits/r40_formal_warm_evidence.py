"""Independent full40 warmup transport, order, identity and cost accounting."""
import math
from host_audits.r39_target_warmups import warm_descriptors
SEQUENCE=[("pic-producer",0),("pic-producer",1),("native-prefix",0),("native-prefix",1)]
def _metrics(m):
    if(type(m)is not dict or m.get("completion_tokens")!=1024 or m.get("usage",{}).get("prompt_tokens")!=32768
       or m.get("finish_reason")!="length"or type(m.get("request_id"))is not str or not m["request_id"]):
        raise ValueError("full32768/fixed1024 actual transport required")
    ts=[m.get(k)for k in("started","first_content","ended")]
    if any(type(v)not in(int,float)or not math.isfinite(v)for v in ts)or not ts[0]<=ts[1]<=ts[2]:
        raise ValueError("finite ordered stream times required")
    return ts
def audit_warmups(journal,unit,contract):
    desc=warm_descriptors(contract["formal_token_artifact"])
    if contract.get("r40_warm_descriptors")!=desc or unit.get("r40_warm_descriptors")!=desc:
        raise ValueError("original input and frozen warm descriptors differ")
    names=[e.get("event")for e in journal]
    if names.count("r40-begin")!=1 or names.count("r40-end")!=1 or "r40-target-warmup-failed"in names:
        raise ValueError("single successful complete lifecycle required")
    bi=names.index("r40-begin");ei=names.index("r40-end");begin=journal[bi];end=journal[ei]
    protocol={"requests":40,"concurrency":16,"output_tokens":1024,"common_cache_preparations":4,"target_warmups":2,"retries":0}
    if(begin.get("protocol")!=protocol or begin.get("scored")is not False or end.get("scored")is not False
       or end.get("valid")is not True or end.get("requests")!=40 or not bi<ei):
        raise ValueError("actual full40 ruler differs")
    prep=[(i,e)for i,e in enumerate(journal)if e.get("event")=="warmup"]
    warm=[(i,e)for i,e in enumerate(journal)if e.get("event")=="r40-target-warmup"]
    starts=[(i,e)for i,e in enumerate(journal)if e.get("event")=="r40-target-warmup-begin"]
    measured=[(i,e)for i,e in enumerate(journal)if e.get("event")=="measured-response"]
    if([(e.get("kind"),e.get("ordinal"))for _,e in prep]!=SEQUENCE
       or any(e.get("scored")is not False for _,e in prep)
       or len(warm)!=2 or len(starts)!=2 or len(measured)!=40):
        raise ValueError("four preps/two target warmups/full40 actual denominator required")
    seconds=0.;warm_ids=[]
    for ordinal,((si,s),(wi,row))in enumerate(zip(starts,warm)):
        if(not prep[-1][0]<si<wi<bi or ordinal and si<=warm[ordinal-1][0]
           or row.get("ordinal")!=ordinal or s.get("descriptor")!=desc[ordinal]or row.get("descriptor")!=desc[ordinal]
           or s.get("scored")is not False or row.get("scored")is not False):
            raise ValueError("ordered two targets after4preps before measured work required")
        _metrics(row.get("metrics",{}));elapsed=row.get("elapsed_seconds")
        if type(elapsed)not in(int,float)or not math.isfinite(elapsed)or not 0<elapsed<1800:
            raise ValueError("finite positive extra warm cost required")
        warm_ids.append(row["metrics"]["request_id"]);seconds+=elapsed
    if unit.get("r40_target_warmups")!=[{k:v for k,v in e.items()if k not in("event","scored")}for _,e in warm]:
        raise ValueError("warm journal/unit records differ")
    if(unit.get("valid")is not True or unit.get("requests")!=40 or unit.get("concurrency")!=16 or unit.get("retries")!=0
       or unit.get("input_sha256")!=contract["formal_token_artifact"]["sha256"]):
        raise ValueError("original full40 unit identity differs")
    rows=unit["results"]
    if len(rows)!=40 or [r.get("index")for r in rows]!=list(range(40))or any(r.get("ok")is not True for r in rows):
        raise ValueError("actual full40 valid ordered results required")
    if any(not bi<i<ei or e.get("scored")is not True for i,e in measured):
        raise ValueError("measured events cross target warm lifecycle")
    indexed=sorted([{k:v for k,v in e.items()if k not in("event","scored")}for _,e in measured],key=lambda r:r["index"])
    if indexed!=rows:raise ValueError("full actual measured journal/unit records differ")
    times=[_metrics(r["metrics"])for r in rows];ids=[r["metrics"]["request_id"]for r in rows]
    if len(set(ids))!=40 or len(set(warm_ids))!=2 or set(ids)&set(warm_ids):raise ValueError("warm/measured IDs overlap or duplicate")
    if not begin.get("started",float("inf"))<=min(x[0]for x in times)or not max(x[2]for x in times)<=end.get("ended",float("-inf")):
        raise ValueError("actual timing region includes warm or crosses end")
    if max(e["metrics"]["ended"]for _,e in warm)>begin["started"]:raise ValueError("warm timing crosses measured begin")
    span=max(x[2]for x in times)-min(x[0]for x in times)
    if(span<=0 or unit.get("r40_target_warmup_seconds")!=seconds or unit.get("r40_measured_makespan_seconds")!=span
       or unit.get("r40_measured_plus_target_warmup_seconds")!=span+seconds):
        raise ValueError("reported extra and combined time arithmetic differs")
    return {"actual_target_warmups":2,"common_cache_preparations":4,"warm_request_ids":warm_ids,
        "measured_request_ids":ids,"extra_target_warmup_seconds":seconds,"measured_makespan_seconds":span,
        "measured_plus_target_warmup_seconds":span+seconds,"formal40_transport_lifecycle_valid":True,
        "scope":"One matched ruler arm; not paired native speed/fullquality/lifecycle acceptance."}

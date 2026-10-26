"""HOST-only full40 ruler: four original preparations, then two full targets."""
import math,time
from independent_formal_workload import run_formal_workload as original_unit
from host_audits.r39_target_warmups import prepare_warmups,check_metrics

SEQUENCE=(("pic-producer",0),("pic-producer",1),("native-prefix",0),("native-prefix",1))
def metric_time(m):
    check_metrics(m)
    vals=[m.get(k) for k in ("started","first_content","ended")]
    if any(type(x)not in(int,float)or not math.isfinite(x)for x in vals)or not vals[0]<=vals[1]<=vals[2]:
        raise ValueError("finite ordered actual stream timings required")
    return vals
def run_unit(spec,*,send_warmup,send_measured,guard,record,require_material_ready,
             expected_warm_descriptors):
    warm=prepare_warmups(spec);desc=[{k:v for k,v in x.items()if k!="payload"}for x in warm]
    if desc!=expected_warm_descriptors:raise ValueError("exact frozen warm payloads required")
    seen=[];done=[];began=None;warm_seconds=0.
    def observe(event):
        nonlocal began,warm_seconds
        record(event)
        if event.get("event")!="warmup":return
        seen.append((event.get("kind"),event.get("ordinal")))
        if tuple(seen)!=SEQUENCE[:len(seen)]or len(seen)>4:raise ValueError("original four preparations required")
        if len(seen)!=4:return
        if began is not None:raise ValueError("single warmup lifecycle required")
        for item in warm:
            ordinal=item["ordinal"];guard()
            record({"event":"r40-target-warmup-begin","scored":False,"descriptor":desc[ordinal]})
            started=time.monotonic()
            try:
                m=send_measured(item["payload"]);guard();metric_time(m)
                if m["request_id"]in[x["metrics"]["request_id"]for x in done]:
                    raise ValueError("duplicate actual target warm identity")
            except Exception as error:
                record({"event":"r40-target-warmup-failed","scored":False,"ordinal":ordinal,
                        "error":{"type":type(error).__name__,"message":str(error)}})
                raise
            elapsed=time.monotonic()-started
            if not 0<elapsed<1800:raise ValueError("bounded actual target warm duration required")
            row={"ordinal":ordinal,"descriptor":desc[ordinal],"metrics":m,"elapsed_seconds":elapsed}
            done.append(row);warm_seconds+=elapsed
            record(dict(row,event="r40-target-warmup",scored=False))
        began=time.monotonic()
        record({"event":"r40-begin","scored":False,"started":began,
                "protocol":{"requests":40,"concurrency":16,"output_tokens":1024,"common_cache_preparations":4,"target_warmups":2,"retries":0}})
    result=original_unit(spec,send_warmup=send_warmup,send_measured=send_measured,
        guard=guard,record=observe,require_material_ready=require_material_ready)
    ended=time.monotonic()
    record({"event":"r40-end","scored":False,"ended":ended,"valid":result.get("valid"),"requests":len(result.get("results",[]))})
    if tuple(seen)!=SEQUENCE or len(done)!=2 or began is None:raise ValueError("actual complete warmup lifecycle absent")
    rows=result.get("results",[]);ids=[r.get("metrics",{}).get("request_id")for r in rows if r.get("ok")]
    if set(ids).intersection(x["metrics"]["request_id"]for x in done):raise ValueError("warm requests overlap measured identities")
    span=None
    if result.get("valid")is True:
        if len(rows)!=40 or len(set(ids))!=40:raise ValueError("retained actual full40 required")
        times=[metric_time(r["metrics"])for r in rows]
        if min(x[0]for x in times)<began or max(x[2]for x in times)>ended:
            raise ValueError("actual measured interval crosses warmups")
        span=max(x[2]for x in times)-min(x[0]for x in times)
    return dict(result,r40_target_warmups=done,r40_target_warmup_seconds=warm_seconds,
        r40_warm_descriptors=desc,r40_measured_makespan_seconds=span,
        r40_measured_plus_target_warmup_seconds=span+warm_seconds if span is not None else None,
        scope="Actual retained full40/c16/fixed1024, common4cacheprep+2fulltargetwarm. Extra warm cost reported; no native gain from one arm.")

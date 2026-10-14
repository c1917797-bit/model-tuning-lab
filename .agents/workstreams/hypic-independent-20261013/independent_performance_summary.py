"""Fail-closed formal phase summary, separate from source/physical audit."""
import math
import statistics

def percentile(values,p):
    xs=sorted(values)
    if not xs:raise ValueError("empty percentile")
    return xs[max(0,math.ceil(p*len(xs))-1)]

def summarize_phase(records):
    records=tuple(records)
    if len(records)!=40 or {x["index"] for x in records}!=set(range(40)):
        raise ValueError("full40 exact indices required")
    ids=set();ttft=[];tpot=[];tokens=0;decode_ms=0.
    for r in records:
        if r.get("ok") is not True:raise ValueError("failed request retained; phase invalid")
        m=r["metrics"];rid=m.get("request_id")
        if not isinstance(rid,str) or not rid or rid in ids:
            raise ValueError("unique service IDs required")
        ids.add(rid)
        if m.get("completion_tokens")!=1024 or m.get("usage",{}).get("prompt_tokens")!=32768:
            raise ValueError("fixed input/output token protocol mismatch")
        if m.get("finish_reason")!="length" or m.get("tpot_denominator")!="completion_tokens":
            raise ValueError("fixed boundary/TPOT ruler mismatch")
        a,b=m["ttft_ms"],m["duration_ms"]
        if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in (a,b)) or not 0<=a<=b:
            raise ValueError("invalid timings")
        derived=(b-a)/1024
        if not math.isclose(derived,m["tpot_ms"],rel_tol=1e-10,abs_tol=1e-10):
            raise ValueError("TPOT does not match raw timings")
        ttft.append(a);tpot.append(derived);tokens+=1024;decode_ms+=b-a
    return {"requests":40,"unique_ids":40,"weighted_tpot_ms":decode_ms/tokens,
            "ttft_p95_ms":percentile(ttft,.95),"tpot_p95_ms":percentile(tpot,.95)}

def summarize_three_rounds(phases):
    if set(phases)!={1,2,3}:raise ValueError("all3 rounds required")
    rows=[summarize_phase(phases[i]) for i in (1,2,3)]
    values=[r["weighted_tpot_ms"] for r in rows]
    return {"rounds":rows,"weighted_tpot_median_ms":statistics.median(values),
            "weighted_tpot_min_ms":min(values),"weighted_tpot_max_ms":max(values),
            "scope":"timing protocol only; source/activation/quality/isolation audit separate"}

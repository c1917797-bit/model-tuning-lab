"""Official aggregate nativePDC counters sampled outside measured request timing."""
import json,math,re,time,urllib.request
FAMILIES={"vllm:prefix_cache_queries_total","vllm:prefix_cache_hits_total",
          "vllm:num_requests_running","vllm:num_requests_waiting","vllm:request_success_total"}
REASONS={"stop","length","abort","error","repetition"}
def parse_metrics(text):
    if not isinstance(text,str) or len(text.encode())>2097152:raise ValueError("bounded UTF8 metrics required")
    values={};success={}
    for line in text.splitlines():
        if not line or line.startswith("#"):continue
        name=line.split("{",1)[0]
        if name not in FAMILIES:continue
        m=re.fullmatch(r'([^{}]+)\{([^{}]*)\}\s+(\S+)',line)
        if not m:raise ValueError("metric syntax mismatch")
        pairs=list(re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)=("(?:\\.|[^"\\])*")',m[2]))
        if ",".join(x[0] for x in pairs)!=m[2]:raise ValueError("metric label syntax")
        labels={}
        for x in pairs:
            if x[1] in labels:raise ValueError("duplicate metric label")
            labels[x[1]]=json.loads(x[2])
        expected={"engine","model_name"}|({"finished_reason"}if name.endswith("request_success_total")else set())
        if set(labels)!=expected or labels["engine"]!="0" or labels["model_name"]!="qwen3.5":
            raise ValueError("unexpected engine/model/metric labels")
        value=float(m[3])
        if not math.isfinite(value) or value<0 or value!=int(value):raise ValueError("invalid counter/gauge")
        value=int(value)
        if "finished_reason"in labels:
            key=labels["finished_reason"]
            if key not in REASONS or key in success:raise ValueError("unexpected/duplicate finishreason")
            success[key]=value
        else:
            if name in values:raise ValueError("duplicate metric series")
            values[name]=value
    if set(success)!=REASONS or set(values)!=FAMILIES-{"vllm:request_success_total"}:
        raise ValueError("complete source-bound series required")
    return {"queries":values["vllm:prefix_cache_queries_total"],
            "hits":values["vllm:prefix_cache_hits_total"],
            "running":values["vllm:num_requests_running"],
            "waiting":values["vllm:num_requests_waiting"],"success":success}

def audit_delta(before,after):
    a=parse_metrics(before);b=parse_metrics(after)
    for x,total in ((a,4),(b,44)):
        if x["running"] or x["waiting"] or sum(x["success"].values())!=total:
            raise ValueError("exclusive4warmup/40measured boundary required")
        if any(x["success"][r] for r in ("abort","error","repetition")):
            raise ValueError("non-success request observed")
    if any(b["success"][r]<a["success"][r] for r in REASONS):
        raise ValueError("finished counter reset")
    q=b["queries"]-a["queries"];h=b["hits"]-a["hits"]
    if q<=0 or h<=0 or h>q:raise ValueError("actual measured nativePDC hits not proven")
    return {"aggregate_native_pdc_verified":True,"measured_successes":40,
            "queried_tokens":q,"cached_tokens":h,
            "scope":"aggregate actual native cache reuse among40 requests, not per-request hit coverage"}

def fetch_metrics(port):
    with urllib.request.urlopen("http://127.0.0.1:"+str(port)+"/metrics",timeout=10) as r:
        b=r.read(2097153)
    if len(b)>2097152:raise ValueError("metrics byte budget exceeded")
    return b.decode("utf-8")

def wait_boundary(expected,*,fetch,guard,clock=time.monotonic,sleep=time.sleep):
    stop=clock()+60
    while True:
        guard();raw=fetch();x=parse_metrics(raw);total=sum(x["success"].values())
        if total>expected or any(x["success"][r] for r in ("abort","error","repetition")):
            raise ValueError("unexpected request/finish at boundary")
        if total==expected and x["running"]==x["waiting"]==0:return raw
        if clock()>=stop:raise TimeoutError("native metric boundary deadline")
        sleep(1)

def observe_full40(original,args,kwargs,*,fetch,guard,save,identity):
    receipt=dict(identity);error=None
    try:
        receipt["before"]=wait_boundary(4,fetch=fetch,guard=guard)
        # The original request timers and exact40 client are unchanged.
        result=original(*args,**kwargs)
        receipt["after"]=wait_boundary(44,fetch=fetch,guard=guard)
        receipt["audit"]=audit_delta(receipt["before"],receipt["after"])
        return result
    except BaseException as exc:
        receipt["error"]={"type":type(exc).__name__,"message":str(exc)}
        raise
    finally:
        save(receipt)

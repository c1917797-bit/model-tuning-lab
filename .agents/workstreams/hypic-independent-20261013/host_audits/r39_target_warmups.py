"""HOST-only explicit target-path warmups; original R38 measured unit unchanged."""
import hashlib,json,re,time
from pathlib import Path
from independent_formal_client import completion_payload
from host_audits.r38_component_controller import run_unit as original_unit
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def prepare_warmups(spec):
    p=Path(spec["path"])
    if not p.is_absolute()or p.is_symlink()or p.stat().st_size>33554432:
        raise ValueError("bounded original artifact required")
    data=p.read_bytes()
    if hashlib.sha256(data).hexdigest()!=spec["sha256"]:raise ValueError("target warmup source input drift")
    a=json.loads(data);cases=a["requests"];prefix=a["native_prefix"];public=a["public_segment"]
    if len(cases)!=40 or [x["index"]for x in cases]!=list(range(40))or len(prefix)!=8192 or len(public)!=16384:
        raise ValueError("original full40/native8192/public16384 required")
    result=[]
    for ordinal,case in enumerate(cases[:2]):
        tokens=list(case["token_ids"]);lo=case["segment_start"];hi=case["segment_end"]
        if(len(tokens)!=32768 or type(lo)is not int or type(hi)is not int or not 8192<lo<hi<=32768
           or hi-lo!=16384 or tokens[:8192]!=prefix or tokens[lo:hi]!=public):
            raise ValueError("actual private8192 before exact public segment required")
        # Reuse an existing valid token from this frozen private suffix. Change
        # the first private token so later PDC cannot get a full private hit.
        choices=[x for x in tokens[hi:]if type(x)is int and x>=0 and x!=tokens[8192]]
        if not choices:raise ValueError("distinct existing private-tail token unavailable")
        old=tokens[8192];tokens[8192]=choices[0]
        if tokens==case["token_ids"]or tokens[:8192]!=prefix or tokens[lo:hi]!=public:
            raise ValueError("warm mutation changed original shared regions")
        payload=completion_payload(dict(case,token_ids=tokens))
        result.append({"ordinal":ordinal,"source_case_index":case["index"],
            "private_token_position":8192,"old_token":old,"replacement_token":tokens[8192],
            "payload_sha256":digest(payload),"tokens_sha256":digest(tokens),"payload":payload})
    if result[0]["payload_sha256"]==result[1]["payload_sha256"]:raise ValueError("distinct target warmups required")
    return tuple(result)
def warm_descriptors(spec):
    return [{k:v for k,v in x.items()if k!="payload"}for x in prepare_warmups(spec)]
def check_metrics(m):
    if(type(m)is not dict or m.get("completion_tokens")!=1024
       or m.get("usage",{}).get("prompt_tokens")!=32768 or m.get("finish_reason")!="length"
       or type(m.get("request_id"))is not str or not m["request_id"]):
        raise ValueError("actual target32768/fixed1024 stream required")
def run_unit(spec,*,send_warmup,send_measured,guard,record,require_material_ready,
             target_warmups,expected_warm_descriptors):
    if type(target_warmups)is not int or target_warmups not in(0,2):
        raise ValueError("single explicit target warmup count0or2 required")
    warmups=prepare_warmups(spec)
    descriptors=[{k:v for k,v in x.items()if k!="payload"}for x in warmups]
    if descriptors!=expected_warm_descriptors:raise ValueError("frozen target warmup payload identity differs")
    seen=[];completed=[];warmed=False;warm_seconds=0.
    sequence=(("pic-producer",0),("pic-producer",1),("native-prefix",0),("native-prefix",1))
    def observe(event):
        nonlocal warmed,warm_seconds
        record(event)
        if event.get("event")!="warmup":return
        seen.append((event.get("kind"),event.get("ordinal")))
        if tuple(seen)!=sequence[:len(seen)]:raise ValueError("original four preparations differ")
        if len(seen)!=4:return
        if warmed:raise ValueError("target warmup lifecycle repeated")
        warmed=True
        for item in warmups[:target_warmups]:
            guard();record({"event":"r39-target-warmup-begin","scored":False,"descriptor":descriptors[item["ordinal"]]})
            started=time.monotonic()
            try:
                metrics=send_measured(item["payload"]);guard();check_metrics(metrics)
                if metrics["request_id"]in[x["metrics"]["request_id"]for x in completed]:
                    raise ValueError("duplicate actual warm request identity")
            except Exception as error:
                record({"event":"r39-target-warmup-failed","scored":False,"ordinal":item["ordinal"],
                        "error":{"type":type(error).__name__,"message":str(error)}})
                raise
            elapsed=time.monotonic()-started
            if not 0<elapsed<1800:raise ValueError("bounded actual warmup duration required")
            warm_seconds+=elapsed
            row={"ordinal":item["ordinal"],"descriptor":descriptors[item["ordinal"]],
                 "metrics":metrics,"elapsed_seconds":elapsed}
            record(dict(row,event="r39-target-warmup",scored=False));completed.append(row)
    result=original_unit(spec,send_warmup=send_warmup,send_measured=send_measured,guard=guard,
        record=observe,require_material_ready=require_material_ready)
    if not warmed or tuple(seen)!=sequence or len(completed)!=target_warmups:
        raise ValueError("complete explicit target warmup lifecycle required")
    measured={x["metrics"]["request_id"]for x in result["results"]if x["ok"]}
    if measured.intersection(x["metrics"]["request_id"]for x in completed):
        raise ValueError("warm requests cannot count in measured denominator")
    return dict(result,r39_target_warmup_count=target_warmups,r39_target_warmups=completed,
                r39_target_warmup_seconds=warm_seconds,r39_warm_descriptors=descriptors,
                scope="Single warmup-count protocol contrast; original measured16/c16/fixed1024 preserved. Extra target warmup time explicitly reported, no algorithm/native speed claim.")

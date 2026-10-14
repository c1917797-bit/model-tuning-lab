"""Independent warmup protocol; caller records unscored responses separately."""

def build_warmups(artifact):
    a=tuple(artifact["native_prefix"]);b=tuple(artifact["public_segment"])
    if len(a)!=8192 or len(b)!=16384 or len(artifact["requests"])!=40:
        raise ValueError("frozen full40 artifact required")
    out=[]
    # Two B+distinct256-tail observations are unscored, not40 measured requests.
    # Caller must enable the independently verified public-prefix capture path.
    for i in range(2):
        case=artifact["requests"][i];start=case["segment_end"]
        tail=tuple(case["token_ids"][start:start+256])
        if len(tail)!=256:raise ValueError("PIC warmup tail unavailable")
        out.append({"kind":"pic-producer","ordinal":i,"payload":{
            "model":"qwen3.5","prompt":list(b+tail),"temperature":0,"seed":0,
            "max_tokens":1,"ignore_eos":True}})
    # Different private tails avoid mistaking a fully repeated warmup for A hit.
    for i in range(2):
        case=artifact["requests"][i];start=case["segment_end"]
        tail=tuple(case["token_ids"][start:start+256])
        if len(tail)!=256:raise ValueError("native warmup tail unavailable")
        out.append({"kind":"native-prefix","ordinal":i,"payload":{
            "model":"qwen3.5","prompt":list(a+tail),"temperature":0,"seed":0,
            "max_tokens":1,"ignore_eos":True}})
    return tuple(out)

def execute_warmups(warmups,*,send,guard,record,require_material_ready):
    if tuple(x["kind"] for x in warmups)!=("pic-producer","pic-producer",
                                         "native-prefix","native-prefix"):
        raise ValueError("exact separated warmup sequence required")
    for w in warmups:
        guard()
        result=send(w["payload"])
        guard()
        record({"event":"warmup","kind":w["kind"],"ordinal":w["ordinal"],
                "scored":False,"response":result})
        if w["kind"]=="pic-producer" and w["ordinal"]==1:
            # Caller must prove all4rank48/16 actual materials; not justHTTP200.
            require_material_ready()

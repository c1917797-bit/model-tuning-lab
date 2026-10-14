"""Exact three-request mechanism probe from the frozen full40 token artifact."""
import hashlib,json
from pathlib import Path

def native_prefix_warmup(spec):
    # Validate same immutable artifact and private geometry first.
    load_formal_canary(spec)
    raw=Path(spec["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=spec["sha256"]:raise ValueError("warmup artifact drift")
    d=json.loads(raw);tokens=list(d["native_prefix"])+list(d["requests"][0]["token_ids"][-256:])
    return {"model":"qwen3.5","prompt":tokens,"temperature":0,"seed":0,
            "max_tokens":1,"ignore_eos":True}

def load_formal_canary(spec):
    if not {"path","sha256"}<=set(spec) or set(spec)-{"path","sha256","public_tail_tokens"}:
        raise ValueError("exact artifact path/hash and optional producer tail required")
    tail_length=spec.get("public_tail_tokens",0)
    if type(tail_length) is not int or tail_length not in (0,256):
        raise ValueError("producer tail must be0 or256")
    path=Path(spec["path"])
    if not path.is_absolute() or path.is_symlink() or path.stat().st_size>33554432:
        raise ValueError("bounded absolute token artifact required")
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=spec["sha256"]:raise ValueError("formal artifact drift")
    d=json.loads(data);reqs=d["requests"];public=d["public_segment"]
    if len(reqs)!=40 or len(public)!=16384 or len(d["native_prefix"])!=8192:
        raise ValueError("formal artifact denominator mismatch")
    producer=list(public)
    if tail_length:
        first=reqs[0];end=first["segment_end"]
        tail=first["token_ids"][end:end+tail_length]
        if len(tail)!=tail_length:raise ValueError("producer tail unavailable")
        producer+=tail
    prompts=[producer]
    for i in (0,1):
        r=reqs[i];s=8192+1024+i*512
        if r["index"]!=i or r["segment_start"]!=s or r["segment_end"]!=s+16384:
            raise ValueError("formal private segment geometry mismatch")
        t=r["token_ids"]
        if len(t)!=32768 or t[:8192]!=d["native_prefix"] or t[s:s+16384]!=public:
            raise ValueError("formal prompt token identity mismatch")
        prompts.append(t)
    return [{"model":"qwen3.5","prompt":t,"temperature":0,"seed":0,
             "max_tokens":1 if i==0 else 1024,"ignore_eos":True}
            for i,t in enumerate(prompts)]

"""Exact three-request mechanism probe from the frozen full40 token artifact."""
import hashlib,json
from pathlib import Path

def load_formal_canary(spec):
    if set(spec)!={"path","sha256"}:raise ValueError("exact artifact path/hash required")
    path=Path(spec["path"])
    if not path.is_absolute() or path.is_symlink() or path.stat().st_size>33554432:
        raise ValueError("bounded absolute token artifact required")
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=spec["sha256"]:raise ValueError("formal artifact drift")
    d=json.loads(data);reqs=d["requests"];public=d["public_segment"]
    if len(reqs)!=40 or len(public)!=16384 or len(d["native_prefix"])!=8192:
        raise ValueError("formal artifact denominator mismatch")
    prompts=[public]
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

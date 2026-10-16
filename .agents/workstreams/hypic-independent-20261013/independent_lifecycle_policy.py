"""Pure explicit lifecycle policy, source binding and bounded transport controls."""
import hashlib
from pathlib import Path

def lifecycle_mode(c):
    stage=c.get("lifecycle_stage")
    if stage not in ("disabled","enabled","uninstalled"):raise ValueError("explicit lifecycle stage required")
    if any(type(c.get(k,False))is not bool or c.get(k,False)for k in ("formal_quality","formal_quality_canary","formal_performance")):
        raise ValueError("lifecycle cannot substitute formal quality/performance")
    if c.get("enable_prefix_caching")is not False or c.get("enable_thinking")is not False or c.get("enforce_eager")is not True or c.get("completion")is not True:
        raise ValueError("explicit noPDC/nonthinking/eager completion lifecycle control required")
    if c.get("lifecycle_private_output_tokens")!=64 or c.get("max_output_tokens")!=64 or not c.get("formal_token_artifact"):
        raise ValueError("frozen bounded64 private lifecycle artifact required")
    diagnostic=c.get("cache_diagnostic")
    if stage=="uninstalled":
        if diagnostic is not None or not c.get("baseline_host_source_sha256"):raise ValueError("uninstalled stage requires no package startup")
    elif type(diagnostic)is not dict or not diagnostic.get("compact_manifest") or not diagnostic.get("source_sha256"):
        raise ValueError("enabled/disabled lifecycle requires same bound package")
    return stage,stage=="enabled"

def validate_lifecycle_sources(c,here):
    diagnostic=c.get("cache_diagnostic")
    sources=diagnostic["source_sha256"]if diagnostic else c["baseline_host_source_sha256"]
    here=Path(here).resolve()
    for name,digest in sources.items():
        original=here/name;p=original.resolve()
        if original.is_symlink() or not p.is_relative_to(here) or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
            raise ValueError("lifecycle source drift: "+name)
    return len(sources)

def lifecycle_payloads(artifact):
    from independent_formal_canary import load_formal_canary
    payloads=load_formal_canary(artifact)
    if len(payloads)!=3:raise ValueError("exact public/two private lifecycle requests required")
    return [dict(p,max_tokens=1 if i==0 else 64)for i,p in enumerate(payloads)]

def semantic_payload():
    return {"model":"qwen3.5","messages":[{"role":"user","content":"Calculate 2 + 2. Reply with only the integer."}],
        "temperature":0,"seed":0,"max_tokens":32,"chat_template_kwargs":{"enable_thinking":False}}

def check_semantic(response):
    choices=response.get("choices",[]);usage=response.get("usage",{})
    if not response.get("id") or len(choices)!=1 or choices[0].get("message",{}).get("content","").strip().rstrip(".")!="4":
        raise ValueError("native semantic lifecycle control failed")
    n=usage.get("completion_tokens")
    if type(n)is not int or not 1<=n<=32:raise ValueError("bounded semantic output usage required")
    return True

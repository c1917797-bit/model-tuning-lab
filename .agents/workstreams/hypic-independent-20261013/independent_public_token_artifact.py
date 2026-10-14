"""Hash-bound public token selection from an external frozen workload."""
import hashlib
import json
from pathlib import Path

def public_tokens_from_artifact(spec):
    if set(spec)!={"path","sha256","length"}:
        raise ValueError("exact token artifact path/hash/length required")
    path=Path(spec["path"])
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError("absolute regular token artifact required")
    if path.stat().st_size>33554432:raise ValueError("token artifact too large")
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=spec["sha256"]:
        raise ValueError("public token artifact drift")
    payload=json.loads(data);tokens=payload["public_segment"]
    if type(spec["length"]) is not int or spec["length"]!=16384 or len(tokens)!=16384:
        raise ValueError("formal public length required")
    if any(type(x) is not int or x<0 for x in tokens):
        raise ValueError("invalid public token IDs")
    return tuple(tokens)

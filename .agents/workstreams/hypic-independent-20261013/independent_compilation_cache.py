"""Bounded official compiled-cache storage; never contains prompt/KV material."""
import hashlib,json
from pathlib import Path
BASE=Path("/cache/cch/hypic-independent-20261013")
MAX_FILES=40000
MAX_BYTES=2147483648
def validate_cache_spec(contract):
    spec=contract.get("compiled_cache")
    if not isinstance(spec,dict) or set(spec)!={"mode","path"} or spec["mode"] not in ("seed","reuse"):
        raise ValueError("exact seed/reuse compiled-cache specification required")
    if contract.get("formal_performance") or contract.get("formal_quality"):
        raise ValueError("compiled-cache diagnostic is not formal acceptance")
    p=Path(spec["path"])
    if not p.is_absolute() or ".." in p.parts or not p.is_relative_to(BASE) or p.name!="compiled-cache":
        raise ValueError("owned compiled-cache path required")
    for q in [p,*p.parents]:
        if q.is_symlink():raise ValueError("compiled-cache symlink rejected")
    return dict(spec)
def inventory(path,*,max_files=MAX_FILES,max_bytes=MAX_BYTES):
    root=Path(path)
    if root.is_symlink() or not root.is_dir():raise ValueError("real compiled-cache directory required")
    files=[];total=0
    for p in sorted(root.rglob("*")):
        if p.is_symlink():raise ValueError("compiled-cache child symlink rejected")
        if not p.is_file():continue
        size=p.stat().st_size;total+=size
        if len(files)>=max_files or total>max_bytes:raise ValueError("compiled-cache storage ceiling exceeded")
        h=hashlib.sha256()
        with p.open("rb") as f:
            for block in iter(lambda:f.read(1048576),b""):h.update(block)
        files.append({"path":str(p.relative_to(root)),"size":size,"sha256":h.hexdigest()})
    canonical=json.dumps(files,sort_keys=True,separators=(",",":")).encode()
    return {"files":files,"file_count":len(files),"bytes":total,"sha256":hashlib.sha256(canonical).hexdigest()}
def prepare_cache(contract,raw):
    spec=validate_cache_spec(contract);path=Path(spec["path"]);raw=Path(raw)
    if spec["mode"]=="seed":
        if path!=raw/"compiled-cache" or path.exists():raise ValueError("fresh seed must belong to new attempt")
        path.mkdir(exist_ok=False)
    else:
        if path==raw/"compiled-cache":raise ValueError("reuse must name a separate audited seed attempt")
        seed=path.parent
        result=json.loads((seed/"result.json").read_text())
        if not result.get("valid") or not result.get("release",{}).get("removed") or not result["release"].get("port_free"):
            raise ValueError("only terminal valid and released seed may be reused")
        receipt=json.loads((seed/"compiled-cache-inventory.json").read_text())
        bound=json.loads((seed/"compiled-cache-identity.json").read_text())
        expected=identity(contract)
        if bound!=expected:raise ValueError("compiled-cache seed identity drift")
        actual=inventory(path)
        if actual!=receipt or not actual["file_count"]:raise ValueError("compiled-cache seed missing or changed")
    return path
def identity(contract):
    return {"image":contract["image"],"model_config_sha256":contract["model_config_sha256"],
        "source_sha256":contract["cache_diagnostic"]["source_sha256"],
        "tp":contract["tp"],"physical_npus":contract["physical_npus"],
        "scope":"official compiled binaries only; no prompt/KV/public-state transfer"}

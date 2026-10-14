"""External hash-bound catalog; raw quality tokens never belong in source Git."""
import hashlib,json
from pathlib import Path
from independent_segment_catalog import SegmentCatalog

def catalog_from_artifact(spec,*,boundary_tokens=8):
    if set(spec)!={"path","sha256","segments"}:
        raise ValueError("exact catalog path/hash/count required")
    count=spec["segments"]
    if type(count) is not int or not 1<=count<=128:
        raise ValueError("bounded catalog count required")
    path=Path(spec["path"])
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError("absolute regular catalog required")
    with path.open("rb") as stream:
        raw=stream.read(33554433)
    if len(raw)>33554432:raise ValueError("catalog too large")
    if hashlib.sha256(raw).hexdigest()!=spec["sha256"]:
        raise ValueError("catalog source drift")
    payload=json.loads(raw)
    if set(payload)!={"schema","public_segments"} or payload["schema"]!="hypic-public-catalog/v1":
        raise ValueError("catalog schema mismatch")
    segments=payload["public_segments"]
    if not isinstance(segments,list) or len(segments)!=count:
        raise ValueError("catalog count mismatch")
    if any(not isinstance(x,list) or len(x)>32768 for x in segments):
        raise ValueError("bounded token arrays required")
    catalog=SegmentCatalog(segments,boundary_tokens=boundary_tokens)
    return tuple(catalog.entries.values())

def resolve_catalog_config(config):
    config=dict(config)
    if "public_catalog_artifact" not in config:return config
    if any(x in config for x in ("public_segments","public_tokens","public_token_recipe","public_token_artifact")):
        raise ValueError("ambiguous catalog token configuration")
    config["public_segments"]=catalog_from_artifact(
        config.pop("public_catalog_artifact"),boundary_tokens=config.get("boundary_tokens",8))
    return config

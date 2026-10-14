"""Hash-bound quality unit and explicit unscored material producers."""
import hashlib,json
from pathlib import Path
from independent_segment_catalog import SegmentCatalog
from independent_quality_client import run_quality
from independent_quality_ruler import load_ruler

def read_bound(spec):
    if set(spec)!={"path","sha256"}:raise ValueError("exact artifact path/hash required")
    p=Path(spec["path"])
    if not p.is_absolute() or p.is_symlink() or not p.is_file():raise ValueError("regular absolute artifact required")
    with p.open("rb") as stream:raw=stream.read(33554433)
    if len(raw)>33554432 or hashlib.sha256(raw).hexdigest()!=spec["sha256"]:
        raise ValueError("quality artifact bound/hash mismatch")
    return json.loads(raw)

def run_quality_workload(spec,*,send,guard,record,require_material_ready):
    if set(spec)!={"inputs","catalog","ruler_path","batch_samples"}:
        raise ValueError("frozen quality inputs/catalog/ruler/batch required")
    inputs=read_bound(spec["inputs"]);catalog=read_bound(spec["catalog"])
    if inputs.get("schema")!="hypic-quality-inputs/v1" or catalog.get("schema")!="hypic-public-catalog/v1":
        raise ValueError("quality artifact schema mismatch")
    if inputs["generation"]!={"max_tokens":1024,"temperature":0,"seed":0,
        "ignore_eos":False,"enable_thinking":False} or inputs["repetitions"]!=3:
        raise ValueError("quality generation drift")
    stage=SegmentCatalog(catalog["public_segments"])
    ruler=load_ruler(spec["ruler_path"])
    rows=inputs["requests"]
    for row in rows:
        s=row["segment"];tokens=stage.tokens(s["tokens_sha256"])
        if tuple(row["token_ids"][s["start"]:s["end"]])!=tokens:
            raise ValueError("quality selected segment membership mismatch")
    def prepare(unit):
        for digest in unit["producer_digests"]:
            guard();tokens=stage.tokens(digest)
            response=send({"model":"qwen3.5","prompt":list(tokens),"temperature":0,
                "seed":0,"max_tokens":1,"ignore_eos":False,"stream":False})
            guard()
            record({"event":"quality-public-producer","scored":False,
                "repetition":unit["repetition"],"batch":unit["batch"],
                "segment_sha256":digest,"response":response})
            if not response.get("id") or response.get("usage",{}).get("prompt_tokens")!=len(tokens):
                raise ValueError("producer identity/token usage missing")
            require_material_ready(digest)
    def scored(item):record(dict(item,event="quality-scored-response",scored=True))
    return run_quality(rows,send=send,prepare=prepare,score=ruler["score_case"],
        guard=guard,record=scored,batch_samples=spec["batch_samples"])

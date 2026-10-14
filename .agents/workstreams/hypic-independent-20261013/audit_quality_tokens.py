"""Independent full-catalog token membership check; no inference."""
import argparse,json,hashlib
from pathlib import Path
from independent_segment_catalog import SegmentCatalog

def audit(root):
    receipt=json.loads((root/"receipt.json").read_text())
    for name,digest in receipt["files"].items():
        if name not in ("inputs.json","catalog.json"):raise ValueError("unexpected artifact")
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError("artifact drift")
    inputs=json.loads((root/"inputs.json").read_text())
    catalog=json.loads((root/"catalog.json").read_text())
    rows=inputs["requests"]
    if len(rows)!=127 or [x["index"] for x in rows]!=list(range(127)):
        raise ValueError("complete127 ordered denominator required")
    if len({x["sample_id"] for x in rows})!=127:raise ValueError("duplicate sample")
    if inputs["generation"]!={"max_tokens":1024,"temperature":0,"seed":0,
        "ignore_eos":False,"enable_thinking":False} or inputs["repetitions"]!=3:
        raise ValueError("generation ruler drift")
    stage=SegmentCatalog(catalog["public_segments"])
    for row in rows:
        selected=stage.select_one(row["token_ids"])
        expected=row["segment"]
        if (selected.start,selected.end,selected.tokens_sha256)!=(expected["start"],expected["end"],expected["tokens_sha256"]):
            raise ValueError("selected segment mismatch")
        if len(row["token_ids"])+1024>41984:raise ValueError("capacity exceeded")
    return {"samples":127,"unique_segments":len(stage.entries),"selection_errors":0,
        "files_sha256":receipt["files"],"scope":"CPU artifact membership only, not tokenizer replay or NPU quality acceptance"}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True)
    print(json.dumps(audit(p.parse_args().root)),flush=True)

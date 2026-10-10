"""Independent raw packed-frame comparison. No candidate import/Torch/model permission.
An actual owned numerical producer is still required; this is not a fake fixture PASS.
"""
import hashlib
import json
import math
from pathlib import Path
import fast_oracle as oracle

FIELDS = ("key_codes","key_scales","key_minima","value_codes","value_scales","value_minima","key_residual","value_residual")
IDENTITIES = ("before_bind","actual_format","post_rope","slot_owner","pending_ticket","after_read_completion")

def ref_read(ref, maximum):
    if type(ref) is not dict or set(ref) != {"path","bytes","sha256"}:
        raise ValueError("exact physical three-field raw Ref")
    if type(ref["bytes"]) is not int or not 0 <= ref["bytes"] <= maximum or len(ref["sha256"]) != 64:
        raise ValueError("bounded actual byte count")
    p = Path(ref["path"])
    if not p.is_absolute() or p.is_symlink() or p.resolve() != p:
        raise ValueError("absolute nonsymlink raw file")
    raw = p.read_bytes()
    if len(raw) != ref["bytes"] or hashlib.sha256(raw).hexdigest() != ref["sha256"]:
        raise ValueError("actual size/SHA")
    return raw

def consume(frame_ref, *, kernel_sha):
    raw = ref_read(frame_ref, 8 * 1024 * 1024)
    frame = json.loads(raw)
    if frame.get("schema") != "kivi.actual-packed-qkav-frame/v1" or frame.get("kernel_source_sha256") != kernel_sha:
        raise ValueError("actual new kernel origin, not borrowed native PASS")
    bits,dtype = frame["bits"],frame["dtype"]
    pages,records,slots = frame["pool_geometry"]
    if bits not in (2,4) or dtype not in ("float16","bfloat16") or any(type(x) is not int or x<=0 for x in (pages,records,slots)):
        raise ValueError("actual compact geometry")
    sizes = {"key_codes":pages*128*256*bits//8, "key_scales":pages*1024*2, "key_minima":pages*1024*2,
             "value_codes":records*256*bits//8, "value_scales":records*8*2, "value_minima":records*8*2,
             "key_residual":slots*128*256*2, "value_residual":slots*129*256*2}
    if sum(sizes.values()) > 192*1024*1024 or set(frame["pool_fields"]) != set(FIELDS):
        raise ValueError("bounded whole compact snapshots (not a whole-model lease)")
    payload={}
    for name in FIELDS:
        if frame["pool_fields"][name]["bytes"] != sizes[name]:
            raise ValueError("actual field extent " + name)
        payload[name]=ref_read(frame["pool_fields"][name],sizes[name])
    rows=frame["rows"]
    if not 1 <= len(rows) <= 16:
        raise ValueError("actual batch1..16")
    verdict=[]
    owners=set()
    for row in rows:
        length,kp,vp,slot=row["controls"]
        if any(type(x) is not int for x in (length,kp,vp,slot)) or not (1<=length<=33792 and 0<=kp<=length
                and kp%128==0 and 0<=vp<=length and 1<=length-kp<=128 and 1<=length-vp<=129 and 0<=slot<slots):
            raise ValueError("pending K128/V129 lengths, no geometry shrink")
        if len(row["kp"]) != kp//128 or len(row["vp"]) != vp or any(type(x) is not int or not 0<=x<pages for x in row["kp"]) or any(type(x) is not int or not 0<=x<records for x in row["vp"]):
            raise ValueError("whole actual per-request remap")
        owner=(row["request_id"],slot,row["epoch"],row["generation"])
        if type(owner[0]) is not str or not owner[0] or any(type(x) is not int or x<=0 for x in owner[2:]) or owner in owners:
            raise ValueError("distinct actual claimed owners")
        owners.add(owner)
        if set(row["identity_refs"]) != set(IDENTITIES):
            raise ValueError("six raw seam identities required; semantic owner admission separate")
        for ref in row["identity_refs"].values():
            ref_read(ref,8*1024*1024)
        qraw=ref_read(row["query_ref"],6*256*2);oraw=ref_read(row["output_ref"],6*256*2)
        if len(qraw)!=6*256*2 or len(oraw)!=len(qraw):
            raise ValueError("entire Q6/D256 query and native output")
        q=[[oracle.scalar(qraw,h*256+d,dtype) for d in range(256)] for h in range(6)]
        actual=[oracle.scalar(oraw,i,dtype) for i in range(6*256)]
        if not all(math.isfinite(x) for h in q for x in h):
            raise ValueError("finite actual query")
        expected=oracle.attention(payload,row,q,bits,dtype)
        numerical=oracle.compare(actual,[x for h in expected["scalar_a16_boundary_output"] for x in h])
        split=[x for h in expected["official_python_split_boundary_output"] for x in h]
        split_rms=math.sqrt(math.fsum(x*x for x in split)/len(split))
        split_error=math.sqrt(math.fsum((a-b)**2 for a,b in zip(actual,split))/len(split))/max(split_rms,1e-8)
        verdict.append({"owner":owner,"length":length,"full_output_elements":len(actual),
                        "named_ascend_boundary_measure":numerical,"official_python_split_relative_rms_reported":split_error,
                        "raw_identity_files_sha_checked":True,"semantic_owner_device_lease_verified":False})
    return {"schema":"kivi.packed-qkav.raw-frame-numerical/v1","frame_ref":frame_ref,
            "kernel_source_sha256":kernel_sha,"rows":verdict,
            "scope":"packed snapshots + independent vectorized-unpack/scalar-fsum numerical comparison only",
            "reference_source_sha256":hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest(),
            "reader_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "released_cuda_parity":False,"writer_lifecycle_complete":False,"whole_176":False,
            "native_ready":False,"model_ready":False,"performance_ready":False,"run_authority":False}


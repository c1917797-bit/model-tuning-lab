"""Decode the ACTUAL native 17-field ABI. No tensors, no NPU or synthetic PASS."""
import re,struct
from pathlib import Path
FIELDS=("vectorCoreNum","ubCalSize","ubRestBytes","t","nk","dk","nv","dv",
        "sBlockNum","b","vStep","stateOutBufferNum","attnOutBufferNum","scale",
        "hasGama","hasGamaK","hasAcceptedTokens")
FORMAT="<13If3I"
SIZE=72
HEADER=Path("/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/operator/native_copy_trace_v2/op_kernel/native_trace_tiling_data.h")
def require(v,s):
    if not v:raise ValueError(s)
def audit_layout():
    actual=tuple(re.findall(r"\b(uint32_t|float)\s+(\w+)\s*;",HEADER.read_text()))
    expected=tuple(("float" if n=="scale" else "uint32_t",n) for n in FIELDS)
    require(actual==expected,"actual C++ struct order/type mismatch")
    require(struct.calcsize(FORMAT)==68,"17 fields + four zero tail bytes")
    return expected
def decode_tiling(values):
    audit_layout()
    require(len(values)==SIZE,"actual tiling size72")
    raw=bytes(values)
    require(raw[68:]==b"\0"*4,"actual deterministic alignment tail")
    return dict(zip(FIELDS,struct.unpack(FORMAT,raw[:68])))

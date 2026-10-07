#!/usr/bin/env python3
"""Source identity checks only. Never an Ascend numerical PASS."""
import hashlib,json,re
from pathlib import Path
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
OP=ROOT/"projects/kvbuffer-parallel-ascend/operator/native_copy_trace_v2"
SNAP=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/native-source-snapshot-20261007-1052/recurrent_gated_delta_rule")
def require(v,s):
    if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def text(p):return Path(p).read_bytes().decode().replace("\r\n","\n")
def body(source,name,cls):
    marker=cls+"::"+name+"("
    start=source.index(marker);start=source.rfind("\n",0,start)+1
    b=source.index("{",start);depth=1;end=b+1
    while depth:
        require(end<len(source),"balanced method")
        if source[end]=="{":depth+=1
        if source[end]=="}":depth-=1
        end+=1
    return source[start:end]
def transformed_native(s):
    s=s.replace("RecurrentGatedDeltaRule","NativeRecurrentCopyTraceV2")
    s=s.replace("__RECURRENT_GATED_DELTA_RULE_KERNEL_H_","__NATIVE_RECURRENT_COPY_TRACE_V2_KERNEL_H_")
    s=s.replace("recurrent_gated_delta_rule_tiling_data.h","native_trace_tiling_data.h")
    m=json.loads(text(OP/"SOURCE_TRANSFORMS.json"))
    for item in m["header_transforms"]:
        require(s.count(item["from"])==1,"unique native observer seam")
        s=s.replace(item["from"],item["to"],1)
    return s if s.endswith("\n") else s+"\n"  # explicit final-LF canonicalization, not arithmetic
def port_method(s):
    s=s.replace("RecurrentGatedDeltaRuleTiling::","NativeTiling::")
    s=re.sub(r"    auto stateDtype = context_->GetInputDesc\(STATE_INDEX\)->GetDataType\(\);\n","",s)
    s=s.replace("(stateDtype == ge::DT_FLOAT) ? 4 : 2","4")
    s=s.replace("ge::graphStatus ","bool ").replace("ge::GRAPH_FAILED","false").replace("ge::GRAPH_SUCCESS","true")
    return s.replace("OP_LOGD(","NATIVE_TRACE_LOG(").replace("OP_LOGE(","NATIVE_TRACE_LOG(")
def audit():
    m=json.loads(text(OP/"SOURCE_TRANSFORMS.json"));checks=[]
    require(sha(SNAP/"op_kernel/recurrent_gated_delta_rule.h")==m["native_header_sha256"],"actual native header bytes")
    require(sha(SNAP/"op_host/recurrent_gated_delta_rule_tiling.cpp")==m["native_tiling_cpp_sha256"],"actual native tiling bytes")
    checks+=["native_header_sha256","native_tiling_cpp_sha256"]
    expected=transformed_native(text(SNAP/"op_kernel/recurrent_gated_delta_rule.h"))
    require(text(OP/"op_kernel/recurrent_gated_delta_rule_copy_trace.h")==expected,
            "complete header differs outside six copy-only transformations")
    checks.append("complete_header_arithmetic_queue_ub_identity")
    original=text(SNAP/"op_host/recurrent_gated_delta_rule_tiling.cpp")
    port=text(OP/"op_extension/native_tiling.h")
    for name,source in m["native_methods"].items():
        require(body(original,name,"RecurrentGatedDeltaRuleTiling")==source,"actual method source "+name)
        require(re.sub(r"\s+","",body(port,name,"NativeTiling"))==re.sub(r"\s+","",port_method(source)),
                "exact specialized native method "+name)
        checks.append("native_method_"+name)
    require("BufferProfile(uint32_t s=1,uint32_t a=1" in port,"native buffer defaults1/1")
    require("CalcFixedUbBytes(16,128,128)" in port and "CalcWorkingUbBytes(16,128,128)" in port,
            "actual aligned native NV16, not unaligned12")
    require("sizeof(NativeRecurrentCopyTraceV2TilingData)==72" in port,"native aligned17field72B")
    checks+=["native_profile_defaults","native_aligned_ub_geometry","native_tiling_size"]
    wrapper=text(OP/"op_extension/qwen36_native_recurrent_copy_trace_v2_torch.cpp")
    require("PlatformAscendCManager::GetInstance()" in wrapper and "CoreMemType::UB,ub" in wrapper and
            "actualCores==cores" in wrapper,"actual hardware not guessed tiling")
    require("std::memcpy(bytes.data(),&data,68)" in wrapper and "std::array<uint8_t,72> bytes{}" in wrapper,"deterministic padding")
    decode=wrapper[wrapper.index("at::Tensor qwen36_native_recurrent_copy_trace_v2_decode_trace("):]
    require("aclrtMemcpy" not in decode and ".cpu(" not in decode and ".item(" not in decode and
            "stream(false)" in decode and "RunOpApi" in decode,"capture-safe launch/no host tensor transfer")
    require("mutable storage ranges overlap" in wrapper and "storage bound" in wrapper and "pointer%32==0" in wrapper,
            "actual physical mutable storage constraints")
    schema=text(OP/"op_extension/register.cpp")
    for alias in ["Tensor(a!) state","Tensor(b!) precast_trace","Tensor(c!) selected_state_trace"]:
        require(alias in schema,"actual mutable schema "+alias)
    require("qwen36_native_recurrent_copy_trace_v2" in schema and "qwen36_kvbuffer_native_order_trace_v2" not in schema,"independent namespace")
    checks+=["actual_hardware_tiling","deterministic_tiling_padding","capture_safe_launch","physical_storage_guards","mutable_aliases","independent_namespace"]
    # Negative arithmetic mutation must be rejected by the complete-header anchor.
    mutant=expected.replace("RGDR_ENABLE_ADD_FOLD_REDUCE  1","RGDR_ENABLE_ADD_FOLD_REDUCE  0",1)
    require(mutant!=expected,"non-vacuous source negative")
    checks.append("arithmetic_mutation_detected")
    return {"schema":"kvbp.native-recurrent-source-audit/v2","status":"source_only","checks":checks,
            "npu_executed":False,"native_precast_observed":False,"numeric_verified":False}
if __name__=="__main__":print(json.dumps(audit(),indent=2))

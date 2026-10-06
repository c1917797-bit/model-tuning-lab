#!/usr/bin/env python3
"""Read-only source/geometry contract. NOT ASC compilation, NPU or performance."""
import difflib
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD = HERE.parent
HEADER = HERE / "op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode.h"
TILING = HERE / "op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h"
WRAPPER = HERE / "op_extension/qwen36_gdn_damp_integer_compaction_v1_decode_torch.cpp"
ENTRY = HERE / "op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_kernel.asc"
MANIFEST = HERE / "source_manifest.json"
sys.dont_write_bytecode = True

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def body(text, name):
    pattern = r"__aicore__ inline[^;{\n]*\b" + re.escape(name) + r"\([^;{]*?\)\s*\{"
    match = re.search(pattern, text)
    if not match:
        raise AssertionError("method definition missing: " + name)
    start = match.end()-1
    depth = 0
    for end in range(start, len(text)):
        depth += (text[end] == "{") - (text[end] == "}")
        if depth == 0:
            return text[start:end+1]
    raise AssertionError("unbalanced method body: " + name)

def rename(text):
    return (text.replace("Qwen36Damp", "Qwen36DampIntegerCompactionV1")
            .replace("QWEN36_GDN_DAMP", "QWEN36_GDN_DAMP_INTEGER_COMPACTION_V1")
            .replace("qwen36_gdn_damp", "qwen36_gdn_damp_integer_compaction_v1")
            .replace("qwen36_damp,", "qwen36_damp_integer_compaction_v1,")
            .replace("Qwen36GdnDampDecode", "Qwen36GdnDampIntegerCompactionV1Decode"))

def check():
    manifest = json.loads(MANIFEST.read_text())
    for section in ("compiled_sources", "original_sources"):
        for relative, expected in manifest[section].items():
            assert sha(ROOT / relative) == expected, relative
    old = (OLD / "op_kernel/qwen36_gdn_damp_decode.h").read_text()
    candidate = HEADER.read_text()
    unchanged = ("VectorToScalar", "LoadValidateMetadata", "LoadPlan", "LoadToken",
                 "LoadState", "LowBroadcast", "MatVec", "ReduceRows",
                 "StoreHead", "StoreInvalid")
    for name in unchanged:
        assert body(candidate, name) == body(old, name), name
    # Only the documented explicit workspace seam may differ in UpdateReadout.
    # All recurrence, reduction order, barriers and updated-state readout remain
    # byte-identical after this exact textual normalization.
    old_broadcast = "        Broadcast<float, 2, 1>(broad_, delta_, dstShape, srcShape);"
    explicit_broadcast = """        // Existing 8192B scratch is dead after LoadState and before PackStore.
        // Public fifth-argument API avoids the implicit PopStackBuffer/LCM path.
        auto broadcastTmp = scratchB_.ReinterpretCast<uint8_t>();
        Broadcast<float, 2, 1>(broad_, delta_, dstShape, srcShape, broadcastTmp);"""
    readout = body(candidate, "UpdateReadout")
    assert readout.count(explicit_broadcast) == 1
    assert readout.replace(explicit_broadcast, old_broadcast) == body(old, "UpdateReadout")
    original_pack = body(old, "PackStore")
    candidate_pack = body(candidate, "PackStore")
    seam = "        LowBroadcast(lowFloat_, lowFloat_, scaleVector_, true);"
    assert original_pack.split(seam)[0] == candidate_pack.split("        for (uint32_t chunk")[0]
    suffix = "        DataCopy(packed.ReinterpretCast<float>()[1152]"
    assert (original_pack[original_pack.index(suffix):] ==
            candidate_pack[candidate_pack.index(suffix):].replace("        return true;\n", ""))
    original_task = body(old, "ProcessTask")
    changed = """            if (!PackStore(headSlot, group)) {
                StoreInvalid(token * VALUE_HEADS + head);
                return;
            }"""
    assert body(candidate, "ProcessTask").replace(changed, "            PackStore(headSlot, group);") == original_task
    quant = body(candidate, "QuantizeChunk")
    assert "LowBroadcast(lowFloat_, lowFloat_, scaleVector_, true)" not in candidate
    assert "0x42fe0000" in quant and quant.index("0x42fe0000") < quant.index("Cast(magnitude_")
    assert quant.index("Cast(magnitude_") < quant.index("::Certify<")
    assert "GatherMaskParams(1, 1, 8, 1)" in quant
    assert "rank < static_cast<uint32_t>(retained)" in quant
    assert "for (uint32_t lane" not in quant
    assert quant.count("ExactCode(") == 1
    assert "VectorToScalar();" in quant and "HardEvent::S_V" in quant
    assert quant.index("lane < 0 ||") < quant.index("rawX.GetValue(lane)")
    assert quant.index("WaitFlag<HardEvent::S_V>") < quant.index("if (!valid) { return false; }")
    assert "std::array" not in candidate
    assert "Duplicate(rejectMask_" not in candidate
    assert "const_cast<__gm__ int32_t*>(reinterpret_cast<const __gm__ int32_t*>(tiling)) + LUT_OFFSET_INTS" in candidate
    assert candidate.count("quantizerLutGm_") == 3
    assert "DataCopy(local, quantizerLutGm_, 256);" in candidate
    assert "quantizerLutGm_.SetValue" not in candidate
    assert sha(HERE / "audit/decode-header-v1.h.txt") == "966a675c2e8c640b935b3fa08b253c2271672c89a2581a431649b7ee83480b84"
    # Every new allocation is disjoint and 32B aligned. Bounds are explicit,
    # not a proof of compiler LCM or of TPipe allocator/physical alignment.
    N = 448
    plane = N*4
    regions = [(f"cert{i}", i*plane, plane) for i in range(16)]
    regions += [("accepted", 28672, plane)]
    names = ("quotient", "scale", "magnitude", "codes", "indices", "compact")
    regions += [(n, 30464+i*plane, plane) for i,n in enumerate(names)]
    regions += [("C",41216,512),("F",41728,512),("mask",42240,256)]
    for i,(name,off,size) in enumerate(regions):
        assert off%32 == size%32 == 0 and off+size <= 42496, name
        for _,other,length in regions[i+1:]:
            assert off+size <= other or other+length <= off, name
    assert sum(size for _,_,size in regions) == 42496
    queues = 160+864+2048+5120+2*5120+2*256
    assert queues == 18944 and 79872+queues+42496 == 141312
    # Exact host C/F generation agrees with the frozen independent model.
    sys.path.insert(0, str(OLD / "quantizer/fast_integer_certificate"))
    from integer_certificate import tables
    rows = []
    for j in range(128):
        safe_j = min(j,126)
        k = 2*safe_j+1
        f = k.bit_length()-2
        center = k << (23-f)
        rows.append((center-1 if safe_j&1 else center+1, f))
    assert rows == tables()
    lut_hash = {
        "c_sha256":hashlib.sha256(struct.pack("<128i",*(c for c,_ in rows))).hexdigest(),
        "f_sha256":hashlib.sha256(struct.pack("<128i",*(f for _,f in rows))).hexdigest()}
    wrapper = WRAPPER.read_text()
    decode = wrapper[wrapper.index("at::Tensor qwen36_gdn_damp_integer_compaction_v1_decode_torch"):]
    assert ".stream(false)" in decode and ".stream(true)" not in decode
    assert ".to(at::kCPU)" not in decode and "aclrtMemcpy(" not in decode
    assert "OpCommand::RunOpApi" in decode
    assert "storage.nbytes()" in wrapper and " % 32 == 0" in wrapper
    assert "Ascend910B4" in wrapper and "initialize_quantizer_lut" in wrapper
    assert "stream(true)" in wrapper[:wrapper.index("at::Tensor qwen36_gdn_damp_integer_compaction_v1_decode_torch")]
    entry = ENTRY.read_text()
    host_projection = re.sub(r"#if defined\(__NPU_ARCH__\).*?#endif", "", entry, flags=re.S)
    assert "extern \"C\" __global__ __vector__ void" in host_projection
    assert "qwen36_gdn_damp_integer_compaction_v1_decode_kernel(" in host_projection
    assert re.search(r"\)\s*\{\s*\}", host_projection)
    tiling = TILING.read_text()
    assert "ABI_VERSION = 2" in tiling and "sizeof(DampTilingData) == 1056" in tiling
    assert "offsetof(DampTilingData, cTable) == 32" in tiling
    cmake = (HERE / "CMakeLists.txt").read_text()
    assert 'option(DAMP_BUILD_INTEGER_COMPACTION_V1' in cmake and ' OFF)' in cmake
    assert "--npu-arch=dav-2201" in cmake
    registration = (HERE / "op_extension/register.cpp").read_text()
    assert "qwen36_damp_integer_compaction_v1" in registration
    for alias in ("Tensor(a!) high_state", "Tensor(b!) low_state", "Tensor(c!) low_scale"):
        assert alias in registration
    return {"schema":"damp_integer_compaction_source_contract_v1",
            "status":"software_source_contract_pass", "unchanged_method_bodies":list(unchanged),
            "original_sources_checked":len(manifest["original_sources"]),
            "compiled_sources_checked":len(manifest["compiled_sources"]),
            "new_ub_regions":len(regions),"explicit_ub_bytes":141312,
            "workspace_adapted_method":"UpdateReadout",
            "broadcast_explicit_existing_scratch_bytes":8192,
            "hidden_lcm_proven":False,"lut":lut_hash,
            "asc_compiled":False,"npu_executed":False,
            "graph_supported":False,"performance_result":None}

def diff():
    manifest = json.loads(MANIFEST.read_text())
    for original in manifest["original_sources"]:
        rel = Path(original).relative_to(Path("projects/damp-ascend/operator"))
        target_rel = str(rel).replace("qwen36_gdn_damp", "qwen36_gdn_damp_integer_compaction_v1")
        target = HERE / target_rel
        print("".join(difflib.unified_diff((ROOT/original).read_text().splitlines(True),
                    target.read_text().splitlines(True),fromfile=original,
                    tofile=str(target.relative_to(ROOT)))),end="")

if __name__ == "__main__":
    if sys.argv[1:] == ["--diff"]:
        diff()
    elif not sys.argv[1:]:
        print(json.dumps(check(),sort_keys=True,indent=2))
    else:
        raise SystemExit("usage: check_source_contract.py [--diff]")

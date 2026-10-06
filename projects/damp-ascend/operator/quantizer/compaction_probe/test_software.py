#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""No Torch/device/build; AST + source contract + independent fixture checks."""
import ast
import hashlib
import json
import re
from pathlib import Path
from cases import EXACT_SHA,GUARDS,software_gate
def main():
    root=Path(__file__).resolve().parent
    for p in root.glob("*.py"):
        ast.parse(p.read_text(),filename=str(p))
    exact=root.parent/"exact_quantizer_bits.h"
    assert hashlib.sha256(exact.read_bytes()).hexdigest()==EXACT_SHA
    kernel=(root/"op_kernel/compaction_probe_kernel.asc").read_text()
    host=kernel.split("#if defined(__NPU_ARCH__)")[0]
    # The definition remains after device-include guard and visible to host.
    definition=kernel.index('extern "C" __global__ __vector__ void')
    opening=kernel.index("{",definition)
    assert kernel.index("#if defined(__NPU_ARCH__)",definition)>opening
    body=(root/"op_kernel/compaction_probe.h").read_text()
    plan=(root/"op_kernel/probe_plan.h").read_text()
    guard_match=re.search(r"constexpr int32_t GUARDS\[OUTPUTS\]=\{([^}]+)\};",plan)
    assert guard_match and tuple(int(v.strip(),0) for v in guard_match.group(1).split(","))==GUARDS
    assert "#include <array>" not in plan and "std::array" not in plan
    assert "Duplicate(packedMask.ReinterpretCast<uint32_t>(),uint32_t(0),64);" in body
    assert "Duplicate(packedMask,uint8_t(0),256);" not in body
    old_plan=(root/"audit/probe_plan-v1.h.txt").read_text()
    old_body=(root/"audit/compaction_probe-v1.h.txt").read_text()
    assert hashlib.sha256(old_plan.encode()).hexdigest()=="d45955942a930d3d73c90a86d7f740ec8d7c2ca561a1d8e0bdf40606016676bf"
    assert hashlib.sha256(old_body.encode()).hexdigest()=="bb9fea145f7ffeb34534e24c707d32bdffbf9de31aec5d423c771f7c4d015798"
    assert plan==old_plan.replace("#include <array>\n","").replace("constexpr std::array<int32_t,OUTPUTS> GUARDS=","constexpr int32_t GUARDS[OUTPUTS]=")
    assert body==old_body.replace("Duplicate(packedMask,uint8_t(0),256);","Duplicate(packedMask.ReinterpretCast<uint32_t>(),uint32_t(0),64);")
    assert "CompareScalar(packedMask," in body and "ReinterpretCast<float>()" in body
    assert "GatherMask(w[1],w[0],packedMask.ReinterpretCast<uint32_t>()" in body
    assert "rank<static_cast<uint32_t>(retained)" in body
    assert "ExactCode(" in body and "HardEvent::V_S" in body and "HardEvent::S_V" in body
    wrapper=(root/"op_extension/compaction_torch.cpp").read_text()
    assert wrapper.index("flags[i]==0 || flags[i]==1") < wrapper.index("Outputs compact(")
    assert 'PROPERTIES LANGUAGE ASC' in (root/"CMakeLists.txt").read_text()
    assert "RunOpApi(" in wrapper and "<<<1,nullptr,stream>>>" in wrapper
    assert "stream(false)" in wrapper and "at::full" in wrapper
    result=software_gate()
    result["source_contract"]="AST/text precheck only; not CXX/ASC/ELF proof"
    print(json.dumps(result,sort_keys=True,allow_nan=False))
if __name__=="__main__":main()

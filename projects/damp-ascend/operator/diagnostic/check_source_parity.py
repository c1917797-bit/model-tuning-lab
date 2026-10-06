#!/usr/bin/env python3
"""Stdlib-only exact source-body audit; no compile, load, device or Git writes."""
import argparse
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAIRS = {
    "CMakeLists.txt": "CMakeLists.txt",
    "op_extension/ops.h": "op_extension/ops.h",
    "op_extension/register.cpp": "op_extension/register.cpp",
    "op_extension/qwen36_gdn_damp_decode_torch.cpp": "op_extension/qwen36_gdn_damp_trace_torch.cpp",
    "op_kernel/qwen36_gdn_damp_decode.h": "op_kernel/qwen36_gdn_damp_trace.h",
    "op_kernel/qwen36_gdn_damp_decode_kernel.asc": "op_kernel/qwen36_gdn_damp_trace_kernel.asc",
    "op_kernel/qwen36_gdn_damp_decode_tiling.h": "op_kernel/qwen36_gdn_damp_trace_tiling.h",
}
UNCHANGED = ("VectorToScalar", "LoadValidateMetadata", "LoadPlan", "LoadToken",
             "LoadState", "LowBroadcast", "MatVec", "ReduceRows", "UpdateReadout",
             "StoreHead", "StoreInvalid")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def body(source, name):
    # First use can be a call before declaration; match an actual method.
    matches = list(re.finditer(r"__aicore__\s+inline\s+[^()\n]+?\b" +
                              re.escape(name) + r"\s*\(", source))
    if len(matches) != 1:
        raise ValueError("declaration not unique: " + name)
    opening = source.index("{", matches[0].start())
    depth = 1
    i = opening+1
    while depth:
        if source[i] == "{": depth += 1
        if source[i] == "}": depth -= 1
        i += 1
    return source[opening:i]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--production-root", type=Path, default=HERE.parent)
    args = p.parse_args()
    manifest = json.loads((HERE/"production_sources.json").read_text())
    production = args.production_root.resolve()
    for relative, expected in manifest["source_hashes"].items():
        if sha(production/relative) != expected:
            raise ValueError("production source changed: " + relative)
    old = (production/"op_kernel/qwen36_gdn_damp_decode.h").read_text()
    new = (HERE/"op_kernel/qwen36_gdn_damp_trace.h").read_text()
    checks = {name: body(old, name) == body(new, name) for name in UNCHANGED}
    checks["PackStore"] = body(old, "PackStore") == body(new, "PackStore").replace(
        "        TraceQuotient(group);\n", "")
    checks["ProcessTask"] = body(old, "ProcessTask") == body(new, "ProcessTask").replace(
        "        traceTask_ = token * VALUE_HEADS + head;\n", "").replace(
        "            TraceUpdated(group);\n", "")
    if not all(checks.values()):
        raise ValueError("arithmetic body changed: " + repr(checks))
    result = {"schema": "damp-diagnostic-source-parity/v1", "status": "PASS",
              "unchanged_kernel_body_checks": checks,
              "production_hashes": manifest["source_hashes"],
              "diagnostic_source_hashes": {
                  str(x.relative_to(HERE)): sha(x) for x in sorted(HERE.rglob("*"))
                  if x.is_file() and "__pycache__" not in x.parts},
              "scope": "source audit only, no build or NPU proof"}
    print(json.dumps(result, indent=2, allow_nan=False))

if __name__ == "__main__":
    main()

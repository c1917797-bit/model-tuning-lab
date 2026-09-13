#!/usr/bin/env python3
"""Static contract for the upstream-derived fused GDN prefill candidate."""

from pathlib import Path


root = Path(__file__).resolve().parents[2]
patch = (
    root
    / "qwen35-performance-optimization"
    / "runtime-monkeypatch"
    / "sitecustomize.py"
).read_text(encoding="utf-8")
runner = (
    root
    / "qwen35-performance-optimization"
    / "scripts"
    / "run_qwen35_gdn_runtime_t12_npu03.sh"
).read_text(encoding="utf-8")

required_patch_fragments = [
    "QWEN35_ASCEND_UPSTREAM_FUSED_PREFILL",
    "upstream 77d13e2c0",
    "torch_npu.npu_chunk_gated_delta_rule",
    "initial_state = ssm_state[prefill_state_indices]",
    "last_recurrent_state.to(ssm_state.dtype)",
    "_qwen35_probe_fused_chunk",
    "AscendGatedDeltaNetAttention._qwen35_probe_fused_chunk()",
    "device probe failed; using Triton",
    'f"fallback ({type(exc).__name__})"',
]
for fragment in required_patch_fragments:
    assert fragment in patch, fragment

assert "candidate-fused-prefill)" in runner
assert "fused_prefill_metadata_reuse_enabled=0" in runner
assert "upstream_fused_prefill_enabled=1" in runner
assert "mmar_prefill_threshold=0" in runner
assert "mmar_prefill_max_tokens=0" in runner

print("PASS: upstream-derived fused GDN prefill source contract")

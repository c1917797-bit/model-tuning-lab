#!/usr/bin/env python3
"""Static trust contract for the pinned upstream FusedGdnDecode integration."""

from pathlib import Path


root = Path(__file__).resolve().parents[2]
patch = (root / "qwen35-performance-optimization/runtime-monkeypatch/sitecustomize.py").read_text(encoding="utf-8")
runner = (root / "qwen35-performance-optimization/scripts/run_qwen35_gdn_runtime_t12_npu03.sh").read_text(encoding="utf-8")

for fragment in (
    "QWEN35_ASCEND_FUSED_GDN_DECODE",
    "torch.ops.custom.npu_fused_gdn_decode",
    "the exact Qwen3.5-27B TP4 contract",
    "spec_sequence_masks is None",
    "self.A_log.dtype == torch.float32",
    "ssm_state.dtype in (torch.float32, mixed_qkv_non_spec.dtype)",
    "non_spec_state_indices_tensor.dtype == torch.int32",
):
    assert fragment in patch, fragment

for fragment in (
    "candidate-fused-prefill-conv-prepack-fused-decode)",
    "d967eeb08ceef7c394d0d5e27767e5b08b77aa58",
    "1c5e65a7d7b91abb33bc00b368a12bf2e05331e933ec1ac041cf0fb0b07702e4",
    "a5abcbcc49f8b192a5444c36252989b9004ba53a4c913a98c9630b886a2191d8",
    "312225147b5cb6abf6010a48d89fc8f5b3d47ad6b4723aab0c61b3c2bef94076",
    '-v "$t36_root:$t36_container_root:ro"',
):
    assert fragment in runner, fragment

print("PASS: pinned upstream FusedGdnDecode runtime source contract")

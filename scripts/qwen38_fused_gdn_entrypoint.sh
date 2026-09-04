#!/usr/bin/env bash
set -euo pipefail

PATCH_PATH=${QWEN38_GDN_PATCH:-/experiment/patches/qwen38-gdn-state-layout/77d13e2c0-fused-gdn-prefill.patch}
SRC=/vllm-workspace/vllm-ascend

cd "$SRC"
if grep -q 'npu_chunk_gated_delta_rule' vllm_ascend/ops/gdn.py; then
  echo "GDN fused patch already present; reusing patched source tree"
else
  git apply --check "$PATCH_PATH"
  git apply "$PATCH_PATH"
fi

# Proof that the algorithm path is present before importing vLLM.
grep -q 'npu_chunk_gated_delta_rule' vllm_ascend/ops/gdn.py

exec vllm serve "$@"

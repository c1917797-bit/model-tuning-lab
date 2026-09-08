#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
runner="$root/qwen35-performance-optimization/scripts/run_qwen35_gdn_runtime_t12_npu03.sh"
[[ -x "$runner" || -f "$runner" ]]

grep -Fq 'flock -n 9' "$runner"
grep -Fq 'docker run --rm' "$runner"
grep -Fq -- '--device /dev/davinci0' "$runner"
grep -Fq -- '--device /dev/davinci3' "$runner"
! grep -Fq -- '--device /dev/davinci4' "$runner"
! grep -Fq -- '--privileged' "$runner"
grep -Fq 'VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=1' "$runner"
grep -Fq 'VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD=0' "$runner"
grep -Fq 'qwen35-performance-optimization/runtime-monkeypatch' "$runner"
! grep -Eq '/vllm-workspace/(vllm|vllm-ascend)/.*\.py:ro' "$runner"
grep -Fq 'sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1' "$runner"
grep -Fq '8d2d403f17843ed2e40d2e768b61bc1faa55fa9fce9d1fcd58af810567aa89e1' "$runner"

echo 'PASS: t12 NPU0-3 runtime-only launcher contract'

#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
runner="$root/qwen35-performance-optimization/scripts/run_qwen35_gdn_runtime_t12_npu03.sh"
capture="$root/qwen35-performance-optimization/scripts/capture_qwen35_gdn_t12_activation.sh"
[[ -x "$runner" || -f "$runner" ]]

grep -Fq 'flock -n 9' "$runner"
grep -Fq 'run --rm' "$runner"
grep -Fq -- '--shm-size 64g' "$runner"
grep -Fq 'VARIANT:-candidate' "$runner"
grep -Fq 'candidate) patch_enabled=1' "$runner"
grep -Fq 'control) patch_enabled=0' "$runner"
grep -Fq -- '--label com.c1917797.qwen35-t12=1' "$runner"
grep -Fq -- '--label com.c1917797.qwen35-variant="$variant"' "$runner"
! grep -Eq '(^|[[:space:]])\+([[:space:]]|$)' "$runner"
grep -Fq -- '--device /dev/davinci0' "$runner"
grep -Fq -- '--device /dev/davinci3' "$runner"
! grep -Fq -- '--device /dev/davinci4' "$runner"
! grep -Fq -- '--privileged' "$runner"
grep -Fq 'VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS="$patch_enabled"' "$runner"
! grep -Fq 'VLLM_ASCEND_MMAR_PREFILL_' "$runner"
grep -Fq 'qwen35-performance-optimization/runtime-monkeypatch' "$runner"
grep -Fq -- '-v "$repo_root":/experiment:ro' "$runner"
grep -Fq -- '-v "$patch_root":/opt/qwen35-t12-monkeypatch:ro' "$runner"
! grep -Eq '/vllm-workspace/(vllm|vllm-ascend)/.*\.py:ro' "$runner"
! grep -Eq 'docker[[:space:]]+(commit|cp)([[:space:]]|$)' "$runner"
grep -Fq 'sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1' "$runner"
grep -Fq 'aaa4f27c244d68b6f628325b521d703abde0f05973459b1f4517d1fad1cabe1b' "$runner"
grep -Fq 'qwen35_gdn_runtime_t12_${variant}_npu03' "$capture"

echo 'PASS: t12 NPU0-3 runtime-only launcher contract'

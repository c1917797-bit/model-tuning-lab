#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
runner="$root/qwen35-performance-optimization/scripts/run_qwen35_gdn_runtime_t12_npu03.sh"
starter="$root/qwen35-performance-optimization/scripts/start_qwen35_gdn_runtime_t12_supervised.sh"
capture="$root/qwen35-performance-optimization/scripts/capture_qwen35_gdn_t12_activation.sh"
[[ -x "$runner" || -f "$runner" ]]
[[ -x "$starter" || -f "$starter" ]]

grep -Fq 'flock -n 9' "$runner"
grep -Fq 'run -d --rm' "$runner"
grep -Fq 'docker wait "$container_id"' "$runner"
grep -Fq 'docker logs --follow "$container_id"' "$runner"
grep -Fq -- '--shm-size 64g' "$runner"
grep -Fq 'VARIANT:-candidate' "$runner"
grep -Fq 'candidate)' "$runner"
grep -Fq 'patch_enabled=1' "$runner"
grep -Fq 'candidate-prefill)' "$runner"
grep -Fq 'candidate-prefill-t21)' "$runner"
grep -Fq 'candidate-prefill-no-prefetch)' "$runner"
grep -Fq 'weight_prefetch_enabled=false' "$runner"
grep -Fq 'prefetch_patch_enabled=0' "$runner"
grep -Fq 'mmar_prefill_threshold=512' "$runner"
grep -Fq 'mmar_prefill_max_tokens=16384' "$runner"
grep -Fq 'control)' "$runner"
grep -Fq 'patch_enabled=0' "$runner"
grep -Fq -- '--label com.c1917797.qwen35-t12=1' "$runner"
grep -Fq -- '--label com.c1917797.qwen35-variant="$variant"' "$runner"
! grep -Eq '(^|[[:space:]])\+([[:space:]]|$)' "$runner"
grep -Fq -- '--device /dev/davinci0' "$runner"
grep -Fq -- '--device /dev/davinci3' "$runner"
! grep -Fq -- '--device /dev/davinci4' "$runner"
! grep -Fq -- '--privileged' "$runner"
grep -Fq 'VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS="$patch_enabled"' "$runner"
grep -Fq 'QWEN35_ASCEND_WEIGHT_PREFETCH_PATCH="$prefetch_patch_enabled"' "$runner"
grep -Fq 'ASCEND_MATMUL_ALLREDUCE_M1_AICPU_FIRST' "$runner"
grep -Fq 'CANDIDATE_OPP_ROOT:$operator_container_root:ro' "$runner"
grep -Fq 'candidate OPP tree SHA256 mismatch' "$runner"
grep -Fq 'packaged set_env.bash is not sourced' "$runner"
grep -Fq '8e22ab5d7b0c5b7eb88a393bc452a60fc377df434e1b8f70986a48723b67c84a' "$runner"
grep -Fq 'd324d27a6bb0c957af968d83f8642b94bfb6cb56f9ad0f8402313fb65b434edb' "$runner"
grep -Fq 'VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD="$mmar_prefill_threshold"' "$runner"
grep -Fq 'VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS="$mmar_prefill_max_tokens"' "$runner"
grep -Fq 'qwen35-performance-optimization/runtime-monkeypatch' "$runner"
grep -Fq -- '-v "$repo_root":/experiment:ro' "$runner"
grep -Fq -- '-v "$patch_root":/opt/qwen35-t12-monkeypatch:ro' "$runner"
grep -Fq 'ENABLE_DYNAMIC_PROFILING:-0' "$runner"
grep -Fq 'PROFILE_DIR requires ENABLE_DYNAMIC_PROFILING=1' "$runner"
grep -Fq -- '-v "$profile_dir:/profile:rw"' "$runner"
grep -Fq -- '-e PROFILING_MODE=dynamic' "$runner"
! grep -Eq '/vllm-workspace/(vllm|vllm-ascend)/.*\.py:ro' "$runner"
! grep -Fq -- '-v /cache/austinov:/cache/austinov' "$runner"
grep -Fq -- '-v /cache/austinov/Qwen3.8-27B:/cache/austinov/Qwen3.8-27B:ro' "$runner"
! grep -Eq 'docker[[:space:]]+(commit|cp)([[:space:]]|$)' "$runner"
grep -Fq 'sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1' "$runner"
grep -Fq 'f4c4b30c8e5fb1f27fbfbb8b6ac290b58fb95c7484f5de0e7ee27c545972a6be' "$runner"
grep -Fq 'QWEN35_ASCEND_T21_DENSE_MLP=1' "$runner"
grep -Fq 'QWEN35_ASCEND_T21_DENSE_MLP=0' "$runner"
grep -Fq 'qwen35-t21-public-acl-bridge-20260912-v4' "$runner"
grep -Fq '7c0e01b2b6d4274ead9871c76df5a83cad3618cddec35128ca4e8d12a8c786e4' "$runner"
grep -Fq 'ef99d0382ead18f4ef565fb62b40e679adaa9ee120af56089989430fa5a38afb' "$runner"
grep -Fq 'T21 bridge SHA256 mismatch' "$runner"
grep -Fq 'QWEN35_ASCEND_DIAGNOSTICS:-0' "$runner"
grep -Fq 'QWEN35_ASCEND_DIAGNOSTICS_INTERVAL:-32' "$runner"
grep -Fq 'QWEN35_ASCEND_DIAGNOSTICS="$qwen35_diagnostics"' "$runner"
grep -Fq 'QWEN35_ASCEND_DIAGNOSTICS_INTERVAL="$qwen35_diagnostics_interval"' "$runner"
grep -Fq 'qwen35_gdn_runtime_t12_${variant}_npu03' "$capture"
grep -Fq 'docker logs "$container_name"' "$capture"
grep -Fq -- '--log "$OUTPUT_ROOT/container-logs.live.txt"' "$capture"
grep -Fq 'nohup setsid "$launcher"' "$starter"
grep -Fq 'kill -0 "$supervisor_pid"' "$starter"
grep -Fq 'refusing to reuse supervisor artifacts' "$starter"
! grep -Eq 'docker[[:space:]]+(run|stop|commit|cp)([[:space:]]|$)' "$starter"

probe_root="/cache/austinov/qwen35-profile-contract-probe-$$"
if OUTPUT_ROOT="$probe_root" PROFILE_DIR=/cache/austinov/unexpected-profile bash "$runner" >/dev/null 2>&1; then
  echo 'runner accepted PROFILE_DIR while dynamic profiling was disabled' >&2
  exit 1
fi
if OUTPUT_ROOT="$probe_root" ENABLE_DYNAMIC_PROFILING=2 bash "$runner" >/dev/null 2>&1; then
  echo 'runner accepted invalid ENABLE_DYNAMIC_PROFILING value' >&2
  exit 1
fi
if OUTPUT_ROOT="$probe_root" ENABLE_DYNAMIC_PROFILING=1 PROFILE_DIR=/tmp/qwen35-profile bash "$runner" >/dev/null 2>&1; then
  echo 'runner accepted PROFILE_DIR outside /cache/austinov' >&2
  exit 1
fi
if OUTPUT_ROOT="$probe_root" QWEN35_ASCEND_DIAGNOSTICS=2 bash "$runner" >/dev/null 2>&1; then
  echo 'runner accepted invalid QWEN35_ASCEND_DIAGNOSTICS value' >&2
  exit 1
fi
if OUTPUT_ROOT="$probe_root" QWEN35_ASCEND_DIAGNOSTICS_INTERVAL=0 bash "$runner" >/dev/null 2>&1; then
  echo 'runner accepted invalid QWEN35_ASCEND_DIAGNOSTICS_INTERVAL value' >&2
  exit 1
fi

echo 'PASS: t12 NPU0-3 runtime-only launcher contract'

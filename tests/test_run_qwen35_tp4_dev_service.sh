#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d "$repo_root/tests/.guard-test.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

mock_bin="$tmp/bin"
mkdir -p "$mock_bin"
docker_log="$tmp/docker.log"

cat >"$mock_bin/docker" <<'MOCK'
#!/usr/bin/env bash
if [[ "${1:-}" == container && "${2:-}" == inspect ]]; then
  exit 1
fi
printf '%s\n' "$*" >>"$DOCKER_LOG"
MOCK
chmod +x "$mock_bin/docker"

cat >"$mock_bin/npu-smi" <<'MOCK'
#!/usr/bin/env bash
cat <<'INFO'
| NPU     Chip              | Process id    | Process name             | Process memory(MB)      |
| 4       0                 | 4111982       | VLLMWorker_TP            | 27952                   |
INFO
MOCK
chmod +x "$mock_bin/npu-smi"

set +e
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi"   DEVICE_SET=4-7 CONTAINER_NAME=guard-test-occupied   PROFILE_DIR="$tmp/profile-occupied"   "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" profile   >"$tmp/occupied.out" 2>"$tmp/occupied.err"
rc=$?
set -e
if [[ "$rc" != 42 ]]; then cat "$tmp/occupied.err" >&2; fi
[[ "$rc" == 42 ]]
grep -q "physical NPU4-7 are not idle" "$tmp/occupied.err"
[[ ! -e "$docker_log" ]]

cat >"$mock_bin/npu-smi" <<'MOCK'
#!/usr/bin/env bash
cat <<'INFO'
| NPU     Chip              | Process id    | Process name             | Process memory(MB)      |
INFO
MOCK
chmod +x "$mock_bin/npu-smi"
mkdir "$tmp/profile-existing"

set +e
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi"   CONTAINER_NAME=guard-test-profile-dir   PROFILE_DIR="$tmp/profile-existing"   "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" profile   >"$tmp/profile.out" 2>"$tmp/profile.err"
rc=$?
set -e
if [[ "$rc" != 44 ]]; then cat "$tmp/profile.err" >&2; fi
[[ "$rc" == 44 ]]
grep -q "refusing to reuse profile directory" "$tmp/profile.err"
[[ ! -e "$docker_log" ]]

PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-profile-fresh \
  PROFILE_DIR="$tmp/profile-fresh" \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" profile \
  >"$tmp/profile-fresh.out" 2>"$tmp/profile-fresh.err"
grep -q -- '--profiler-config.profiler torch' "$docker_log"
grep -q -- '--no-async-scheduling' "$docker_log"
if grep -Eq '(^| )--async-scheduling( |$)' "$docker_log"; then
  echo "profile mode unexpectedly enabled async scheduling" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-profile-msprof-mmar-off-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" \
  profile-msprof-mmar-off \
  >"$tmp/profile-msprof-mmar-off-fresh.out" \
  2>"$tmp/profile-msprof-mmar-off-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- 'PROFILING_MODE=dynamic' "$docker_log"
grep -q -- '"enable_matmul_allreduce":false' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=0' "$docker_log"
if grep -q -- '--profiler-config.profiler' "$docker_log"; then
  echo "msprof mode unexpectedly enabled the vLLM torch profiler" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-profile-mmar-off-fresh \
  PROFILE_DIR="$tmp/profile-mmar-off-fresh" \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" profile-mmar-off \
  >"$tmp/profile-mmar-off-fresh.out" 2>"$tmp/profile-mmar-off-fresh.err"
grep -q -- '--profiler-config.profiler torch' "$docker_log"
grep -q -- '--no-async-scheduling' "$docker_log"
grep -q -- '"enable_matmul_allreduce":false' "$docker_log"
grep -q -- '"enable_flashcomm1":false' "$docker_log"
grep -q -- '"weight_nz_mode":1' "$docker_log"
grep -q -- '--tensor-parallel-size 4' "$docker_log"
grep -q -- '--data-parallel-size 1' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=0' "$docker_log"
if grep -Eq '(^| )--async-scheduling( |$)' "$docker_log"; then
  echo "MMAR-off profile mode unexpectedly enabled async scheduling" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-baseline-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" baseline \
  >"$tmp/baseline-fresh.out" 2>"$tmp/baseline-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- '"enable_matmul_allreduce":true' "$docker_log"
grep -q -- '"enable_flashcomm1":false' "$docker_log"
grep -q -- '"weight_nz_mode":1' "$docker_log"
grep -q -- '--cpuset-cpus 0-95' "$docker_log"
grep -q -- '--device /dev/davinci4:/dev/davinci0' "$docker_log"
grep -q -- '--device /dev/davinci5:/dev/davinci1' "$docker_log"
grep -q -- '--device /dev/davinci6:/dev/davinci2' "$docker_log"
grep -q -- '--device /dev/davinci7:/dev/davinci3' "$docker_log"
if grep -q -- '--no-async-scheduling' "$docker_log"; then
  echo "baseline mode unexpectedly disabled async scheduling" >&2
  exit 1
fi
if grep -q -- '--profiler-config.profiler' "$docker_log"; then
  echo "baseline mode unexpectedly enabled profiling" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-control-mmar-off-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" control-mmar-off \
  >"$tmp/control-mmar-off-fresh.out" 2>"$tmp/control-mmar-off-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- '"enable_matmul_allreduce":false' "$docker_log"
grep -q -- '"enable_flashcomm1":false' "$docker_log"
grep -q -- '"weight_nz_mode":1' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=0' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_FLASHCOMM1=0' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_NZ=1' "$docker_log"
if grep -q -- '--quantization' "$docker_log"; then
  echo "control candidate unexpectedly enabled quantization" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-mmar-on-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" mmar-on \
  >"$tmp/mmar-on-fresh.out" 2>"$tmp/mmar-on-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- '"enable_matmul_allreduce":true' "$docker_log"
grep -q -- '"enable_flashcomm1":false' "$docker_log"
grep -q -- '"weight_nz_mode":1' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_FLASHCOMM1=0' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_NZ=1' "$docker_log"
if grep -q -- '--quantization' "$docker_log"; then
  echo "MatMulAllReduce candidate unexpectedly enabled quantization" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-mmar-on-hccl-aiv-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" mmar-on-hccl-aiv \
  >"$tmp/mmar-on-hccl-aiv-fresh.out" 2>"$tmp/mmar-on-hccl-aiv-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- '--tensor-parallel-size 4' "$docker_log"
grep -q -- '--data-parallel-size 1' "$docker_log"
grep -q -- '"enable_matmul_allreduce":true' "$docker_log"
grep -q -- '"enable_flashcomm1":false' "$docker_log"
grep -q -- '"weight_nz_mode":1' "$docker_log"
grep -q -- 'HCCL_OP_EXPANSION_MODE=AIV' "$docker_log"
if grep -q -- '--quantization' "$docker_log"; then
  echo "MMAR HCCL AIV candidate unexpectedly enabled quantization" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-tp2-dp2-mmar-on-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" tp2-dp2-mmar-on \
  >"$tmp/tp2-dp2-mmar-on-fresh.out" 2>"$tmp/tp2-dp2-mmar-on-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- '--tensor-parallel-size 2' "$docker_log"
grep -q -- '--data-parallel-size 2' "$docker_log"
grep -q -- '"enable_matmul_allreduce":true' "$docker_log"
grep -q -- '"enable_flashcomm1":false' "$docker_log"
grep -q -- '"weight_nz_mode":1' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_FLASHCOMM1=0' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_NZ=1' "$docker_log"
if grep -q -- '--quantization' "$docker_log"; then
  echo "TP2 DP2 MMAR candidate unexpectedly enabled quantization" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-tp2-dp2-mmar-on-text-only-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" \
  tp2-dp2-mmar-on-text-only \
  >"$tmp/tp2-dp2-mmar-on-text-only-fresh.out" \
  2>"$tmp/tp2-dp2-mmar-on-text-only-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- '--tensor-parallel-size 2' "$docker_log"
grep -q -- '--data-parallel-size 2' "$docker_log"
grep -q -- '--limit-mm-per-prompt {"image":0,"video":0}' "$docker_log"
grep -q -- '"enable_matmul_allreduce":true' "$docker_log"
grep -q -- '"enable_flashcomm1":false' "$docker_log"
grep -q -- '"weight_nz_mode":1' "$docker_log"
grep -q -- 'HCCL_BUFFSIZE=512' "$docker_log"
if grep -q -- '--quantization' "$docker_log"; then
  echo "TP2 DP2 text-only candidate unexpectedly enabled quantization" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-ngram-gpu-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" ngram-gpu \
  >"$tmp/ngram-gpu-fresh.out" 2>"$tmp/ngram-gpu-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- '"enable_matmul_allreduce":false' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=0' "$docker_log"
grep -q -- '"method":"ngram_gpu"' "$docker_log"
grep -q -- '"num_speculative_tokens":5' "$docker_log"
grep -q -- '"prompt_lookup_min":2' "$docker_log"
grep -q -- '"prompt_lookup_max":5' "$docker_log"
if grep -q -- '--quantization' "$docker_log"; then
  echo "NPU prompt-lookup candidate unexpectedly enabled quantization" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-flashcomm1-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" flashcomm1 \
  >"$tmp/flashcomm1-fresh.out" 2>"$tmp/flashcomm1-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- '"enable_matmul_allreduce":true' "$docker_log"
grep -q -- '"enable_flashcomm1":true' "$docker_log"
if grep -q -- '--profiler-config.profiler' "$docker_log"; then
  echo "flashcomm1 mode unexpectedly enabled profiling" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-bf16-nz-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" bf16-nz \
  >"$tmp/bf16-nz-fresh.out" 2>"$tmp/bf16-nz-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- '"enable_matmul_allreduce":true' "$docker_log"
grep -q -- '"enable_flashcomm1":false' "$docker_log"
grep -q -- '"weight_nz_mode":2' "$docker_log"
if grep -q -- '--profiler-config.profiler' "$docker_log"; then
  echo "bf16-nz mode unexpectedly enabled profiling" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-bf16-nz-mmar-off-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" bf16-nz-mmar-off \
  >"$tmp/bf16-nz-mmar-off-fresh.out" 2>"$tmp/bf16-nz-mmar-off-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- '"enable_matmul_allreduce":false' "$docker_log"
grep -q -- '"enable_flashcomm1":false' "$docker_log"
grep -q -- '"weight_nz_mode":2' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=0' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_FLASHCOMM1=0' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_NZ=2' "$docker_log"
if grep -q -- '--quantization' "$docker_log"; then
  echo "BF16 NZ recovery mode unexpectedly enabled quantization" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-flashcomm1-bf16-nz-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" flashcomm1-bf16-nz \
  >"$tmp/stack-fresh.out" 2>"$tmp/stack-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
grep -q -- '"enable_matmul_allreduce":true' "$docker_log"
grep -q -- '"enable_flashcomm1":true' "$docker_log"
grep -q -- '"weight_nz_mode":2' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_FLASHCOMM1=1' "$docker_log"
grep -q -- 'VLLM_ASCEND_ENABLE_NZ=2' "$docker_log"
if grep -q -- '--profiler-config.profiler' "$docker_log"; then
  echo "cumulative stack unexpectedly enabled profiling" >&2
  exit 1
fi

echo "PASS: run_qwen35_tp4_dev_service guards"

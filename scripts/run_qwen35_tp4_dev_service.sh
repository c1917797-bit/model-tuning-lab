#!/usr/bin/env bash
set -euo pipefail

mode="${1:-}"
case "$mode" in
  baseline|mtp|profile|flashcomm1) ;;
  *)
    echo "usage: $0 {baseline|mtp|profile|flashcomm1}" >&2
    exit 64
    ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
container_name="${CONTAINER_NAME:-qwen35_query_rewrite_tp4_dev_${mode}}"
port="${PORT:-10010}"
profile_dir="${PROFILE_DIR:-/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/profiles/tp4-baseline-v1}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"

if docker container inspect "$container_name" >/dev/null 2>&1; then
  echo "refusing to replace existing container: $container_name" >&2
  exit 41
fi

npu_snapshot="$("$npu_smi_bin" info)"
occupied="$(
  awk -F '|' '
    $2 ~ /^[[:space:]]*[0-3][[:space:]]+[0-9]+[[:space:]]*$/ &&
    $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {
      gsub(/[[:space:]]/, "", $2)
      gsub(/[[:space:]]/, "", $3)
      print "NPU" substr($2, 1, 1) ":pid=" $3
    }
  ' <<<"$npu_snapshot"
)"
if [[ -n "$occupied" ]]; then
  echo "refusing to start: NPU0-3 are not idle" >&2
  echo "$occupied" >&2
  exit 42
fi

serve_args=(
  vllm serve /cache/austinov/Qwen3.8-27B
  --host 127.0.0.1
  --port "$port"
  --tensor-parallel-size 4
  --data-parallel-size 1
  --seed 1024
  --served-model-name Qwen3-5/Qwen3.5-27B
  --max-num-seqs 16
  --max-model-len 133000
  --max-num-batched-tokens 32768
  --trust-remote-code
  --gpu-memory-utilization 0.90
  --enable-prefix-caching
  --mamba-cache-mode align
  --mamba-cache-dtype bfloat16
  --mamba-ssm-cache-dtype bfloat16
  --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,2,4,6,8,10,12,14,16,32,64,128,256,384,512,640,768,896,1024,1280,1536,1792,2048,2304,2560,2816,3072,3328,3456,3584]}'
  --additional-config "$(
    if [[ "$mode" == flashcomm1 ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":true}'
    else
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false}'
    fi
  )"
  --default-chat-template-kwargs '{"enable_thinking":false}'
)

# torch_npu's external profiler callback must be started and stopped from the
# same execution thread. vLLM 0.23.0 async scheduling violates that invariant
# at /stop_profile and cancels the multiprocess response queue. Profiling is
# diagnostic-only, so preserve async scheduling for performance candidates and
# use the synchronous scheduler only for the isolated profiler service.
if [[ "$mode" == profile ]]; then
  # Omitting --async-scheduling is not sufficient in vLLM 0.23.0: the
  # effective default can still enable it.  Force the diagnostic service onto
  # the synchronous scheduler so the profiler lifecycle invariant is testable.
  serve_args+=(--no-async-scheduling)
else
  serve_args+=(--async-scheduling)
fi

if [[ "$mode" == mtp ]]; then
  serve_args+=(--speculative-config '{"method":"mtp","num_speculative_tokens":1}')
fi

if [[ "$mode" == profile ]]; then
  if [[ -e "$profile_dir" ]]; then
    echo "refusing to reuse profile directory: $profile_dir" >&2
    exit 44
  fi
  mkdir -p "$profile_dir"
  serve_args+=(
    --profiler-config.profiler torch
    --profiler-config.torch_profiler_dir "$profile_dir"
  )
fi

docker_args=(
  run -d
  --name "$container_name"
  --network host
  --cpuset-cpus 96-191
  --device /dev/davinci0
  --device /dev/davinci1
  --device /dev/davinci2
  --device /dev/davinci3
  --device /dev/davinci_manager
  --device /dev/devmm_svm
  --device /dev/hisi_hdc
  -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info
  -v /etc/ascend_install.info:/etc/ascend_install.info
  -v /usr/local/dcmi:/usr/local/dcmi
  -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi
  -v /cache/austinov:/cache/austinov
  -v /cache/cch:/cache/cch:ro
  -v "$repo_root":/experiment:ro
  -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3
  -e HCCL_BUFFSIZE=512
  -e OMP_PROC_BIND=false
  -e OMP_NUM_THREADS=1
  -e TASK_QUEUE_ENABLE=1
  -e TRITON_KERNEL_DUMP=1
  -e TRITON_DUMP_DIR=/cache/efim/triton_dump
  -e VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1
  -e VLLM_ASCEND_ENABLE_FLASHCOMM1=0
  -e VLLM_ASCEND_PTO_CHUNK_GDN=1
  -e VLLM_LOGGING_LEVEL=DEBUG
)

docker "${docker_args[@]}" quay.io/ascend/vllm-ascend:v0.23.0 "${serve_args[@]}"

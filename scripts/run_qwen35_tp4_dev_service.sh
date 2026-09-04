#!/usr/bin/env bash
set -euo pipefail

mode="${1:-}"
case "$mode" in
  baseline|mtp|ngram-gpu|profile|profile-mmar-off|profile-msprof-mmar-off|profile-msprof-mmar-on|control-mmar-off|mmar-on|flashcomm1|bf16-nz|bf16-nz-mmar-off|flashcomm1-bf16-nz|selective-ffn-nz) ;;
  *)
    echo "usage: $0 {baseline|mtp|ngram-gpu|profile|profile-mmar-off|profile-msprof-mmar-off|profile-msprof-mmar-on|control-mmar-off|mmar-on|flashcomm1|bf16-nz|bf16-nz-mmar-off|flashcomm1-bf16-nz|selective-ffn-nz}" >&2
    exit 64
    ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
device_set="${DEVICE_SET:-4-7}"
case "$device_set" in
  0-3)
    physical_npus=(0 1 2 3)
    physical_npu_csv="0,1,2,3"
    cpuset_cpus="96-191"
    ;;
  4-7)
    physical_npus=(4 5 6 7)
    physical_npu_csv="4,5,6,7"
    cpuset_cpus="0-95"
    ;;
  *)
    echo "DEVICE_SET must be 0-3 or 4-7" >&2
    exit 64
    ;;
esac
device_tag="${device_set//-/_}"
container_name="${CONTAINER_NAME:-qwen35_query_rewrite_tp4_dev_${mode}_$device_tag}"
port="${PORT:-10010}"
profile_dir="${PROFILE_DIR:-/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/profiles/tp4-baseline-v1}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
selective_ffn_nz_root="${SELECTIVE_FFN_NZ_ROOT:-/cache/cch/.worktrees/exp-20260904-qwen35-selective-ffn-nz}"
selective_ffn_nz_commit="71c25ec9"
flashcomm1_env=0
weight_nz_env=1
matmul_allreduce_env=1
selective_ffn_nz_env=0
if [[ "$mode" == flashcomm1 || "$mode" == flashcomm1-bf16-nz ]]; then
  flashcomm1_env=1
fi
if [[ "$mode" == bf16-nz || "$mode" == bf16-nz-mmar-off ||
      "$mode" == flashcomm1-bf16-nz ]]; then
  weight_nz_env=2
fi
if [[ "$mode" == profile-mmar-off || "$mode" == profile-msprof-mmar-off ||
      "$mode" == control-mmar-off || "$mode" == ngram-gpu ||
      "$mode" == bf16-nz-mmar-off ]]; then
  matmul_allreduce_env=0
fi
if [[ "$mode" == selective-ffn-nz ]]; then
  if [[ "$device_set" != 4-7 ]]; then
    echo "selective-ffn-nz is restricted to physical NPU4-7" >&2
    exit 43
  fi
  actual_ref="$(
    git -c safe.directory="$selective_ffn_nz_root" -C "$selective_ffn_nz_root" rev-parse --short=8 HEAD
  )"
  if [[ "$actual_ref" != "$selective_ffn_nz_commit" ]]; then
    echo "selective FFN NZ source must be $selective_ffn_nz_commit, got $actual_ref" >&2
    exit 45
  fi
  selective_ffn_nz_env=1
fi

if docker container inspect "$container_name" >/dev/null 2>&1; then
  echo "refusing to replace existing container: $container_name" >&2
  exit 41
fi

npu_snapshot="$("$npu_smi_bin" info)"
occupied="$(
  awk -F '|' -v wanted="$physical_npu_csv" '
    BEGIN {
      split(wanted, ids, ",")
      for (item in ids) {
        selected[ids[item]] = 1
      }
    }
    $2 ~ /^[[:space:]]*[0-7][[:space:]]+[0-9]+[[:space:]]*$/ &&
    $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {
      gsub(/[[:space:]]/, "", $2)
      gsub(/[[:space:]]/, "", $3)
      npu = substr($2, 1, 1)
      if (selected[npu]) {
        print "NPU" npu ":pid=" $3
      }
    }
  ' <<<"$npu_snapshot"
)"
if [[ -n "$occupied" ]]; then
  echo "refusing to start: physical NPU$device_set are not idle" >&2
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
    if [[ "$mode" == flashcomm1-bf16-nz ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":true,"weight_nz_mode":2}'
    elif [[ "$mode" == flashcomm1 ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":true}'
    elif [[ "$mode" == profile-mmar-off ||
            "$mode" == profile-msprof-mmar-off ||
            "$mode" == control-mmar-off ||
            "$mode" == ngram-gpu ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":false,"enable_flashcomm1":false,"weight_nz_mode":1}'
    elif [[ "$mode" == bf16-nz-mmar-off ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":false,"enable_flashcomm1":false,"weight_nz_mode":2}'
    elif [[ "$mode" == bf16-nz ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":2}'
    else
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":1}'
    fi
  )"
  --default-chat-template-kwargs '{"enable_thinking":false}'
)

# torch_npu's external profiler callback must be started and stopped from the
# same execution thread. vLLM 0.23.0 async scheduling violates that invariant
# at /stop_profile and cancels the multiprocess response queue. Profiling is
# diagnostic-only, so preserve async scheduling for performance candidates and
# use the synchronous scheduler only for the isolated profiler service.
if [[ "$mode" == profile || "$mode" == profile-mmar-off ]]; then
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
if [[ "$mode" == ngram-gpu ]]; then
  # Prompt Lookup Decoding is training-free and lossless under target-model
  # verification. Keep proposal generation on NPU so async scheduling remains
  # enabled and the CPU proposer does not become a host-side bottleneck.
  serve_args+=(--speculative-config '{"method":"ngram_gpu","num_speculative_tokens":5,"prompt_lookup_min":2,"prompt_lookup_max":5}')
fi

if [[ "$mode" == profile || "$mode" == profile-mmar-off ]]; then
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

device_args=()
for index in "${!physical_npus[@]}"; do
  physical_id="${physical_npus[$index]}"
  device_args+=(--device "/dev/davinci$physical_id:/dev/davinci$index")
done

docker_args=(
  run -d
  --name "$container_name"
  --network host
  --cpuset-cpus "$cpuset_cpus"
  "${device_args[@]}"
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
  -e VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE="$matmul_allreduce_env"
  -e VLLM_ASCEND_ENABLE_FLASHCOMM1="$flashcomm1_env"
  -e VLLM_ASCEND_ENABLE_NZ="$weight_nz_env"
  -e VLLM_ASCEND_ENABLE_DENSE_FFN_NZ="$selective_ffn_nz_env"
  -e VLLM_ASCEND_PTO_CHUNK_GDN=1
  -e VLLM_LOGGING_LEVEL=DEBUG
)

if [[ "$mode" == selective-ffn-nz ]]; then
  image_source_root=/vllm-workspace/vllm-ascend/vllm_ascend
  docker_args+=(
    -v "$selective_ffn_nz_root/vllm_ascend/envs.py:$image_source_root/envs.py:ro"
    -v "$selective_ffn_nz_root/vllm_ascend/utils.py:$image_source_root/utils.py:ro"
    -v "$selective_ffn_nz_root/vllm_ascend/ops/linear.py:$image_source_root/ops/linear.py:ro"
  )
fi

if [[ "$mode" == profile-msprof-mmar-off ||
      "$mode" == profile-msprof-mmar-on ]]; then
  # CANN dynamic attach is initialized with the application, then msprof
  # controls the bounded collection window by worker PID. This avoids vLLM
  # 0.23.0's broken lazy torch-profiler initialization on a different thread.
  # The on mode intentionally falls through the normal MMAR-enabled config.
  docker_args+=(-e PROFILING_MODE=dynamic)
fi

docker "${docker_args[@]}" quay.io/ascend/vllm-ascend:v0.23.0 "${serve_args[@]}"

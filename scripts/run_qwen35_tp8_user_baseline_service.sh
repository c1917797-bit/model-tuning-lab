#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
container_name="${CONTAINER_NAME:?set an immutable CONTAINER_NAME}"
port="${PORT:-10010}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
runtime_role="${RUNTIME_ROLE:-baseline}"
mtp_local_argmax_root="${MTP_LOCAL_ARGMAX_ROOT:-/cache/cch/.worktrees/exp-20260905-qwen35-mtp-local-argmax}"
mtp_local_argmax_commit="${MTP_LOCAL_ARGMAX_COMMIT:-37d32edf5a2626b4b6b1c6ed57fcad8d3ed9c8cd}"
mtp_num_speculative_tokens="${MTP_NUM_SPECULATIVE_TOKENS:-1}"

case "$runtime_role" in
  baseline|mtp-local-argmax|tp4-dp2|tp4-dp2-mtp-local-argmax) ;;
  *) echo "unsupported RUNTIME_ROLE: $runtime_role" >&2; exit 64 ;;
esac

uses_mtp=false
tensor_parallel_size=8
data_parallel_size=1
if [[ "$runtime_role" == tp4-dp2* ]]; then
  tensor_parallel_size=4
  data_parallel_size=2
fi
if [[ "$runtime_role" == *mtp-local-argmax ]]; then
  uses_mtp=true
  if [[ ! "$mtp_num_speculative_tokens" =~ ^[1-9][0-9]*$ ]]; then
    echo "MTP_NUM_SPECULATIVE_TOKENS must be a positive integer" >&2
    exit 65
  fi
  actual_ref="$(
    git -c safe.directory="$mtp_local_argmax_root" \
      -C "$mtp_local_argmax_root" rev-parse HEAD
  )"
  if [[ "$actual_ref" != "$mtp_local_argmax_commit" ]]; then
    echo "Qwen3.5 MTP local-argmax source must be $mtp_local_argmax_commit, got $actual_ref" >&2
    exit 45
  fi
  mtp_patch="$mtp_local_argmax_root/vllm_ascend/patch/worker/patch_qwen3_5.py"
  proposer_patch="$mtp_local_argmax_root/vllm_ascend/spec_decode/llm_base_proposer.py"
  if [[ ! -f "$mtp_patch" ]]; then
    echo "Qwen3.5 MTP local-argmax patch is missing: $mtp_patch" >&2
    exit 46
  fi
  if [[ ! -f "$proposer_patch" ]]; then
    echo "Ascend proposer local-argmax patch is missing: $proposer_patch" >&2
    exit 47
  fi
fi

if docker container inspect "$container_name" >/dev/null 2>&1; then
  echo "refusing to replace existing container: $container_name" >&2
  exit 41
fi

reservation_ignore_names="${NPU_RESERVATION_IGNORE_NAMES-/vllm-ep-310p-research-910b-monitor,/vllm-19.1-Qwen3.5-4B-1065}"
container_reservations="$(
  for running_id in $(docker ps -q); do
    docker inspect --format '{{.Name}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}' "$running_id"
  done | awk -v ignored_csv="$reservation_ignore_names" '
    BEGIN {
      split(ignored_csv, ignored_names, ",")
      for (item in ignored_names) ignored[ignored_names[item]] = 1
    }
    $0 ~ /\/dev\/davinci[0-7]([[:space:]]|$)/ && !($1 in ignored)
  '
)"
if [[ -n "$container_reservations" ]]; then
  echo "refusing to start: a running container reserves physical NPU0-7" >&2
  echo "$container_reservations" >&2
  exit 48
fi

npu_snapshot="$("$npu_smi_bin" info)"
occupied="$(
  awk -F '|' '
    $2 ~ /^[[:space:]]*[0-7][[:space:]]+[0-9]+[[:space:]]*$/ &&
    $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {
      gsub(/[[:space:]]/, "", $2)
      gsub(/[[:space:]]/, "", $3)
      print "NPU" substr($2, 1, 1) ":pid=" $3
    }
  ' <<<"$npu_snapshot"
)"
if [[ -n "$occupied" ]]; then
  echo "refusing to start: physical NPU0-7 are not idle" >&2
  echo "$occupied" >&2
  exit 42
fi
if ss -ltn | awk '{print $4}' | grep -Eq ":${port}$"; then
  echo "refusing to start: port $port is already listening" >&2
  exit 49
fi

device_args=()
for physical_id in 0 1 2 3 4 5 6 7; do
  device_args+=(--device "/dev/davinci$physical_id:/dev/davinci$physical_id")
done

serve_args=(
  vllm serve /cache/austinov/Qwen3.8-27B
  --host 127.0.0.1
  --port "$port"
  --tensor-parallel-size "$tensor_parallel_size"
  --pipeline-parallel-size 1
  --data-parallel-size "$data_parallel_size"
  --seed 1024
  --served-model-name Qwen3-5/Qwen3.5-27B
  --max-num-seqs 16
  --max-model-len 133000
  --max-num-batched-tokens 32768
  --trust-remote-code
  --gpu-memory-utilization 0.90
  --enable-prefix-caching
  --enable-chunked-prefill
  --mamba-cache-mode align
  --mamba-cache-dtype bfloat16
  --mamba-ssm-cache-dtype bfloat16
  --disable-custom-all-reduce
  --compilation-config '{"mode":3,"custom_ops":["all"],"ir_enable_torch_wrap":false,"splitting_ops":[],"compile_sizes":[],"compile_ranges_endpoints":[8096],"inductor_compile_config":{"enable_auto_functionalized_v2":false,"size_asserts":false,"alignment_asserts":false,"scalar_asserts":false,"combo_kernels":true,"benchmark_combo_kernel":true},"inductor_passes":{},"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_num_of_warmups":1,"cudagraph_capture_sizes":[1,2,4,8,16,24,32],"use_inductor_graph_partition":false,"pass_config":{"fuse_norm_quant":true,"fuse_act_quant":true,"fuse_attn_quant":false,"enable_sp":false,"fuse_gemm_comms":false,"fuse_allreduce_rms":false,"fuse_rope_kvcache_cat_mla":false,"fuse_act_padding":false},"max_cudagraph_capture_size":32,"dynamic_shapes_config":{"type":"backed","evaluate_guards":false,"assume_32_bit_indexing":false},"fast_moe_cold_start":true}'
  --additional-config '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false}'
  --default-chat-template-kwargs '{"enable_thinking":false}'
  --async-scheduling
)

runtime_mount_args=()
if [[ "$uses_mtp" == true ]]; then
  serve_args+=(--speculative-config "{\"method\":\"mtp\",\"num_speculative_tokens\":$mtp_num_speculative_tokens,\"use_local_argmax_reduction\":true}")
  runtime_mount_args+=(
    -v "$mtp_patch:/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py:ro"
    -v "$proposer_patch:/vllm-workspace/vllm-ascend/vllm_ascend/spec_decode/llm_base_proposer.py:ro"
  )
fi

docker run -d \
  --name "$container_name" \
  --network host \
  --cpuset-cpus 0-191 \
  "${device_args[@]}" \
  --device /dev/davinci_manager \
  --device /dev/devmm_svm \
  --device /dev/hisi_hdc \
  -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64 \
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info \
  -v /etc/ascend_install.info:/etc/ascend_install.info \
  -v /usr/local/dcmi:/usr/local/dcmi \
  -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
  -v /cache/austinov:/cache/austinov \
  -v /cache/cch:/cache/cch:ro \
  -v "$repo_root":/experiment:ro \
  "${runtime_mount_args[@]}" \
  -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
  -e HCCL_BUFFSIZE=512 \
  -e OMP_PROC_BIND=false \
  -e OMP_NUM_THREADS=1 \
  -e TASK_QUEUE_ENABLE=1 \
  -e TRITON_KERNEL_DUMP=1 \
  -e TRITON_DUMP_DIR=/cache/efim/triton_dump \
  -e VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1 \
  -e VLLM_ASCEND_ENABLE_FLASHCOMM1=0 \
  -e VLLM_LOGGING_LEVEL=DEBUG \
  quay.io/ascend/vllm-ascend:v0.23.0 \
  "${serve_args[@]}"

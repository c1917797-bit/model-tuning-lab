#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
container_name="${CONTAINER_NAME:?set an immutable CONTAINER_NAME}"
port="${PORT:-10010}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"

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
  --tensor-parallel-size 8
  --pipeline-parallel-size 1
  --data-parallel-size 1
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

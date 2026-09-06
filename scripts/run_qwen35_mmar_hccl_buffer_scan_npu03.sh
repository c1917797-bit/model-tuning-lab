#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_root="${OUTPUT_ROOT:?set OUTPUT_ROOT to a new absolute directory}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
buffers="${HCCL_BUFFER_VALUES:-64 128 256 512}"

case "$output_root" in
  /*) ;;
  *) echo "OUTPUT_ROOT must be absolute" >&2; exit 64 ;;
esac
if [[ -e "$output_root" ]]; then
  echo "refusing to reuse immutable output root: $output_root" >&2
  exit 44
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
  echo "refusing to start: physical NPU0-3 are not idle" >&2
  echo "$occupied" >&2
  exit 42
fi

mkdir -p "$output_root"
for buffer in $buffers; do
  [[ "$buffer" =~ ^[0-9]+$ ]] || {
    echo "invalid HCCL buffer value: $buffer" >&2
    exit 64
  }
  container_name="qwen35_mmar_hccl_buff${buffer}_npu03"
  if docker container inspect "$container_name" >/dev/null 2>&1; then
    echo "refusing to replace existing container: $container_name" >&2
    exit 41
  fi
  docker run --name "$container_name" --network host --cpuset-cpus 0-95 \
    --device /dev/davinci0 \
    --device /dev/davinci1 \
    --device /dev/davinci2 \
    --device /dev/davinci3 \
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
    -v "$repo_root":/experiment:ro \
    -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 \
    -e HCCL_BUFFSIZE="$buffer" \
    -e OMP_PROC_BIND=false \
    -e OMP_NUM_THREADS=1 \
    -e TASK_QUEUE_ENABLE=1 \
    quay.io/ascend/vllm-ascend:v0.23.0 \
    python3 /experiment/scripts/benchmark_qwen35_mmar_hccl_buffer.py \
      --output "$output_root/buff${buffer}.json" \
      --master-port "$((29711 + buffer))"
  docker logs "$container_name" >"$output_root/buff${buffer}.log" 2>&1 || true
  docker rm "$container_name" >/dev/null
done

sha256sum "$output_root"/*.json "$output_root"/*.log >"$output_root/SHA256SUMS"
echo "completed HCCL buffer scan: $output_root"

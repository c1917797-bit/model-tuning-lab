#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_root="${OUTPUT_ROOT:?set OUTPUT_ROOT to a new absolute directory}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
container_name="${CONTAINER_NAME:-qwen35_mmar_policy_microbench_npu4_7}"

case "$output_root" in
  /*) ;;
  *) echo "OUTPUT_ROOT must be absolute" >&2; exit 64 ;;
esac
if [[ -e "$output_root" ]]; then
  echo "refusing to reuse immutable output root: $output_root" >&2
  exit 44
fi
if docker container inspect "$container_name" >/dev/null 2>&1; then
  echo "refusing to replace existing container: $container_name" >&2
  exit 41
fi

npu_snapshot="$("$npu_smi_bin" info)"
occupied="$(
  awk -F '|' '
    $2 ~ /^[[:space:]]*[4-7][[:space:]]+[0-9]+[[:space:]]*$/ &&
    $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {
      gsub(/[[:space:]]/, "", $2)
      gsub(/[[:space:]]/, "", $3)
      print "NPU" substr($2, 1, 1) ":pid=" $3
    }
  ' <<<"$npu_snapshot"
)"
if [[ -n "$occupied" ]]; then
  echo "refusing to start: physical NPU4-7 are not idle" >&2
  echo "$occupied" >&2
  exit 42
fi

mkdir -p "$output_root"
cleanup() {
  local status=$?
  if docker container inspect "$container_name" >/dev/null 2>&1; then
    docker logs "$container_name" >"$output_root/container.log" 2>&1 || true
    docker rm -f "$container_name" >/dev/null 2>&1 || true
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

docker run --name "$container_name" --network host --cpuset-cpus 0-95 \
  --device /dev/davinci4:/dev/davinci0 \
  --device /dev/davinci5:/dev/davinci1 \
  --device /dev/davinci6:/dev/davinci2 \
  --device /dev/davinci7:/dev/davinci3 \
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
  -e HCCL_BUFFSIZE=512 \
  -e OMP_PROC_BIND=false \
  -e OMP_NUM_THREADS=1 \
  -e TASK_QUEUE_ENABLE=1 \
  quay.io/ascend/vllm-ascend:v0.23.0 \
  python3 /experiment/scripts/benchmark_qwen35_mmar_policy.py \
    --output "$output_root/result.json"

docker logs "$container_name" >"$output_root/container.log" 2>&1 || true
docker rm "$container_name" >/dev/null
sha256sum "$output_root/result.json" "$output_root/container.log" \
  >"$output_root/SHA256SUMS"
trap - EXIT INT TERM
echo "completed MMAR policy microbenchmark: $output_root"

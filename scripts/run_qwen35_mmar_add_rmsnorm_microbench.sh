#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_root="${OUTPUT_ROOT:?set OUTPUT_ROOT to a new absolute directory}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
container_name="${CONTAINER_NAME:-qwen35_mmar_add_rmsnorm_microbench_npu4_7}"
source_root="${CUSTOM_VLLM_ASCEND_ROOT:-/cache/cch/.worktrees/exp-20260905-qwen35-mmar-add-rmsnorm-vllm}"
source_commit="4cc7cd7fb03b796fcd090a373b9c087f5ace8de5"
build_root="$source_root/build-mmar-add-rmsnorm"
custom_extension="$build_root/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
custom_kernels="$build_root/lib/libvllm_ascend_kernels.so"
custom_extension_sha256="6006e113bf7f52ba5561d9847dbdcc6960b89eff56228d5ab584344719347d23"
custom_kernels_sha256="6a9fc72a66a6055eb522a251fa48632b0ba257f22fb8f91a2deedc05e03e8b6a"

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

# npu-smi can briefly report no device process while another container is
# starting its runtime. Treat any running container with a matching device
# reservation as occupied before checking the process table. The two exact
# names below are long-lived, operator-verified monitor/admin shells: they only
# mount device files and have no NPU runtime process. An explicit empty override
# disables this host-local allowlist.
reservation_ignore_names="${NPU_RESERVATION_IGNORE_NAMES-/vllm-ep-310p-research-910b-monitor,/vllm-19.1-Qwen3.5-4B-1065}"
container_reservations="$(
  for running_id in $(docker ps -q); do
    docker inspect "$running_id" --format \
      '{{.Name}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}'
  done | awk -v ignored_csv="$reservation_ignore_names" '
    BEGIN {
      split(ignored_csv, ignored_names, ",")
      for (item in ignored_names) {
        ignored[ignored_names[item]] = 1
      }
    }
    $0 ~ /\/dev\/davinci[4-7]([[:space:]]|$)/ && !($1 in ignored)
  '
)"
if [[ -n "$container_reservations" ]]; then
  echo "refusing to start: a running container reserves physical NPU4-7" >&2
  echo "$container_reservations" >&2
  exit 48
fi

actual_commit="$(git -c safe.directory="$source_root" -C "$source_root" rev-parse HEAD)"
if [[ "$actual_commit" != "$source_commit" ]]; then
  echo "custom vLLM-Ascend source must be $source_commit, got $actual_commit" >&2
  exit 45
fi
for artifact in "$custom_extension" "$custom_kernels"; do
  if [[ ! -f "$artifact" ]]; then
    echo "missing custom build artifact: $artifact" >&2
    exit 46
  fi
done
actual_extension_sha256="$(sha256sum "$custom_extension" | awk '{print $1}')"
actual_kernels_sha256="$(sha256sum "$custom_kernels" | awk '{print $1}')"
if [[ "$actual_extension_sha256" != "$custom_extension_sha256" ]]; then
  echo "custom extension hash mismatch" >&2
  exit 47
fi
if [[ "$actual_kernels_sha256" != "$custom_kernels_sha256" ]]; then
  echo "custom kernels hash mismatch" >&2
  exit 47
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
  -v "$custom_extension":/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so:ro \
  -v "$custom_kernels":/vllm-workspace/vllm-ascend/vllm_ascend/lib/libvllm_ascend_kernels.so:ro \
  -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 \
  -e HCCL_BUFFSIZE=512 \
  -e OMP_PROC_BIND=false \
  -e OMP_NUM_THREADS=1 \
  -e TASK_QUEUE_ENABLE=1 \
  -e VLLM_ASCEND_CUSTOM_EXTENSION_COMMIT="$source_commit" \
  quay.io/ascend/vllm-ascend:v0.23.0 \
  python3 /experiment/scripts/benchmark_qwen35_mmar_add_rmsnorm.py \
    --output "$output_root/result.json"

docker logs "$container_name" >"$output_root/container.log" 2>&1 || true
docker rm "$container_name" >/dev/null
sha256sum "$output_root/result.json" "$output_root/container.log" \
  >"$output_root/SHA256SUMS"
trap - EXIT INT TERM
echo "completed MMAR+Add+RMSNorm microbenchmark: $output_root"

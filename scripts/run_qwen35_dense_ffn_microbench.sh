#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
physical_npu=4
logical_npu=0
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
container_name="${CONTAINER_NAME:-qwen35_dense_ffn_microbench_npu4}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_dir="${OUTPUT_DIR:-/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/ffn-bf16-layout-$timestamp}"
model_dir="${MODEL_DIR:-/cache/austinov/Qwen3.8-27B}"
started=0

cleanup() {
  if [[ "$started" == 1 ]]; then
    docker stop "$container_name" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

if docker container inspect "$container_name" >/dev/null 2>&1; then
  echo "refusing to replace existing container: $container_name" >&2
  exit 41
fi

npu_snapshot="$("$npu_smi_bin" info)"
occupied="$(
  awk -F '|' -v wanted="$physical_npu" '
    $2 ~ /^[[:space:]]*[0-7][[:space:]]+[0-9]+[[:space:]]*$/ &&
    $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {
      gsub(/[[:space:]]/, "", $2)
      gsub(/[[:space:]]/, "", $3)
      npu = substr($2, 1, 1)
      if (npu == wanted) {
        print "NPU" npu ":pid=" $3
      }
    }
  ' <<<"$npu_snapshot"
)"
if [[ -n "$occupied" ]]; then
  echo "refusing to start: physical NPU4 is not idle" >&2
  echo "$occupied" >&2
  exit 42
fi

if [[ -e "$output_dir" ]]; then
  echo "refusing to reuse output directory: $output_dir" >&2
  exit 44
fi
mkdir -p "$output_dir"

printf '%s\n' \
  "physical_npu=4" \
  "container_visible_npu=0" \
  "forbidden_physical_npus=0,1,2,3" \
  "captured_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  >"$output_dir/resource-boundary.txt"

docker_args=(
  run --rm
  --name "$container_name"
  --network host
  --cpuset-cpus 0-23
  --device /dev/davinci4:/dev/davinci0
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
  -v "$repo_root":/experiment:ro
  -e ASCEND_RT_VISIBLE_DEVICES="$logical_npu"
  -e OMP_PROC_BIND=false
  -e OMP_NUM_THREADS=1
  -e TASK_QUEUE_ENABLE=1
  quay.io/ascend/vllm-ascend:v0.23.0
  python /experiment/scripts/benchmark_qwen35_dense_ffn_ops.py
  --model-dir "$model_dir"
  --output "$output_dir/report.json"
  --m-values "${M_VALUES:-1,5,8,16}"
  --warmup "${WARMUP:-20}"
  --iterations "${ITERATIONS:-100}"
  --repeats "${REPEATS:-5}"
)

started=1
set +e
docker "${docker_args[@]}" >"$output_dir/stdout.log" 2>"$output_dir/stderr.log"
rc=$?
set -e
started=0

if compgen -G "$output_dir/*.json" >/dev/null; then
  sha256sum "$output_dir"/*.json >"$output_dir/SHA256SUMS"
fi
printf '%s\n' "$rc" >"$output_dir/exit-code.txt"
if [[ "$rc" != 0 ]]; then
  echo "FFN microbenchmark failed with exit code $rc; artifacts: $output_dir" >&2
  exit "$rc"
fi

echo "$output_dir"

#!/usr/bin/env bash
set -euo pipefail

image="${IMAGE:-quay.io/ascend/vllm-ascend:v0.23.0}"
repo_root="${REPO_ROOT:-/opt/host/vnf/austinov/worktrees/qwen35-performance-delivery}"
lease_file="${LEASE_FILE:-/cache/austinov/.locks/npu0-3.lock}"
lease_wait_seconds="${LEASE_WAIT_SECONDS:-45}"
run_timeout_seconds="${RUN_TIMEOUT_SECONDS:-1800}"
cases="${CASES:-64;257;1807}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_root="${OUTPUT_ROOT:-/cache/austinov/qwen35-fused-prefill-numerical-$timestamp}"
container_name="${CONTAINER_NAME:-qwen35_fused_prefill_numerical_npu0}"
checker="$repo_root/qwen35-performance-optimization/scripts/check_qwen35_fused_prefill_numerical_npu0.py"

for path in "$repo_root" "$checker"; do
  [[ -e "$path" ]] || { echo "required path is missing: $path" >&2; exit 64; }
done
[[ "$image" == "quay.io/ascend/vllm-ascend:v0.23.0" ]] || {
  echo "numerical gate requires the unchanged official v0.23.0 image" >&2
  exit 64
}
[[ ! -e "$output_root" ]] || {
  echo "refusing to reuse output root: $output_root" >&2
  exit 44
}
! docker container inspect "$container_name" >/dev/null 2>&1 || {
  echo "refusing to reuse existing container: $container_name" >&2
  exit 41
}

mkdir -p "$(dirname "$lease_file")"
exec 9>"$lease_file"
flock -w "$lease_wait_seconds" 9 || {
  echo "NPU0-3 lease unavailable after bounded wait" >&2
  exit 46
}

snapshot="$(npu-smi info)"
occupied="$(awk -F '|' '$2 ~ /^[[:space:]]*[0-3][[:space:]]+[0-9]+[[:space:]]*$/ && $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {print $3}' <<<"$snapshot")"
[[ -z "$occupied" ]] || {
  echo "physical NPU0-3 are occupied" >&2
  exit 42
}

mkdir -p "$output_root"
npu-smi info >"$output_root/npu-before.txt"
docker ps --no-trunc >"$output_root/docker-before.txt"
{
  echo "scope=Qwen3.5-27B-GDN-fused-prefill-BF16-numerical-equivalence"
  echo "image=$image"
  echo "image_id=$(docker image inspect --format '{{.Id}}' "$image")"
  echo "container_policy=one-shot --rm; network none; no image mutation"
  echo "device_policy=physical NPU0 only; physical NPU1-7 are not mapped"
  echo "reference=installed v0.23 Triton chunk_gated_delta_rule"
  echo "candidate=installed torch_npu.npu_chunk_gated_delta_rule"
  echo "qwen_shape=TP4 local Nk=4 Nv=12 Dk=Dv=128"
  echo "cases=$cases"
  echo "checker_sha256=$(sha256sum "$checker" | awk '{print $1}')"
  echo "protocol_commit=$(git -C "$repo_root" rev-parse HEAD)"
} >"$output_root/provenance.txt"

docker_args=(
  run --rm --name "$container_name"
  --label com.model-tuning-lab.owner=qwen35-fused-prefill-numerical
  --label "com.model-tuning-lab.output_root=$output_root"
  --network none
  --device /dev/davinci0
  --device /dev/davinci_manager
  --device /dev/devmm_svm
  --device /dev/hisi_hdc
  -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64:ro
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info:ro
  -v /etc/ascend_install.info:/etc/ascend_install.info:ro
  -v /usr/local/dcmi:/usr/local/dcmi:ro
  -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool:ro
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro
  -v "$repo_root":/experiment:ro
  -e ASCEND_RT_VISIBLE_DEVICES=0
  "$image" bash -lc
)

set +e
timeout --signal=TERM --kill-after=30s "${run_timeout_seconds}s" docker "${docker_args[@]}" '
  set -euo pipefail
  source /usr/local/Ascend/cann-9.1.0/set_env.sh
  python3 /experiment/qwen35-performance-optimization/scripts/check_qwen35_fused_prefill_numerical_npu0.py --cases "$1"
' numerical-gate "$cases" >"$output_root/run.log" 2>&1
run_rc=$?
set -e

npu-smi info >"$output_root/npu-after.txt"
docker ps --no-trunc >"$output_root/docker-after.txt"
printf '%s\n' "$run_rc" >"$output_root/exit-code.txt"
if [[ "$run_rc" -ne 0 ]]; then
  cat "$output_root/run.log" >&2
  echo "fused-prefill numerical gate failed; evidence: $output_root" >&2
  exit "$run_rc"
fi

grep '"schema": "qwen35-fused-prefill-numerical/v1"' "$output_root/run.log"
grep -q '"passed": true' "$output_root/run.log"
echo "PASS: Qwen3.5 fused-prefill numerical equivalence"
echo "evidence=$output_root"

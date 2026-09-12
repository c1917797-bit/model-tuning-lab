#!/usr/bin/env bash
set -euo pipefail

# Device admission smoke for the upstream SwigluGatedMlp ACLNN package.
# This is integration evidence only. It does not establish BF16 numerical
# equivalence, Qwen3.5 shape coverage, or end-to-end performance.

image="${IMAGE:-quay.io/ascend/vllm-ascend:v0.23.0}"
repo_root="${REPO_ROOT:-/opt/host/vnf/austinov/worktrees/qwen35-performance-delivery}"
operator_root="${OPERATOR_ROOT:-/cache/austinov/worktrees/exp-20260911-qwen35-t21-abi-adapter}"
candidate_opp_root="${CANDIDATE_OPP_ROOT:-/cache/austinov/qwen35-t21-abi-adapter-opp-r2-20260911}"
lease_file="${LEASE_FILE:-/cache/austinov/.locks/npu0-3.lock}"
lease_wait_seconds="${LEASE_WAIT_SECONDS:-45}"
run_timeout_seconds="${RUN_TIMEOUT_SECONDS:-180}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_root="${OUTPUT_ROOT:-/cache/austinov/qwen35-t21-upstream-float-smoke-$timestamp}"
container_name="${CONTAINER_NAME:-qwen35_t21_upstream_float_smoke_npu0}"

example_relative="experimental/ffn/swiglu_gated_mlp/examples/test_aclnn_swiglu_gated_mlp.cpp"
vendor_relative="vendors/qwen35_t21_v910_transformer"
example_path="$operator_root/$example_relative"
vendor_path="$candidate_opp_root/$vendor_relative"
custom_library="$vendor_path/op_api/lib/libcust_opapi.so"

for path in "$repo_root" "$operator_root" "$candidate_opp_root" "$example_path" "$vendor_path" "$custom_library"; do
  [[ -e "$path" ]] || { echo "required path is missing: $path" >&2; exit 64; }
done
[[ "$lease_wait_seconds" =~ ^[0-9]+$ ]] || { echo "LEASE_WAIT_SECONDS must be an integer" >&2; exit 64; }
[[ "$run_timeout_seconds" =~ ^[0-9]+$ ]] || { echo "RUN_TIMEOUT_SECONDS must be an integer" >&2; exit 64; }
[[ ! -e "$output_root" ]] || { echo "refusing to reuse output root: $output_root" >&2; exit 44; }
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

assert_npu03_idle() {
  local snapshot occupied
  snapshot="$(npu-smi info)"
  occupied="$(awk -F '|' '$2 ~ /^[[:space:]]*[0-3][[:space:]]+[0-9]+[[:space:]]*$/ && $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {print $3}' <<<"$snapshot")"
  [[ -z "$occupied" ]] || { echo "physical NPU0-3 are occupied" >&2; exit 42; }
}

assert_npu03_idle
mkdir -p "$output_root"
npu-smi info >"$output_root/npu-before.txt"
docker ps --no-trunc >"$output_root/docker-before.txt"
{
  echo "scope=upstream-float-device-admission-smoke-only"
  echo "image=$image"
  echo "image_id=$(docker image inspect --format '{{.Id}}' "$image")"
  echo "container_policy=one-shot --rm; network none; no image mutation"
  echo "device_policy=physical NPU0 only; physical NPU1-7 are not mapped"
  echo "admission_policy=actual NPU0-3 processes only; idle declared/privileged containers do not block by operator instruction"
  echo "lease_file=$lease_file"
  echo "operator_commit=$(git -C "$operator_root" rev-parse HEAD)"
  echo "example_sha256=$(sha256sum "$example_path" | awk '{print $1}')"
  echo "candidate_library_sha256=$(sha256sum "$custom_library" | awk '{print $1}')"
  echo "protocol_commit=$(git -C "$repo_root" rev-parse HEAD)"
} >"$output_root/provenance.txt"

docker_args=(
  run --rm --name "$container_name"
  --label com.model-tuning-lab.owner=qwen35-t21-upstream-float-smoke
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
  -v "$candidate_opp_root":/opp:ro
  -v "$operator_root":/operator:ro
  -e ASCEND_RT_VISIBLE_DEVICES=0
  "$image" bash -lc
)

set +e
timeout --signal=TERM --kill-after=20s "${run_timeout_seconds}s" docker "${docker_args[@]}" '
      set -euo pipefail
      source /usr/local/Ascend/cann-9.1.0/set_env.sh
      vendor=/opp/vendors/qwen35_t21_v910_transformer
      export ASCEND_CUSTOM_OPP_PATH="$vendor"
      export LD_LIBRARY_PATH="$vendor/op_api/lib:${LD_LIBRARY_PATH:-}"
      source_file=/operator/experimental/ffn/swiglu_gated_mlp/examples/test_aclnn_swiglu_gated_mlp.cpp
      compiler_args=(
        -std=c++17 -O2 "$source_file"
        -I/usr/local/Ascend/cann-9.1.0/include
        -I/operator/common/include/external
        -I"$vendor/op_api/include"
        -L"$vendor/op_api/lib"
        -L/usr/local/Ascend/cann-9.1.0/lib64
        -Wl,-rpath,"$vendor/op_api/lib"
        -Wl,-rpath,/usr/local/Ascend/cann-9.1.0/lib64
        -lcust_opapi -lopapi -lnnopbase -lascendcl
        -o /tmp/t21_float_smoke
      )
      g++ "${compiler_args[@]}"
      echo "[link]"
      ldd -r /tmp/t21_float_smoke
      echo "[run]"
      /tmp/t21_float_smoke
    ' >"$output_root/run.log" 2>&1
run_rc=$?
set -e

npu-smi info >"$output_root/npu-after.txt"
printf '%s\n' "$run_rc" >"$output_root/exit-code.txt"
if [[ "$run_rc" -ne 0 ]]; then
  cat "$output_root/run.log" >&2
  echo "upstream FLOAT smoke failed; evidence: $output_root" >&2
  exit "$run_rc"
fi
grep -q '^result\[0\] is:' "$output_root/run.log" || {
  cat "$output_root/run.log" >&2
  echo "smoke exited zero without expected output" >&2
  exit 47
}

cat "$output_root/run.log"
echo "PASS: upstream FLOAT device-admission smoke"
echo "evidence=$output_root"

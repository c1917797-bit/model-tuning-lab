#!/usr/bin/env bash
set -euo pipefail

image="${IMAGE:-quay.io/ascend/vllm-ascend:v0.23.0}"
repo_root="${REPO_ROOT:-/opt/host/vnf/austinov/worktrees/qwen35-performance-delivery}"
candidate_opp_root="${CANDIDATE_OPP_ROOT:-/cache/austinov/qwen35-t21-abi-adapter-opp-r2-20260911}"
bridge_root="${BRIDGE_ROOT:-/cache/austinov/qwen35-t21-public-acl-bridge-20260912-v5}"
model_config="${MODEL_CONFIG:-/cache/austinov/Qwen3.8-27B/config.json}"
lease_file="${LEASE_FILE:-/cache/austinov/.locks/npu0-3.lock}"
lease_wait_seconds="${LEASE_WAIT_SECONDS:-45}"
run_timeout_seconds="${RUN_TIMEOUT_SECONDS:-1800}"
m_values="${M_VALUES:-1 5 8 16}"
seeds="${SEEDS:-1 2 3}"
stress_iterations="${STRESS_ITERATIONS:-100}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_root="${OUTPUT_ROOT:-/cache/austinov/qwen35-t21-public-bridge-numerical-$timestamp}"
container_name="${CONTAINER_NAME:-qwen35_t21_public_bridge_numerical_npu0}"

tool_relative="qwen35-performance-optimization/tools/qwen35_t21_public_bridge_numerical.py"
tool_path="$repo_root/$tool_relative"
vendor_relative="vendors/qwen35_t21_v910_transformer"
vendor_path="$candidate_opp_root/$vendor_relative"
custom_library="$vendor_path/op_api/lib/libcust_opapi.so"
bridge_library="$bridge_root/qwen35_t21_bridge.so"

for path in "$repo_root" "$tool_path" "$model_config" "$custom_library" "$bridge_library"; do
  [[ -e "$path" ]] || { echo "required path is missing: $path" >&2; exit 64; }
done
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); t=d["text_config"]; assert d["model_type"]=="qwen3_5"; assert t["dtype"]=="bfloat16"; assert t["hidden_size"]==5120; assert t["intermediate_size"]==17408' "$model_config" || {
  echo "model config does not match Qwen3.5 BF16 TP4 shape contract" >&2
  exit 64
}
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
snapshot="$(npu-smi info)"
occupied="$(awk -F '|' '$2 ~ /^[[:space:]]*[0-3][[:space:]]+[0-9]+[[:space:]]*$/ && $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {print $3}' <<<"$snapshot")"
[[ -z "$occupied" ]] || { echo "physical NPU0-3 are occupied" >&2; exit 42; }

mkdir -p "$output_root"
npu-smi info >"$output_root/npu-before.txt"
{
  echo "scope=public-acl-bridge-zero-copy-layout-numerical-and-stress-gate"
  echo "image=$image"
  echo "image_id=$(docker image inspect --format '{{.Id}}' "$image")"
  echo "device_policy=physical NPU0 only; physical NPU1-7 are not mapped"
  echo "admission_policy=actual NPU0-3 processes plus cooperative lease"
  echo "model_config_sha256=$(sha256sum "$model_config" | awk '{print $1}')"
  echo "bridge_sha256=$(sha256sum "$bridge_library" | awk '{print $1}')"
  echo "candidate_library_sha256=$(sha256sum "$custom_library" | awk '{print $1}')"
  echo "tool_sha256=$(sha256sum "$tool_path" | awk '{print $1}')"
  echo "protocol_commit=$(git -C "$repo_root" rev-parse HEAD)"
  echo "m_values=$m_values"
  echo "seeds=$seeds"
  echo "stress_iterations=$stress_iterations"
} >"$output_root/provenance.txt"

set +e
timeout --signal=TERM --kill-after=30s "${run_timeout_seconds}s" docker run --rm \
  --name "$container_name" \
  --network none \
  --device /dev/davinci0 \
  --device /dev/davinci_manager \
  --device /dev/devmm_svm \
  --device /dev/hisi_hdc \
  -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64:ro \
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info:ro \
  -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
  -v "$candidate_opp_root":/opp:ro \
  -v "$bridge_root":/bridge:ro \
  -v "$repo_root":/experiment:ro \
  -e ASCEND_RT_VISIBLE_DEVICES=0 \
  -e PYTHONPATH=/bridge \
  -e QWEN35_T21_OPAPI_LIBRARY="/opp/$vendor_relative/op_api/lib/libcust_opapi.so" \
  -e "M_VALUES=$m_values" \
  -e "SEEDS=$seeds" \
  -e "STRESS_ITERATIONS=$stress_iterations" \
  "$image" bash -lc '
    set -euo pipefail
    source /usr/local/Ascend/cann-9.1.0/set_env.sh
    export ASCEND_CUSTOM_OPP_PATH=/opp/vendors/qwen35_t21_v910_transformer
    export LD_LIBRARY_PATH="$ASCEND_CUSTOM_OPP_PATH/op_api/lib:${LD_LIBRARY_PATH:-}"
    python /experiment/qwen35-performance-optimization/tools/qwen35_t21_public_bridge_numerical.py
  ' >"$output_root/run.log" 2>&1
run_rc=$?
set -e
npu-smi info >"$output_root/npu-after.txt"
printf '%s\n' "$run_rc" >"$output_root/exit-code.txt"
if [[ "$run_rc" -ne 0 ]]; then
  cat "$output_root/run.log" >&2
  echo "public bridge numerical gate failed; evidence: $output_root" >&2
  exit "$run_rc"
fi

expected_count="$(( $(wc -w <<<"$m_values") * $(wc -w <<<"$seeds") ))"
actual_count="$(grep -c 'qwen35-t21-public-bridge-numerical/v1' "$output_root/run.log" || true)"
passed_count="$(grep 'qwen35-t21-public-bridge-numerical/v1' "$output_root/run.log" | grep -c '"passed": true' || true)"
stress_passed="$(grep 'qwen35-t21-public-bridge-stress/v1' "$output_root/run.log" | grep -c '"passed": true' || true)"
[[ "$actual_count" -eq "$expected_count" && "$passed_count" -eq "$expected_count" && "$stress_passed" -eq 1 ]] || {
  cat "$output_root/run.log" >&2
  echo "result count mismatch: expected=$expected_count actual=$actual_count passed=$passed_count stress=$stress_passed" >&2
  exit 47
}
grep 'qwen35-t21-public-bridge-' "$output_root/run.log"
echo "PASS: public bridge zero-copy layout numerical and stress gate"
echo "evidence=$output_root"

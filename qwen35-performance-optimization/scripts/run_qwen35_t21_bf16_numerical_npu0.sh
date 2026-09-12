#!/usr/bin/env bash
set -euo pipefail

image="${IMAGE:-quay.io/ascend/vllm-ascend:v0.23.0}"
repo_root="${REPO_ROOT:-/opt/host/vnf/austinov/worktrees/qwen35-performance-delivery}"
candidate_opp_root="${CANDIDATE_OPP_ROOT:-/cache/austinov/qwen35-t21-abi-adapter-opp-r2-20260911}"
model_config="${MODEL_CONFIG:-/cache/austinov/Qwen3.8-27B/config.json}"
lease_file="${LEASE_FILE:-/cache/austinov/.locks/npu0-3.lock}"
lease_wait_seconds="${LEASE_WAIT_SECONDS:-45}"
run_timeout_seconds="${RUN_TIMEOUT_SECONDS:-1800}"
m_values="${M_VALUES:-1 5 8 16}"
seeds="${SEEDS:-1 2 3}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_root="${OUTPUT_ROOT:-/cache/austinov/qwen35-t21-bf16-numerical-$timestamp}"
container_name="${CONTAINER_NAME:-qwen35_t21_bf16_numerical_npu0}"

source_relative="qwen35-performance-optimization/tools/qwen35_t21_bf16_numerical_gate.cpp"
source_path="$repo_root/$source_relative"
vendor_relative="vendors/qwen35_t21_v910_transformer"
vendor_path="$candidate_opp_root/$vendor_relative"
custom_library="$vendor_path/op_api/lib/libcust_opapi.so"

for path in "$repo_root" "$candidate_opp_root" "$model_config" "$source_path" "$vendor_path" "$custom_library"; do
  [[ -e "$path" ]] || { echo "required path is missing: $path" >&2; exit 64; }
done
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); t=d["text_config"]; assert d["model_type"]=="qwen3_5"; assert t["dtype"]=="bfloat16"; assert t["hidden_size"]==5120; assert t["intermediate_size"]==17408' "$model_config" || {
  echo "model config does not match Qwen3.5 BF16 TP4 shape contract" >&2
  exit 64
}
for value in $m_values; do
  [[ " 1 5 8 16 " == *" $value "* ]] || { echo "invalid M value: $value" >&2; exit 64; }
done
for seed in $seeds; do
  [[ "$seed" =~ ^[1-9][0-9]*$ ]] || { echo "invalid positive seed: $seed" >&2; exit 64; }
done
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
docker ps --no-trunc >"$output_root/docker-before.txt"
{
  echo "scope=exact-shape-bf16-same-device-numerical-gate"
  echo "image=$image"
  echo "image_id=$(docker image inspect --format '{{.Id}}' "$image")"
  echo "container_policy=one-shot --rm; network none; no image mutation"
  echo "device_policy=physical NPU0 only; physical NPU1-7 are not mapped"
  echo "admission_policy=actual NPU0-3 processes only; idle declared/privileged containers do not block by operator instruction"
  echo "reference=official aclnnMatmul -> aclnnSwiGlu -> aclnnMatmul"
  echo "model_config=$model_config"
  echo "model_config_sha256=$(sha256sum "$model_config" | awk '{print $1}')"
  echo "model_shape=text hidden 5120; global intermediate 17408; TP4 local intermediate 4352; local gate/up 8704"
  echo "m_values=$m_values"
  echo "seeds=$seeds"
  echo "source_sha256=$(sha256sum "$source_path" | awk '{print $1}')"
  echo "candidate_library_sha256=$(sha256sum "$custom_library" | awk '{print $1}')"
  echo "protocol_commit=$(git -C "$repo_root" rev-parse HEAD)"
} >"$output_root/provenance.txt"

docker_args=(
  run --rm --name "$container_name"
  --label com.model-tuning-lab.owner=qwen35-t21-bf16-numerical
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
  -v "$repo_root":/experiment:ro
  -e ASCEND_RT_VISIBLE_DEVICES=0
  -e "M_VALUES=$m_values"
  -e "SEEDS=$seeds"
  "$image" bash -lc
)

set +e
timeout --signal=TERM --kill-after=30s "${run_timeout_seconds}s" docker "${docker_args[@]}" '
  set -euo pipefail
  source /usr/local/Ascend/cann-9.1.0/set_env.sh
  vendor=/opp/vendors/qwen35_t21_v910_transformer
  export ASCEND_CUSTOM_OPP_PATH="$vendor"
  export LD_LIBRARY_PATH="$vendor/op_api/lib:${LD_LIBRARY_PATH:-}"
  source_file=/experiment/qwen35-performance-optimization/tools/qwen35_t21_bf16_numerical_gate.cpp
  compiler_args=(
    -std=c++17 -Wall -Wextra -Werror -O2 "$source_file"
    -I/usr/local/Ascend/cann-9.1.0/include
    -I"$vendor/op_api/include"
    -L"$vendor/op_api/lib"
    -L/usr/local/Ascend/cann-9.1.0/lib64
    -Wl,-rpath,"$vendor/op_api/lib"
    -Wl,-rpath,/usr/local/Ascend/cann-9.1.0/lib64
    -lcust_opapi -lopapi -lnnopbase -lascendcl
    -o /tmp/t21_bf16_gate
  )
  g++ "${compiler_args[@]}"
  ldd -r /tmp/t21_bf16_gate
  for seed in $SEEDS; do
    for m in $M_VALUES; do
      /tmp/t21_bf16_gate --m "$m" --seed "$seed"
    done
  done
' >"$output_root/run.log" 2>&1
run_rc=$?
set -e

npu-smi info >"$output_root/npu-after.txt"
printf '%s\n' "$run_rc" >"$output_root/exit-code.txt"
if [[ "$run_rc" -ne 0 ]]; then
  cat "$output_root/run.log" >&2
  echo "BF16 numerical gate failed; evidence: $output_root" >&2
  exit "$run_rc"
fi

expected_count="$(( $(wc -w <<<"$m_values") * $(wc -w <<<"$seeds") ))"
actual_count="$(grep -c '"schema":"qwen35-t21-bf16-numerical/v1"' "$output_root/run.log" || true)"
passed_count="$(grep -c '"passed":true' "$output_root/run.log" || true)"
[[ "$actual_count" -eq "$expected_count" && "$passed_count" -eq "$expected_count" ]] || {
  cat "$output_root/run.log" >&2
  echo "result count mismatch: expected=$expected_count actual=$actual_count passed=$passed_count" >&2
  exit 47
}

grep '"schema":"qwen35-t21-bf16-numerical/v1"' "$output_root/run.log"
echo "PASS: exact-shape BF16 numerical matrix"
echo "evidence=$output_root"

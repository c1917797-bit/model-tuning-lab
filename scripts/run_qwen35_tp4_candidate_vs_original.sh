#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
run_id="${RUN_ID:?set RUN_ID to a unique immutable id}"
output_root="${OUTPUT_ROOT:?set OUTPUT_ROOT to a new absolute directory}"
candidate_mode="${CANDIDATE_MODE:-flashcomm1}"
candidate_id="${CANDIDATE_ID:-$candidate_mode}"
device_set="${DEVICE_SET:-4-7}"
port="${PORT:-10010}"
base_url="http://127.0.0.1:$port"
readiness_timeout="${READINESS_TIMEOUT_SECONDS:-1800}"
expected_normalized="${EXPECTED_FUSED_TAIL_NORMALIZED:-64}"
expected_fused="${EXPECTED_FUSED_TAIL_FUSED:-128}"
original_dir="${ORIGINAL_BASELINE_DIR:-/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/tp4-dev-decodegraph/quick32-v3}"
device_tag="${device_set//-/_}"
candidate_container="${CANDIDATE_CONTAINER:-qwen35_${candidate_mode}_${device_tag}_$run_id}"
active_container=""
active_log=""

case "$candidate_mode" in
  mtp-local-argmax)
    default_config="$repo_root/configs/qwen35-query-rewrite-mtp-local-argmax-candidate.yaml"
    ;;
  ngram-gpu)
    default_config="$repo_root/configs/qwen35-query-rewrite-ngram-gpu-candidate.yaml"
    ;;
  control-mmar-off)
    default_config="$repo_root/configs/qwen35-query-rewrite-control-mmar-off-candidate.yaml"
    ;;
  mmar-on)
    default_config="$repo_root/configs/qwen35-query-rewrite-mmar-on-candidate.yaml"
    ;;
  mmar-on-hccl-aiv)
    default_config="$repo_root/configs/qwen35-query-rewrite-mmar-on-hccl-aiv-candidate.yaml"
    ;;
  mmar-on-weight-prefetch-gateup)
    default_config="$repo_root/configs/qwen35-query-rewrite-mmar-on-weight-prefetch-gateup-candidate.yaml"
    ;;
  mmar-on-weight-prefetch-gateup-0p1)
    default_config="$repo_root/configs/qwen35-query-rewrite-mmar-on-weight-prefetch-gateup-0p1-candidate.yaml"
    ;;
  mmar-on-weight-prefetch-gateup-0p1-fused-tail)
    default_config="$repo_root/configs/qwen35-query-rewrite-mmar-add-rmsnorm-candidate.yaml"
    ;;
  mmar-on-weight-prefetch-gateup-0p1-hccl-buff1024)
    default_config="$repo_root/configs/qwen35-query-rewrite-mmar-prefetch-0p1-hccl-buff1024-candidate.yaml"
    ;;
  mmar-on-weight-prefetch-gateup-0p1-taskqueue2)
    default_config="$repo_root/configs/qwen35-query-rewrite-mmar-on-weight-prefetch-gateup-0p1-taskqueue2-candidate.yaml"
    ;;
  mmar-on-weight-prefetch-gateup-0p1-static-kernel)
    default_config="$repo_root/configs/qwen35-query-rewrite-mmar-on-weight-prefetch-gateup-0p1-static-kernel-candidate.yaml"
    ;;
  tp2-pp2-mmar-on-weight-prefetch-gateup-0p1)
    default_config="$repo_root/configs/qwen35-query-rewrite-tp2-pp2-mmar-on-weight-prefetch-gateup-0p1-candidate.yaml"
    ;;
  tp2-dp2-mmar-on)
    default_config="$repo_root/configs/qwen35-query-rewrite-tp2-dp2-mmar-on-candidate.yaml"
    ;;
  tp2-dp2-mmar-on-text-only)
    default_config="$repo_root/configs/qwen35-query-rewrite-tp2-dp2-mmar-on-text-only-candidate.yaml"
    ;;
  tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt16384)
    default_config="$repo_root/configs/qwen35-query-rewrite-tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt16384-candidate.yaml"
    ;;
  tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt8192)
    default_config="$repo_root/configs/qwen35-query-rewrite-tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt8192-candidate.yaml"
    ;;
  tp2-dp2-mmar-prefetch-0p1-text-ctx32k-bt8192-gmu0p95)
    default_config="$repo_root/configs/qwen35-query-rewrite-tp2-dp2-mmar-prefetch-0p1-text-ctx32k-bt8192-gmu0p95-candidate.yaml"
    ;;
  selective-ffn-nz)
    default_config="$repo_root/configs/qwen35-query-rewrite-selective-ffn-nz-candidate.yaml"
    ;;
  flashcomm2-oproj2-mmar-prefetch-gateup-0p1)
    default_config="$repo_root/configs/qwen35-query-rewrite-flashcomm2-oproj2-mmar-prefetch-gateup-0p1-candidate.yaml"
    ;;
  flashcomm2-oproj1-mmar-prefetch-gateup-0p1)
    default_config="$repo_root/configs/qwen35-query-rewrite-flashcomm2-oproj1-mmar-prefetch-gateup-0p1-candidate.yaml"
    ;;
  flashcomm1)
    default_config="$repo_root/configs/qwen35-query-rewrite-flashcomm1-candidate.yaml"
    ;;
  flashcomm1-gdn-shape-mmar-prefetch-gateup-0p1)
    default_config="$repo_root/configs/qwen35-query-rewrite-flashcomm1-gdn-shape-mmar-prefetch-gateup-0p1-candidate.yaml"
    ;;
  bf16-nz)
    default_config="$repo_root/configs/qwen35-query-rewrite-bf16-nz-candidate.yaml"
    ;;
  bf16-nz-mmar-off)
    default_config="$repo_root/configs/qwen35-query-rewrite-bf16-nz-mmar-off-candidate.yaml"
    ;;
  flashcomm1-bf16-nz)
    default_config="$repo_root/configs/qwen35-query-rewrite-flashcomm1-bf16-nz-stack.yaml"
    ;;
  *)
    echo "unsupported CANDIDATE_MODE: $candidate_mode" >&2
    exit 64
    ;;
esac
case "$device_set" in
  4-7) ;;
  *) echo "DEVICE_SET must be 4-7 for this workstream" >&2; exit 64 ;;
esac
candidate_config="${CANDIDATE_CONFIG:-$default_config}"

case "$output_root" in
  /*) ;;
  *) echo "OUTPUT_ROOT must be absolute" >&2; exit 64 ;;
esac
if [[ -e "$output_root" ]]; then
  echo "refusing to reuse immutable output root: $output_root" >&2
  exit 44
fi
if [[ ! -f "$candidate_config" ]]; then
  echo "candidate config does not exist: $candidate_config" >&2
  exit 66
fi
if docker container inspect "$candidate_container" >/dev/null 2>&1; then
  echo "refusing to replace existing container: $candidate_container" >&2
  exit 41
fi

mkdir -p "$output_root"

cleanup() {
  local status=$?
  if [[ -n "$active_container" ]] &&
     docker container inspect "$active_container" >/dev/null 2>&1; then
    docker logs "$active_container" >"$active_log" 2>&1 || true
    docker stop --time 30 "$active_container" >/dev/null || true
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

wait_for_health() {
  local deadline=$((SECONDS + readiness_timeout))
  while (( SECONDS < deadline )); do
    if [[ "$(docker inspect -f '{{.State.Running}}' "$candidate_container" 2>/dev/null || true)" != true ]]; then
      echo "$candidate_container exited before readiness" >&2
      return 70
    fi
    if curl --fail --silent --max-time 5 "$base_url/health" >/dev/null; then
      return 0
    fi
    sleep 5
  done
  echo "$candidate_container did not become healthy within ${readiness_timeout}s" >&2
  return 71
}

active_container="$candidate_container"
active_log="$output_root/service.log"
env CONTAINER_NAME="$candidate_container" PORT="$port" DEVICE_SET="$device_set" \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" "$candidate_mode"
wait_for_health
docker inspect "$candidate_container" >"$output_root/container-inspect.json"

if [[ "$candidate_mode" == mmar-on-weight-prefetch-gateup-0p1-fused-tail ]]; then
  activation_log="$output_root/service-before-benchmark.log"
  activation_json="$output_root/integration-check.json"
  docker logs "$candidate_container" >"$activation_log" 2>&1
  set +e
  python3 "$repo_root/scripts/check_qwen35_fused_tail_activation.py" --log "$activation_log" --output "$activation_json" --expected-ranks 4 --expected-normalized "$expected_normalized" --expected-fused "$expected_fused"
  activation_status=$?
  set -e
  sha256sum "$activation_log" "$activation_json" >"$output_root/activation-SHA256SUMS"
  if [[ "$activation_status" != 0 ]]; then
    echo "fused-tail activation gate failed with status $activation_status" >&2
    exit 72
  fi
fi

set +e
python3 "$repo_root/scripts/run_qwen35_candidate_quick32.py" \
  --base-url "$base_url" \
  --candidate-id "$candidate_id" \
  --candidate-mode "$candidate_mode" \
  --device-set "$device_set" \
  --candidate-config "$candidate_config" \
  --run-id "$run_id" \
  --output-root "$output_root/candidate"
candidate_run_status=$?
set -e

if [[ "$candidate_mode" == ngram-gpu ||
      "$candidate_mode" == mtp-local-argmax ]]; then
  curl --fail --silent --max-time 10 "$base_url/metrics" |
    awk '/spec_decode|speculative/ {print}' \
      >"$output_root/speculative-metrics-after.prom"
fi

docker logs "$candidate_container" >"$active_log" 2>&1 || true
docker stop --time 30 "$candidate_container" >/dev/null
active_container=""
active_log=""

set +e
analyzer_extra=()
if [[ "$candidate_run_status" != 0 ]]; then
  analyzer_extra+=(--allow-incomplete)
fi
python3 "$repo_root/scripts/analyze_qwen35_candidate_vs_original.py" \
  --original-dir "$original_dir" \
  --candidate-dir "$output_root/candidate" \
  --candidate-id "$candidate_id" \
  --candidate-device-set "$device_set" \
  --candidate-run "$output_root/candidate/candidate-run.json" \
  --target-ratio 0.5 \
  --output "$output_root/decision.json" \
  "${analyzer_extra[@]}"
decision_status=$?
set -e
if [[ "$decision_status" != 0 && "$decision_status" != 2 &&
      "$decision_status" != 3 && "$decision_status" != 4 ]]; then
  echo "candidate analyzer failed with status $decision_status" >&2
  exit "$decision_status"
fi

artifacts=(
  "$output_root/container-inspect.json"
  "$output_root/service.log"
  "$output_root/candidate/candidate-run.json"
  "$output_root/decision.json"
)
if [[ -f "$output_root/integration-check.json" ]]; then
  artifacts+=(
    "$output_root/service-before-benchmark.log"
    "$output_root/integration-check.json"
    "$output_root/activation-SHA256SUMS"
  )
fi
for concurrency in 1 5 8 16; do
  cell="$output_root/candidate/c${concurrency}-r1.json"
  [[ ! -f "$cell" ]] || artifacts+=("$cell")
done
sha256sum "${artifacts[@]}" >"$output_root/SHA256SUMS"
if [[ -f "$output_root/speculative-metrics-after.prom" ]]; then
  sha256sum "$output_root/speculative-metrics-after.prom" \
    >>"$output_root/SHA256SUMS"
fi

echo "completed candidate versus fixed original baseline: $output_root"
echo "candidate matrix status: $candidate_run_status (0=complete)"
echo "decision analyzer status: $decision_status (0=2x target, 2=iterate, 3=hold correctness, 4=reject runtime)"

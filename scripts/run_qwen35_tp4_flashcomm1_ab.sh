#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
run_id="${RUN_ID:?set RUN_ID to a unique immutable id}"
output_root="${OUTPUT_ROOT:?set OUTPUT_ROOT to a new absolute directory}"
port="${PORT:-10010}"
base_url="http://127.0.0.1:${port}"
readiness_timeout="${READINESS_TIMEOUT_SECONDS:-1800}"
baseline_container="${BASELINE_CONTAINER:-qwen35_tp4_canonical_${run_id}}"
candidate_container="${CANDIDATE_CONTAINER:-qwen35_tp4_flashcomm1_${run_id}}"
baseline_config="$repo_root/configs/qwen35-query-rewrite-baseline.yaml"
candidate_config="$repo_root/configs/qwen35-query-rewrite-flashcomm1-candidate.yaml"
active_container=""
active_log=""

case "$output_root" in
  /*) ;;
  *) echo "OUTPUT_ROOT must be absolute" >&2; exit 64 ;;
esac
if [[ -e "$output_root" ]]; then
  echo "refusing to reuse immutable output root: $output_root" >&2
  exit 44
fi
if [[ "$baseline_container" == "$candidate_container" ]]; then
  echo "baseline and candidate container names must differ" >&2
  exit 64
fi
for name in "$baseline_container" "$candidate_container"; do
  if docker container inspect "$name" >/dev/null 2>&1; then
    echo "refusing to replace existing container: $name" >&2
    exit 41
  fi
done

mkdir -p "$output_root/baseline" "$output_root/candidate"

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
  local container="$1"
  local deadline=$((SECONDS + readiness_timeout))
  while (( SECONDS < deadline )); do
    if [[ "$(docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null || true)" != true ]]; then
      echo "$container exited before readiness" >&2
      return 70
    fi
    if curl --fail --silent --max-time 5 "$base_url/health" >/dev/null; then
      return 0
    fi
    sleep 5
  done
  echo "$container did not become healthy within ${readiness_timeout}s" >&2
  return 71
}

run_variant() {
  local variant="$1"
  local mode="$2"
  local config="$3"
  local container="$4"
  local variant_root="$output_root/$variant"

  active_container="$container"
  active_log="$variant_root/service.log"
  env CONTAINER_NAME="$container" PORT="$port" "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" "$mode"
  wait_for_health "$container"

  docker inspect "$container" >"$variant_root/container-inspect.json"
  python3 "$repo_root/scripts/run_qwen35_benchmark_matrix.py" --config "$config" --base-url "$base_url" --variant "$variant" --run-id "$run_id" --output-root "$variant_root/matrix"

  docker logs "$container" >"$active_log" 2>&1 || true
  docker stop --time 30 "$container" >/dev/null
  active_container=""
  active_log=""
}

run_variant baseline baseline "$baseline_config" "$baseline_container"
run_variant candidate flashcomm1 "$candidate_config" "$candidate_container"

set +e
python3 "$repo_root/scripts/analyze_qwen35_query_rewrite_ab.py" --baseline-dir "$output_root/baseline/matrix" --candidate-dir "$output_root/candidate/matrix" --target-ratio 0.5 --output "$output_root/decision.json"
decision_status=$?
set -e
if [[ "$decision_status" != 0 && "$decision_status" != 2 ]]; then
  echo "A/B analyzer failed with status $decision_status" >&2
  exit "$decision_status"
fi

sha256sum "$output_root/baseline/container-inspect.json" "$output_root/candidate/container-inspect.json" "$output_root/baseline/matrix/matrix-run.json" "$output_root/candidate/matrix/matrix-run.json" "$output_root/decision.json" >"$output_root/SHA256SUMS"

echo "completed TP4 canonical-baseline versus FlashComm1 A/B: $output_root"
echo "decision analyzer status: $decision_status (0=2x target met, 2=iterate)"

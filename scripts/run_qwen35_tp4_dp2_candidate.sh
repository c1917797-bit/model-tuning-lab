#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
run_id="${RUN_ID:?set an immutable RUN_ID}"
output_root="${OUTPUT_ROOT:?set a new absolute OUTPUT_ROOT}"
baseline_summary="${BASELINE_SUMMARY:?set the immutable TP8 baseline summary}"
candidate_mode="${CANDIDATE_MODE:-tp4-dp2}"
port="${PORT:-10010}"
readiness_timeout="${READINESS_TIMEOUT_SECONDS:-2400}"
active_container=""

case "$candidate_mode" in
  tp4-dp2)
    runtime_role=tp4-dp2
    candidate_id=tp4-dp2-vs-tp8
    ;;
  tp4-dp2-mtp-local-argmax)
    runtime_role=tp4-dp2-mtp-local-argmax
    candidate_id=tp4-dp2-mtp-local-argmax-k1
    ;;
  tp4-dp2-fullpiece-user)
    runtime_role=tp4-dp2-fullpiece-user
    candidate_id=tp4-dp2-fullpiece-user
    ;;
  *)
    echo "unsupported CANDIDATE_MODE: $candidate_mode" >&2
    exit 64
    ;;
esac

case "$output_root" in
  /*) ;;
  *) echo "OUTPUT_ROOT must be absolute" >&2; exit 64 ;;
esac
if [[ -e "$output_root" ]]; then
  echo "refusing to reuse immutable output root: $output_root" >&2
  exit 44
fi
if [[ ! -f "$baseline_summary" ]]; then
  echo "baseline summary does not exist: $baseline_summary" >&2
  exit 66
fi
container_name="${CONTAINER_NAME:-qwen35_${candidate_mode}_$run_id}"
mkdir -p "$output_root"

cleanup() {
  local status=$?
  if [[ -n "$active_container" ]] &&
     docker container inspect "$active_container" >/dev/null 2>&1; then
    docker logs "$active_container" >"$output_root/service.log" 2>&1 || true
    docker stop --time 60 "$active_container" >/dev/null || true
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

CONTAINER_NAME="$container_name" PORT="$port" RUNTIME_ROLE="$runtime_role" \
  "$repo_root/scripts/run_qwen35_tp8_user_baseline_service.sh"
active_container="$container_name"

deadline=$((SECONDS + readiness_timeout))
while (( SECONDS < deadline )); do
  if [[ "$(docker inspect -f '{{.State.Running}}' "$container_name" 2>/dev/null || true)" != true ]]; then
    echo "$container_name exited before readiness" >&2
    exit 70
  fi
  if curl --fail --silent --max-time 5 "http://127.0.0.1:$port/health" >/dev/null; then
    break
  fi
  sleep 5
done
if ! curl --fail --silent --max-time 5 "http://127.0.0.1:$port/health" >/dev/null; then
  echo "$container_name did not become healthy" >&2
  exit 71
fi

docker inspect "$container_name" >"$output_root/container-inspect.json"
docker logs "$container_name" >"$output_root/service-ready.log" 2>&1
npu-smi info >"$output_root/npu-ready.txt"

python3 "$repo_root/scripts/run_qwen35_tp8_baseline_matrix.py" \
  --base-url "http://127.0.0.1:$port" \
  --output-root "$output_root/matrix" \
  --run-id "$run_id" \
  --role candidate \
  --tensor-parallel-size 4 \
  --data-parallel-size 2 \
  --repetitions 3

if [[ "$candidate_mode" == tp4-dp2-mtp-local-argmax ]]; then
  curl --fail --silent --max-time 10 "http://127.0.0.1:$port/metrics" |
    awk '/spec_decode|speculative/ {print}' \
      >"$output_root/speculative-metrics-after.prom"
fi
docker logs "$container_name" >"$output_root/service.log" 2>&1 || true
docker stop --time 60 "$container_name" >/dev/null
active_container=""

set +e
python3 "$repo_root/scripts/analyze_qwen35_tp8_candidate.py" \
  --baseline-summary "$baseline_summary" \
  --candidate-summary "$output_root/matrix/candidate-summary.json" \
  --candidate-id "$candidate_id" \
  --target-speedup 2.0 \
  --output "$output_root/decision.json"
decision_status=$?
set -e
if [[ "$decision_status" != 0 && "$decision_status" != 2 && "$decision_status" != 3 ]]; then
  echo "candidate analyzer failed with status $decision_status" >&2
  exit "$decision_status"
fi

find "$output_root" -type f ! -name SHA256SUMS -print0 |
  sort -z | xargs -0 sha256sum >"$output_root/SHA256SUMS"
echo "completed TP4/DP2 candidate: $output_root"
echo "decision analyzer status: $decision_status"

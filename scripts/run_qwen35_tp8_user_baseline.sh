#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
run_id="${RUN_ID:?set an immutable RUN_ID}"
output_root="${OUTPUT_ROOT:?set a new absolute OUTPUT_ROOT}"
container_name="${CONTAINER_NAME:-qwen35_tp8_user_baseline_$run_id}"
port="${PORT:-10010}"
readiness_timeout="${READINESS_TIMEOUT_SECONDS:-2400}"
active_container=""

case "$output_root" in
  /*) ;;
  *) echo "OUTPUT_ROOT must be absolute" >&2; exit 64 ;;
esac
if [[ -e "$output_root" ]]; then
  echo "refusing to reuse immutable output root: $output_root" >&2
  exit 44
fi
mkdir -p "$output_root"

cleanup() {
  local status=$?
  if [[ -n "$active_container" ]] && docker container inspect "$active_container" >/dev/null 2>&1; then
    docker logs "$active_container" >"$output_root/service.log" 2>&1 || true
    docker stop --time 60 "$active_container" >/dev/null || true
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

CONTAINER_NAME="$container_name" PORT="$port" "$repo_root/scripts/run_qwen35_tp8_user_baseline_service.sh"
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
  --repetitions 3

docker logs "$container_name" >"$output_root/service.log" 2>&1 || true
docker stop --time 60 "$container_name" >/dev/null
active_container=""

find "$output_root" -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum >"$output_root/SHA256SUMS"
echo "completed TP8/DP1 user baseline: $output_root"

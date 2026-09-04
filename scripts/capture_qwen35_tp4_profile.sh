#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dataset="${DATASET:-/cache/cch/query_rewrite.jsonl}"
dataset_sha256="${DATASET_SHA256:-a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e}"
model="${MODEL:-Qwen3-5/Qwen3.5-27B}"
port="${PORT:-10010}"
base_url="http://127.0.0.1:${port}"
run_id="${PROFILE_RUN_ID:?set PROFILE_RUN_ID to a unique immutable id}"
container_name="${CONTAINER_NAME:?set CONTAINER_NAME to a new unique name}"
profile_dir="${PROFILE_DIR:?set PROFILE_DIR to a new absolute directory}"
artifact_dir="${ARTIFACT_DIR:-/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/profile-captures/${run_id}}"
readiness_timeout="${READINESS_TIMEOUT_SECONDS:-1800}"
profile_flush_timeout="${PROFILE_FLUSH_TIMEOUT_SECONDS:-600}"
profile_mode="${PROFILE_MODE:-profile-mmar-off}"
request_artifact="${artifact_dir}/request.json"
hotspot_artifact="${artifact_dir}/hotspots.json"
service_log="${artifact_dir}/service.log"

case "$profile_dir" in
  /*) ;;
  *) echo "PROFILE_DIR must be absolute" >&2; exit 64 ;;
esac
case "$artifact_dir" in
  /*) ;;
  *) echo "ARTIFACT_DIR must be absolute" >&2; exit 64 ;;
esac
if [[ -e "$profile_dir" || -e "$artifact_dir" ]]; then
  echo "refusing to reuse immutable output path" >&2
  echo "profile_dir=$profile_dir" >&2
  echo "artifact_dir=$artifact_dir" >&2
  exit 44
fi
case "$profile_mode" in
  profile|profile-mmar-off) ;;
  *) echo "PROFILE_MODE must be profile or profile-mmar-off" >&2; exit 64 ;;
esac

mkdir -p "$artifact_dir"
started=0
cleanup() {
  local status=$?
  if [[ "$started" == 1 ]] && docker container inspect "$container_name" >/dev/null 2>&1; then
    docker logs "$container_name" >"$service_log" 2>&1 || true
    docker stop --time 30 "$container_name" >/dev/null || true
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

env CONTAINER_NAME="$container_name" PORT="$port" PROFILE_DIR="$profile_dir" "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" "$profile_mode"
started=1

deadline=$((SECONDS + readiness_timeout))
while (( SECONDS < deadline )); do
  if [[ "$(docker inspect -f '{{.State.Running}}' "$container_name" 2>/dev/null || true)" != true ]]; then
    echo "profile service exited before readiness" >&2
    exit 70
  fi
  if curl --fail --silent --max-time 5 "$base_url/health" >/dev/null; then
    break
  fi
  sleep 5
done
if ! curl --fail --silent --max-time 5 "$base_url/health" >/dev/null; then
  echo "profile service did not become healthy within ${readiness_timeout}s" >&2
  exit 71
fi

openapi="$(curl --fail --silent --max-time 30 "$base_url/openapi.json")"
grep -q '"/start_profile"' <<<"$openapi" || { echo "missing /start_profile" >&2; exit 72; }
grep -q '"/stop_profile"' <<<"$openapi" || { echo "missing /stop_profile" >&2; exit 72; }

env PYTHONPATH="$repo_root/scripts${PYTHONPATH:+:$PYTHONPATH}" python3 "$repo_root/scripts/run_qwen35_profile_request.py" --base-url "$base_url" --model "$model" --dataset "$dataset" --dataset-sha256 "$dataset_sha256" --run-id "$run_id" --output "$request_artifact"

deadline=$((SECONDS + profile_flush_timeout))
while (( SECONDS < deadline )); do
  if find "$profile_dir" -type f -name kernel_details.csv -print -quit | grep -q .; then
    break
  fi
  sleep 5
done
if ! find "$profile_dir" -type f -name kernel_details.csv -print -quit | grep -q .; then
  echo "profile did not emit kernel_details.csv within ${profile_flush_timeout}s" >&2
  exit 73
fi

python3 "$repo_root/scripts/analyze_ascend_profile.py" "$profile_dir" --output "$hotspot_artifact"
sha256sum "$request_artifact" "$hotspot_artifact"

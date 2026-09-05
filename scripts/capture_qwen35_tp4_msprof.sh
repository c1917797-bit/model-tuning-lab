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
profile_rank="${PROFILE_RANK:-0}"
profile_mode="${PROFILE_MODE:-profile-msprof-mmar-off}"
device_set="${DEVICE_SET:-4-7}"
readiness_timeout="${READINESS_TIMEOUT_SECONDS:-1800}"
control_timeout="${PROFILE_CONTROL_TIMEOUT_SECONDS:-180}"
profile_flush_timeout="${PROFILE_FLUSH_TIMEOUT_SECONDS:-600}"
request_artifact="${artifact_dir}/request.json"
hotspot_artifact="${artifact_dir}/hotspots.json"
service_log="${artifact_dir}/service.log"
msprof_log="${artifact_dir}/msprof-interactive.log"
export_log="${artifact_dir}/msprof-export.log"
ready_file="${artifact_dir}/request-ready"
go_file="${artifact_dir}/request-go"
control_fifo="${artifact_dir}/msprof-control.fifo"
profile_metadata="${artifact_dir}/profile-metadata.json"

case "$profile_dir" in
  /*) ;;
  *) echo "PROFILE_DIR must be absolute" >&2; exit 64 ;;
esac
case "$artifact_dir" in
  /*) ;;
  *) echo "ARTIFACT_DIR must be absolute" >&2; exit 64 ;;
esac
case "$profile_rank" in
  0|1|2|3) ;;
  *) echo "PROFILE_RANK must be one of 0, 1, 2, 3" >&2; exit 64 ;;
esac
case "$profile_mode" in
  profile-msprof-mmar-off|profile-msprof-mmar-on|mmar-on-weight-prefetch-gateup-0p1-fused-tail) ;;
  *) echo "PROFILE_MODE must be profile-msprof-mmar-off, profile-msprof-mmar-on, or mmar-on-weight-prefetch-gateup-0p1-fused-tail" >&2; exit 64 ;;
esac
if [[ "$device_set" != 4-7 ]]; then
  echo "DEVICE_SET must be 4-7 for this workstream" >&2
  exit 64
fi
if [[ -e "$profile_dir" || -e "$artifact_dir" ]]; then
  echo "refusing to reuse immutable output path" >&2
  echo "profile_dir=$profile_dir" >&2
  echo "artifact_dir=$artifact_dir" >&2
  exit 44
fi

mkdir -p "$profile_dir" "$artifact_dir"
python3 - "$profile_metadata" "$run_id" "$profile_mode" "$device_set" "$profile_rank" "$container_name" "$profile_dir" <<'PY'
import json
import sys

path, run_id, profile_mode, device_set, profile_rank, container_name, profile_dir = sys.argv[1:]
with open(path, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "run_id": run_id,
            "profile_mode": profile_mode,
            "device_set": device_set,
            "profile_rank": int(profile_rank),
            "container_name": container_name,
            "profile_dir": profile_dir,
        },
        handle,
        indent=2,
        sort_keys=True,
    )
    handle.write("\n")
PY
started=0
request_pid=
msprof_pid=
cleanup() {
  local status=$?
  if [[ -n "$request_pid" ]]; then
    kill "$request_pid" >/dev/null 2>&1 || true
    wait "$request_pid" >/dev/null 2>&1 || true
  fi
  if [[ -n "$msprof_pid" ]]; then
    kill "$msprof_pid" >/dev/null 2>&1 || true
    wait "$msprof_pid" >/dev/null 2>&1 || true
  fi
  if [[ "$started" == 1 ]] &&
      docker container inspect "$container_name" >/dev/null 2>&1; then
    docker logs "$container_name" >"$service_log" 2>&1 || true
    docker stop --time 30 "$container_name" >/dev/null || true
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

env CONTAINER_NAME="$container_name" PORT="$port" DEVICE_SET="$device_set" ENABLE_DYNAMIC_PROFILING=1 "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" "$profile_mode"
started=1
docker inspect "$container_name" >"${artifact_dir}/container-inspect.json"

deadline=$((SECONDS + readiness_timeout))
while (( SECONDS < deadline )); do
  if [[ "$(docker inspect -f '{{.State.Running}}' "$container_name" 2>/dev/null || true)" != true ]]; then
    echo "msprof profile service exited before readiness" >&2
    exit 70
  fi
  if curl --fail --silent --max-time 5 "$base_url/health" >/dev/null; then
    break
  fi
  sleep 5
done
if ! curl --fail --silent --max-time 5 "$base_url/health" >/dev/null; then
  echo "msprof profile service did not become healthy" >&2
  exit 71
fi

worker_pid="$(
  docker exec "$container_name" ps -e -o pid=,args= |
    awk -v label="Worker_TP${profile_rank}" 'index($0, label) {print $1; exit}'
)"
if [[ -z "$worker_pid" ]] ||
    ! docker exec "$container_name" test -S "/root/dynamic_profiling_socket_${worker_pid}"; then
  echo "unable to resolve dynamic profiler socket for TP${profile_rank}" >&2
  docker exec "$container_name" ps -e -o pid=,args= >&2 || true
  docker exec "$container_name" find /root -maxdepth 1 -type s -name 'dynamic_profiling_socket_*' -print >&2 || true
  exit 72
fi
printf 'profile_rank=%s worker_pid=%s socket=%s\n' "$profile_rank" "$worker_pid" "/root/dynamic_profiling_socket_${worker_pid}" >"${artifact_dir}/profile-target.txt"

env PYTHONPATH="$repo_root/scripts${PYTHONPATH:+:$PYTHONPATH}" python3 "$repo_root/scripts/run_qwen35_profile_request.py" --base-url "$base_url" --model "$model" --dataset "$dataset" --dataset-sha256 "$dataset_sha256" --run-id "$run_id" --control-mode external-msprof --external-ready-file "$ready_file" --external-go-file "$go_file" --output "$request_artifact" &
request_pid=$!

deadline=$((SECONDS + readiness_timeout))
while [[ ! -e "$ready_file" ]] && (( SECONDS < deadline )); do
  if ! kill -0 "$request_pid" >/dev/null 2>&1; then
    wait "$request_pid"
  fi
  sleep 1
done
if [[ ! -e "$ready_file" ]]; then
  echo "profile request did not complete warmup" >&2
  exit 73
fi

mkfifo "$control_fifo"
docker exec -i "$container_name" /usr/local/Ascend/cann-9.1.0/bin/msprof --dynamic=on --pid="$worker_pid" --output="$profile_dir" --ascendcl=on --runtime-api=on --task-time=l2 --aic-metrics=PipeUtilization <"$control_fifo" >"$msprof_log" 2>&1 &
msprof_pid=$!
exec 9>"$control_fifo"
printf 'start\n' >&9

deadline=$((SECONDS + control_timeout))
while ! grep -q "start success" "$msprof_log" 2>/dev/null &&
    (( SECONDS < deadline )); do
  if ! kill -0 "$msprof_pid" >/dev/null 2>&1; then
    cat "$msprof_log" >&2
    wait "$msprof_pid"
  fi
  sleep 1
done
grep -q "start success" "$msprof_log" || {
  cat "$msprof_log" >&2
  echo "msprof did not start" >&2
  exit 74
}

printf 'go\n' >"$go_file"
wait "$request_pid"
request_pid=
printf 'stop\n' >&9

deadline=$((SECONDS + control_timeout))
while ! grep -q "stop success" "$msprof_log" 2>/dev/null &&
    (( SECONDS < deadline )); do
  if ! kill -0 "$msprof_pid" >/dev/null 2>&1; then
    cat "$msprof_log" >&2
    wait "$msprof_pid"
  fi
  sleep 1
done
grep -q "stop success" "$msprof_log" || {
  cat "$msprof_log" >&2
  echo "msprof did not stop" >&2
  exit 75
}
printf 'quit\n' >&9
exec 9>&-
wait "$msprof_pid"
msprof_pid=

prof_dir="$(find "$profile_dir" -mindepth 1 -maxdepth 1 -type d -name 'PROF_*' -print -quit)"
if [[ -z "$prof_dir" ]]; then
  echo "msprof did not emit a PROF_* directory" >&2
  exit 76
fi
docker exec "$container_name" /usr/local/Ascend/cann-9.1.0/bin/msprof --export=on --output="$prof_dir" >"$export_log" 2>&1

deadline=$((SECONDS + profile_flush_timeout))
while (( SECONDS < deadline )); do
  if find "$profile_dir" -type f -name 'op_summary_*.csv' -print -quit | grep -q .; then
    break
  fi
  sleep 5
done
if ! find "$profile_dir" -type f -name 'op_summary_*.csv' -print -quit | grep -q .; then
  echo "msprof did not emit op_summary_*.csv" >&2
  exit 77
fi

python3 "$repo_root/scripts/analyze_ascend_profile.py" "$profile_dir" --output "$hotspot_artifact"
docker logs "$container_name" >"$service_log" 2>&1
sha256sum "$request_artifact" "$hotspot_artifact" "$msprof_log" "$export_log" "$service_log" "$profile_metadata" "${artifact_dir}/container-inspect.json" "${artifact_dir}/profile-target.txt" >"${artifact_dir}/SHA256SUMS"
cat "$hotspot_artifact"

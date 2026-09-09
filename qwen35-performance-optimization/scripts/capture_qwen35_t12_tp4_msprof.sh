#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
container_name="${CONTAINER_NAME:?set CONTAINER_NAME to the exact live t12 container}"
expected_variant="${EXPECTED_VARIANT:-control}"
expected_output_root="${EXPECTED_OUTPUT_ROOT:?set EXPECTED_OUTPUT_ROOT to the immutable launcher output root}"
profile_dir="${PROFILE_DIR:?set PROFILE_DIR to the host directory mounted at /profile}"
artifact_dir="${ARTIFACT_DIR:?set ARTIFACT_DIR to a new directory under /cache/austinov}"
run_id="${PROFILE_RUN_ID:?set PROFILE_RUN_ID to a unique immutable id}"
port="${PORT:-10010}"
base_url="http://127.0.0.1:${port}"
model="${MODEL:-Qwen3-5/Qwen3.5-27B}"
dataset="${DATASET:-/cache/cch/query_rewrite.jsonl}"
dataset_sha256="${DATASET_SHA256:-a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e}"
control_timeout="${PROFILE_CONTROL_TIMEOUT_SECONDS:-180}"
request_timeout="${PROFILE_REQUEST_TIMEOUT_SECONDS:-900}"
flush_timeout="${PROFILE_FLUSH_TIMEOUT_SECONDS:-600}"
expected_image_id="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"

case "$expected_variant" in
  control|candidate) ;;
  *) echo "EXPECTED_VARIANT must be control or candidate" >&2; exit 64 ;;
esac
for path in "$expected_output_root" "$profile_dir" "$artifact_dir"; do
  case "$path" in
    /cache/austinov/*) ;;
    *) echo "all artifact paths must be under /cache/austinov: $path" >&2; exit 64 ;;
  esac
done
[[ -d "$expected_output_root" ]] || { echo "missing EXPECTED_OUTPUT_ROOT" >&2; exit 66; }
[[ -d "$profile_dir" ]] || { echo "missing PROFILE_DIR" >&2; exit 66; }
[[ ! -e "$artifact_dir" ]] || { echo "refusing to reuse ARTIFACT_DIR" >&2; exit 44; }
if find "$profile_dir" -mindepth 1 -print -quit | grep -q .; then
  echo "refusing non-empty PROFILE_DIR" >&2
  exit 44
fi
[[ "$port" =~ ^[0-9]+$ ]] || { echo "invalid PORT" >&2; exit 64; }

mkdir -p "$artifact_dir"
inspect_json="$artifact_dir/container-inspect.json"
docker inspect "$container_name" >"$inspect_json"
python3 - "$inspect_json" "$container_name" "$expected_variant" "$expected_output_root" "$profile_dir" "$expected_image_id" <<'PY'
import json
import sys

path, expected_name, expected_variant, expected_output, expected_profile, expected_image = sys.argv[1:]
items = json.load(open(path, encoding="utf-8"))
if len(items) != 1:
    raise SystemExit("expected exactly one container")
c = items[0]
if not c["State"]["Running"]:
    raise SystemExit("target container is not running")
if c["Name"].lstrip("/") != expected_name:
    raise SystemExit("container name mismatch")
labels = c["Config"].get("Labels") or {}
expected_labels = {
    "com.c1917797.qwen35-t12": "1",
    "com.c1917797.qwen35-variant": expected_variant,
    "com.c1917797.qwen35-output-root": expected_output,
}
for key, value in expected_labels.items():
    if labels.get(key) != value:
        raise SystemExit(f"label mismatch: {key}")
if c["Image"] != expected_image:
    raise SystemExit("official image id mismatch")
devices = {d["PathOnHost"] for d in c["HostConfig"].get("Devices") or []}
required = {f"/dev/davinci{i}" for i in range(4)}
forbidden = {f"/dev/davinci{i}" for i in range(4, 8)}
if not required.issubset(devices) or devices & forbidden:
    raise SystemExit(f"unsafe NPU device declaration: {sorted(devices)}")
mounts = {m["Destination"]: m for m in c.get("Mounts") or []}
profile = mounts.get("/profile")
if not profile or profile["Source"] != expected_profile or not profile["RW"]:
    raise SystemExit("/profile is not the expected writable artifact mount")
for destination in ("/experiment", "/opt/qwen35-t12-monkeypatch"):
    mount = mounts.get(destination)
    if not mount or mount["RW"]:
        raise SystemExit(f"{destination} is not read-only")
for destination in mounts:
    if destination.startswith("/vllm-workspace/vllm"):
        raise SystemExit("source overlay into vLLM workspace is forbidden")
env = set(c["Config"].get("Env") or [])
if "PROFILING_MODE=dynamic" not in env:
    raise SystemExit("container was not launched for dynamic profiling")
if expected_variant == "control":
    if "QWEN35_ASCEND_MONKEYPATCH=0" not in env:
        raise SystemExit("control unexpectedly enables monkeypatch")
    expected_operator_labels = {
        "com.c1917797.qwen35-operator-feature": "disabled",
        "com.c1917797.qwen35-operator-commit": "official-stock",
        "com.c1917797.qwen35-operator-package-sha256": "not-applicable",
    }
    if any(labels.get(key) != value for key, value in expected_operator_labels.items()):
        raise SystemExit("control unexpectedly mounts a custom operator")
PY

curl --fail --silent --max-time 5 "$base_url/health" >/dev/null || {
  echo "target service is not healthy" >&2
  exit 71
}

declare -a worker_pids=()
for rank in 0 1 2 3; do
  worker_pid="$(
    docker exec "$container_name" ps -e -o pid=,args= |
      awk -v label="Worker_TP${rank}" 'index($0, label) {print $1; exit}'
  )"
  [[ "$worker_pid" =~ ^[0-9]+$ ]] || {
    echo "unable to resolve Worker_TP${rank}" >&2
    exit 72
  }
  docker exec "$container_name" test -S "/root/dynamic_profiling_socket_${worker_pid}" || {
    echo "missing dynamic profiling socket for TP${rank}" >&2
    exit 72
  }
  worker_pids[$rank]="$worker_pid"
  mkdir -p "$profile_dir/rank${rank}"
  printf 'rank=%s pid=%s socket=%s\n' "$rank" "$worker_pid" "/root/dynamic_profiling_socket_${worker_pid}" >"$artifact_dir/rank${rank}-target.txt"
done

ready_file="$artifact_dir/request-ready"
go_file="$artifact_dir/request-go"
request_artifact="$artifact_dir/request.json"
request_log="$artifact_dir/request.log"
request_pid=
declare -a msprof_pids=()
declare -a control_fds=()
declare -a control_fifos=()

cleanup() {
  local status=$?
  if [[ -n "$request_pid" ]]; then
    kill "$request_pid" >/dev/null 2>&1 || true
    wait "$request_pid" >/dev/null 2>&1 || true
  fi
  for rank in 0 1 2 3; do
    if [[ -n "${control_fds[$rank]:-}" ]]; then
      fd="${control_fds[$rank]}"
      exec {fd}>&- || true
    fi
    if [[ -n "${msprof_pids[$rank]:-}" ]]; then
      kill "${msprof_pids[$rank]}" >/dev/null 2>&1 || true
      wait "${msprof_pids[$rank]}" >/dev/null 2>&1 || true
    fi
  done
  docker logs "$container_name" >"$artifact_dir/service.log" 2>&1 || true
  exit "$status"
}
trap cleanup EXIT INT TERM

env PYTHONPATH="$repo_root/scripts${PYTHONPATH:+:$PYTHONPATH}" python3 "$repo_root/scripts/run_qwen35_profile_request.py" --base-url "$base_url" --model "$model" --dataset "$dataset" --dataset-sha256 "$dataset_sha256" --run-id "$run_id" --control-mode external-msprof --external-ready-file "$ready_file" --external-go-file "$go_file" --timeout "$request_timeout" --output "$request_artifact" >"$request_log" 2>&1 &
request_pid=$!

deadline=$((SECONDS + request_timeout))
while [[ ! -e "$ready_file" ]] && (( SECONDS < deadline )); do
  if ! kill -0 "$request_pid" >/dev/null 2>&1; then
    wait "$request_pid"
  fi
  sleep 1
done
[[ -e "$ready_file" ]] || { echo "profile warmup did not finish" >&2; exit 73; }

for rank in 0 1 2 3; do
  fifo="$artifact_dir/rank${rank}-control.fifo"
  mkfifo "$fifo"
  control_fifos[$rank]="$fifo"
  docker exec -i "$container_name" /usr/local/Ascend/cann-9.1.0/bin/msprof --dynamic=on --pid="${worker_pids[$rank]}" --output="/profile/rank${rank}" --ascendcl=on --runtime-api=on --task-time=l2 --aic-metrics=PipeUtilization <"$fifo" >"$artifact_dir/rank${rank}-msprof.log" 2>&1 &
  msprof_pids[$rank]=$!
  exec {control_fd}>"$fifo"
  control_fds[$rank]="$control_fd"
  printf 'start\n' >&"$control_fd"
done

deadline=$((SECONDS + control_timeout))
while (( SECONDS < deadline )); do
  all_started=1
  for rank in 0 1 2 3; do
    grep -q "start success" "$artifact_dir/rank${rank}-msprof.log" 2>/dev/null ||
      all_started=0
    if ! kill -0 "${msprof_pids[$rank]}" >/dev/null 2>&1; then
      cat "$artifact_dir/rank${rank}-msprof.log" >&2
      wait "${msprof_pids[$rank]}"
    fi
  done
  [[ "$all_started" == 1 ]] && break
  sleep 1
done
for rank in 0 1 2 3; do
  grep -q "start success" "$artifact_dir/rank${rank}-msprof.log" || {
    echo "msprof did not start on TP${rank}" >&2
    exit 74
  }
done

printf 'go\n' >"$go_file"
wait "$request_pid"
request_pid=

for rank in 0 1 2 3; do
  printf 'stop\n' >&"${control_fds[$rank]}"
done
deadline=$((SECONDS + control_timeout))
while (( SECONDS < deadline )); do
  all_stopped=1
  for rank in 0 1 2 3; do
    grep -q "stop success" "$artifact_dir/rank${rank}-msprof.log" 2>/dev/null ||
      all_stopped=0
  done
  [[ "$all_stopped" == 1 ]] && break
  sleep 1
done
for rank in 0 1 2 3; do
  grep -q "stop success" "$artifact_dir/rank${rank}-msprof.log" || {
    echo "msprof did not stop on TP${rank}" >&2
    exit 75
  }
  printf 'quit\n' >&"${control_fds[$rank]}"
  fd="${control_fds[$rank]}"
  exec {fd}>&-
  control_fds[$rank]=
done
for rank in 0 1 2 3; do
  wait "${msprof_pids[$rank]}"
  msprof_pids[$rank]=
done

for rank in 0 1 2 3; do
  prof_dir="$(
    find "$profile_dir/rank${rank}" -mindepth 1 -maxdepth 1 -type d -name 'PROF_*' -print -quit
  )"
  [[ -n "$prof_dir" ]] || {
    echo "msprof did not emit PROF_* for TP${rank}" >&2
    exit 76
  }
  prof_base="$(basename "$prof_dir")"
  docker exec "$container_name" /usr/local/Ascend/cann-9.1.0/bin/msprof --export=on --output="/profile/rank${rank}/${prof_base}" >"$artifact_dir/rank${rank}-export.log" 2>&1
done

deadline=$((SECONDS + flush_timeout))
while (( SECONDS < deadline )); do
  complete=1
  for rank in 0 1 2 3; do
    find "$profile_dir/rank${rank}" -type f -name 'op_summary_*.csv' -print -quit | grep -q . || complete=0
  done
  [[ "$complete" == 1 ]] && break
  sleep 5
done
for rank in 0 1 2 3; do
  find "$profile_dir/rank${rank}" -type f -name 'op_summary_*.csv' -print -quit | grep -q . || {
      echo "missing op_summary CSV for TP${rank}" >&2
      exit 77
    }
  python3 "$repo_root/scripts/analyze_ascend_profile.py" "$profile_dir/rank${rank}" --output "$artifact_dir/rank${rank}-hotspots.json"
done
python3 "$repo_root/scripts/analyze_ascend_profile.py" "$profile_dir" --output "$artifact_dir/combined-hotspots.json"
docker logs "$container_name" >"$artifact_dir/service.log" 2>&1

python3 - "$artifact_dir" "$run_id" "$expected_variant" "$profile_dir" <<'PY'
import json
import sys
from pathlib import Path

artifact_dir, run_id, variant, profile_dir = sys.argv[1:]
payload = {
    "schema": "qwen35-t12-tp4-msprof-capture/v1",
    "performance_evidence": False,
    "performance_note": "Profiler overhead invalidates TTFT/TPOT acceptance.",
    "run_id": run_id,
    "variant": variant,
    "profile_dir": profile_dir,
    "ranks": [0, 1, 2, 3],
    "task_time": "l2",
    "aic_metrics": "PipeUtilization",
}
Path(artifact_dir, "profile-metadata.json").write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

find "$artifact_dir" -maxdepth 1 -type f ! -name SHA256SUMS -print0 |
  sort -z |
  xargs -0 sha256sum >"$artifact_dir/SHA256SUMS"
cat "$artifact_dir/combined-hotspots.json"

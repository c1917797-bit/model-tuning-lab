#!/usr/bin/env bash
set -u

PHASE=$1
RUN=$2
SERVER=$3
ENDPOINT=$4
PREFIX_LABEL=$5
EXPECTED_CPUSET=$6
SNAPSHOT=$7

ROOT=/cache/austinov/eval-runs/exp-20260903-qwen38-prefix-cache-general-eval
WT=/opt/host/vnf/austinov/worktrees/exp-20260904-qwen38-prefix-cache-general-eval-final
OUT=$ROOT/$PHASE
IMG=quay.io/ascend/vllm-ascend:v0.23.0
CLIENT=qwen38_perf_client_${PHASE}_${RUN}
mkdir -p "$OUT"
rm -f "$OUT/$RUN."{json,console.log,resources.log,contaminated,aborted,started_at,ended_at,environment.txt,docker_exec_events.log}
docker rm -f "$CLIENT" >/dev/null 2>&1 || true

START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "$START" > "$OUT/$RUN.started_at"
{
  echo start=$START
  echo git_head=$(git -C "$WT" rev-parse HEAD)
  echo snapshot=$SNAPSHOT
  echo snapshot_sha256=$(sha256sum "$SNAPSHOT" | awk '{print $1}')
  echo server_container=$SERVER
  echo server_cpuset=$(docker inspect "$SERVER" --format '{{.HostConfig.CpusetCpus}}' 2>/dev/null || true)
  echo client_cpuset=96-111
  echo endpoint=$ENDPOINT
  echo prefix_caching=$PREFIX_LABEL
  echo input_tokens=2048
  echo output_tokens=40
  echo concurrency=8
} > "$OUT/$RUN.environment.txt"

HC=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$ENDPOINT/health" 2>/dev/null || true)
MEM=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
CPUSET=$(docker inspect "$SERVER" --format '{{.HostConfig.CpusetCpus}}' 2>/dev/null || true)
SERVER_CID=$(docker inspect "$SERVER" --format '{{.Id}}' 2>/dev/null || true)

target_devices_ok() {
  [ -n "$SERVER_CID" ] || return 1
  for DEV in 4 5 6 7; do
    ROWS=$(npu-smi info 2>/dev/null | awk -F'|' -v dev="$DEV" '
      {
        f=$2; gsub(/^[ \t]+|[ \t]+$/, "", f); split(f,a,/[ \t]+/)
        pid=$3; name=$4
        gsub(/^[ \t]+|[ \t]+$/, "", pid); gsub(/^[ \t]+|[ \t]+$/, "", name)
        if (a[1] == dev && pid ~ /^[0-9]+$/) print pid "|" name
      }')
    [ "$(printf '%s\n' "$ROWS" | sed '/^$/d' | wc -l)" -eq 1 ] || return 1
    PID=${ROWS%%|*}
    NAME=${ROWS#*|}
    [ "$NAME" = "VLLMWorker_TP" ] || return 1
    grep -q "$SERVER_CID" "/proc/$PID/cgroup" 2>/dev/null || return 1
  done
}

if [ "$HC" != 200 ] || [ "$MEM" -lt $((20*1024*1024)) ] || [ "$CPUSET" != "$EXPECTED_CPUSET" ] || ! target_devices_ok; then
  N03=$(npu-smi info 2>/dev/null | awk -F'|' '{f=$2; gsub(/^[ \t]+|[ \t]+$/, "", f); split(f,a,/[ \t]+/); pid=$3; gsub(/^[ \t]+|[ \t]+$/, "", pid); if (a[1] ~ /^[0-3]$/ && pid ~ /^[0-9]+$/) n++} END{print n+0}')
  echo "preflight target_npu_ok=no background_npu03=$N03 health=$HC mem=$MEM cpuset=$CPUSET expected=$EXPECTED_CPUSET"
  exit 70
fi

SNAP_DIR=$(dirname "$SNAPSHOT")
SNAP_NAME=$(basename "$SNAPSHOT")
CID=$(docker run -d --name "$CLIENT" --network host --cpuset-cpus=96-111 \
  -e PYTHONPYCACHEPREFIX=/tmp/pycache \
  -v "$WT:/repo:ro" -v "$SNAP_DIR:/snapshot:ro" -v "$OUT:/out:rw" \
  "$IMG" python3 /repo/scripts/qwen38_perf_2k40.py \
  --base-url "$ENDPOINT" --model qwen38 --snapshot "/snapshot/$SNAP_NAME" \
  --output "/out/$RUN.json" --concurrency 8 --timeout 180)
echo client_id=$CID >> "$OUT/$RUN.environment.txt"

ABORT=0
while [ "$(docker inspect -f '{{.State.Running}}' "$CLIENT" 2>/dev/null || echo false)" = true ]; do
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  {
    echo "=== $TS ==="
    echo "load $(cat /proc/loadavg)"
    grep -E 'MemAvailable|MemFree|Cached' /proc/meminfo
    npu-smi info 2>/dev/null | tail -34
  } >> "$OUT/$RUN.resources.log"
  N03=$(npu-smi info 2>/dev/null | awk -F'|' '{f=$2; gsub(/^[ \t]+|[ \t]+$/, "", f); split(f,a,/[ \t]+/); pid=$3; gsub(/^[ \t]+|[ \t]+$/, "", pid); if (a[1] ~ /^[0-3]$/ && pid ~ /^[0-9]+$/) n++} END{print n+0}')
  echo "$TS background_npu_0_3_processes=$N03" >> "$OUT/$RUN.resources.log"
  MEM=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
  HC=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "$ENDPOINT/health" 2>/dev/null || true)
  if ! target_devices_ok; then echo "$TS unexpected_target_npu_4_7_activity" >> "$OUT/$RUN.contaminated"; echo "$TS guard_abort_target_npu_4_7" > "$OUT/$RUN.aborted"; ABORT=79; docker rm -f "$CLIENT" >/dev/null 2>&1 || true; break; fi
  if [ "$MEM" -lt $((20*1024*1024)) ]; then echo "$TS guard_abort_low_mem memavail_kb=$MEM" > "$OUT/$RUN.aborted"; ABORT=76; docker rm -f "$CLIENT" >/dev/null 2>&1 || true; break; fi
  if [ "$HC" != 200 ]; then echo "$TS guard_abort_health=$HC" > "$OUT/$RUN.aborted"; ABORT=77; docker rm -f "$CLIENT" >/dev/null 2>&1 || true; break; fi
  sleep 5
done

if [ "$ABORT" -eq 0 ]; then
  RC=$(docker inspect -f '{{.State.ExitCode}}' "$CLIENT")
  docker logs "$CLIENT" > "$OUT/$RUN.console.log" 2>&1 || true
  docker rm "$CLIENT" >/dev/null 2>&1 || true
else
  RC=$ABORT
fi
END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "$END" > "$OUT/$RUN.ended_at"

timeout 6 docker events --since "$START" --until "$END" --filter type=container --filter container="$SERVER" --filter event=exec_create --format '{{.Time}} {{.Action}} {{.Actor.Attributes.name}} {{.Actor.Attributes.execID}}' > "$OUT/$RUN.docker_exec_events.log" 2>/dev/null || true
if [ -s "$OUT/$RUN.docker_exec_events.log" ]; then
  echo "$END foreign_docker_exec_on_server" >> "$OUT/$RUN.contaminated"
  [ "$RC" -eq 0 ] && RC=78
fi
if [ "$RC" -ne 0 ]; then
  echo "RUN_INVALID rc=$RC"
  cat "$OUT/$RUN.aborted" 2>/dev/null || true
  cat "$OUT/$RUN.contaminated" 2>/dev/null || true
  cat "$OUT/$RUN.console.log" 2>/dev/null || true
  exit "$RC"
fi

sha256sum "$OUT/$RUN.json" "$OUT/$RUN.resources.log"
python3 - "$OUT/$RUN.json" <<'PY'
import json,sys
s=json.load(open(sys.argv[1]))['summary']
print(json.dumps(s, indent=2, sort_keys=True))
PY

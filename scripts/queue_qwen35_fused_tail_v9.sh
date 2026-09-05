#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
overlap_log="${OVERLAP_LOG:-/cache/austinov/p0/overlap_ab.log}"
mc2_log="${MC2_LOG:-/cache/austinov/p0/mc2_ab.log}"
output_parent="${OUTPUT_PARENT:-/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates}"
launcher="${LAUNCHER:-$repo_root/scripts/run_qwen35_tp4_candidate_vs_original.sh}"
docker_bin="${DOCKER_BIN:-docker}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
ss_bin="${SS_BIN:-ss}"
port="${PORT:-10010}"
wait_timeout_seconds="${WAIT_TIMEOUT_SECONDS:-7200}"
poll_seconds="${POLL_SECONDS:-15}"
stable_idle_checks="${STABLE_IDLE_CHECKS:-4}"
idle_check_interval_seconds="${IDLE_CHECK_INTERVAL_SECONDS:-15}"
reservation_ignore_names="${NPU_RESERVATION_IGNORE_NAMES-/vllm-ep-310p-research-910b-monitor,/vllm-19.1-Qwen3.5-4B-1065}"

log() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

require_positive_integer() {
  local name="$1"
  local value="$2"
  if [[ ! "$value" =~ ^[0-9]+$ ]] || (( value < 1 )); then
    echo "$name must be a positive integer, got: $value" >&2
    exit 64
  fi
}

require_nonnegative_integer() {
  local name="$1"
  local value="$2"
  if [[ ! "$value" =~ ^[0-9]+$ ]]; then
    echo "$name must be a nonnegative integer, got: $value" >&2
    exit 64
  fi
}

require_positive_integer WAIT_TIMEOUT_SECONDS "$wait_timeout_seconds"
require_nonnegative_integer POLL_SECONDS "$poll_seconds"
require_positive_integer STABLE_IDLE_CHECKS "$stable_idle_checks"
require_nonnegative_integer IDLE_CHECK_INTERVAL_SECONDS "$idle_check_interval_seconds"

has_external_completion_markers() {
  [[ -f "$overlap_log" ]] &&
    grep -q 'OVERLAP_AB_DONE' "$overlap_log" &&
    [[ -f "$mc2_log" ]] &&
    grep -q 'MC2_AB_DONE' "$mc2_log"
}

container_reservations() {
  local running_id
  for running_id in $("$docker_bin" ps -q); do
    "$docker_bin" inspect "$running_id" --format '{{.Name}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}'
  done | awk -v ignored_csv="$reservation_ignore_names" '
    BEGIN {
      split(ignored_csv, ignored_names, ",")
      for (item in ignored_names) {
        ignored[ignored_names[item]] = 1
      }
    }
    $0 ~ /\/dev\/davinci[4-7]([[:space:]]|$)/ && !($1 in ignored)
  '
}

npu_processes() {
  "$npu_smi_bin" info | awk -F '|' '
    $2 ~ /^[[:space:]]*[4-7][[:space:]]+[0-9]+[[:space:]]*$/ &&
    $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {
      gsub(/[[:space:]]/, "", $2)
      gsub(/[[:space:]]/, "", $3)
      print "NPU" substr($2, 1, 1) ":pid=" $3
    }
  '
}

port_is_listening() {
  if ! command -v "$ss_bin" >/dev/null 2>&1; then
    return 1
  fi
  "$ss_bin" -lntH | awk -v port="$port" '
    $4 ~ (":" port "$") { found = 1 }
    END { exit(found ? 0 : 1) }
  '
}

resources_are_idle() {
  [[ -z "$(container_reservations)" ]] &&
    [[ -z "$(npu_processes)" ]] &&
    ! port_is_listening
}

deadline=$((SECONDS + wait_timeout_seconds))
log "waiting for OVERLAP_AB_DONE and MC2_AB_DONE without touching NPU0-3"
while ! has_external_completion_markers; do
  if (( SECONDS >= deadline )); then
    echo "timed out waiting for external completion markers" >&2
    exit 75
  fi
  sleep "$poll_seconds"
done

log "external stages completed; requiring stable NPU4-7 and port $port idle window"
stable=0
while (( stable < stable_idle_checks )); do
  if resources_are_idle; then
    stable=$((stable + 1))
    log "idle check $stable/$stable_idle_checks passed"
  else
    stable=0
    log "assigned resources still busy; stable counter reset"
  fi
  if (( stable < stable_idle_checks )); then
    if (( SECONDS >= deadline )); then
      echo "timed out waiting for stable NPU4-7 idle window" >&2
      exit 75
    fi
    sleep "$idle_check_interval_seconds"
  fi
done

stamp="${STAMP_OVERRIDE:-$(date -u +%Y%m%dT%H%M%SZ)}"
run_id="fused-tail-v9-$stamp"
output_root="$output_parent/mmar-add-rmsnorm-v9-$stamp"
log "launching $run_id into immutable root $output_root"

exec env RUN_ID="$run_id" OUTPUT_ROOT="$output_root" CANDIDATE_MODE="mmar-on-weight-prefetch-gateup-0p1-fused-tail" CANDIDATE_ID="mmar-add-rmsnorm-decode-v9" DEVICE_SET="4-7" PORT="$port" READINESS_TIMEOUT_SECONDS="${READINESS_TIMEOUT_SECONDS:-1800}" "$launcher"

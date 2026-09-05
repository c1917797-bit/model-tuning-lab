#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
r15_log="${R15_LOG:-/cache/austinov/p0/r15.log}"
r15_marker="${R15_MARKER:-R15_DONE}"
output_parent="${OUTPUT_PARENT:-/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates}"
launcher="${LAUNCHER:-$repo_root/scripts/run_qwen35_tp4_candidate_vs_original.sh}"
docker_bin="${DOCKER_BIN:-docker}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
ss_bin="${SS_BIN:-ss}"
port="${PORT:-10010}"
run_label="${RUN_LABEL:-fused-tail-v10}"
output_label="${OUTPUT_LABEL:-mmar-add-rmsnorm-v10}"
candidate_id="${CANDIDATE_ID:-mmar-add-rmsnorm-decode-v10}"
protected_chain_label="${PROTECTED_CHAIN_LABEL:-p0_r15}"
wait_timeout_seconds="${WAIT_TIMEOUT_SECONDS:-14400}"
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

external_chain_is_done() {
  [[ -f "$r15_log" ]] && grep -qF "$r15_marker" "$r15_log"
}

container_reservations() {
  local running_id
  for running_id in $("$docker_bin" ps -q); do
    "$docker_bin" inspect --format '{{.Name}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}' "$running_id"
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
log "waiting for $r15_marker without touching NPU0-3 or $protected_chain_label"
while ! external_chain_is_done; do
  if (( SECONDS >= deadline )); then
    echo "timed out waiting for external completion marker" >&2
    exit 75
  fi
  sleep "$poll_seconds"
done

log "external chain completed; requiring stable NPU4-7 and port $port idle window"
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
run_id="$run_label-$stamp"
output_root="$output_parent/$output_label-$stamp"
log "launching $run_id into immutable root $output_root"

exec env RUN_ID="$run_id" OUTPUT_ROOT="$output_root" CANDIDATE_MODE="mmar-on-weight-prefetch-gateup-0p1-fused-tail" CANDIDATE_ID="$candidate_id" DEVICE_SET="4-7" PORT="$port" READINESS_TIMEOUT_SECONDS="${READINESS_TIMEOUT_SECONDS:-1800}" "$launcher"

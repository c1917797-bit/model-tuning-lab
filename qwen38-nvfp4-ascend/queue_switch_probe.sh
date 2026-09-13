#!/usr/bin/env bash
# Queue one diagnostic behind one exact previously verified controller.
set -Eeuo pipefail
prior_pid="${1:?prior controller PID}"
prior_out="${2:?prior artifact path}"
[[ "$prior_pid" =~ ^[0-9]+$ && "$prior_out" == /cache/austinov/eval-runs/switch12h-* ]] || exit 64
code="$(cd "$(dirname "$0")" && pwd)"
for i in $(seq 1 720); do
 if [[ ! -r "/proc/$prior_pid/cmdline" ]]; then break; fi
 command_line="$(tr '\0' ' ' < "/proc/$prior_pid/cmdline")"
 [[ "$command_line" == *"run_switch_canary.sh qwen3 $prior_out"* ]] || break
 [[ "$i" != 720 ]] || exit 75
 sleep 10
done
out="$(mktemp -d /cache/austinov/eval-runs/switch12h-qwen38-probe-20260913-XXXXXX)"
printf '%s\n' "$out" > "$prior_out/probe-next-artifact.txt"
bash "$code/run_switch_probe.sh" qwen38 "$out" > "$out/controller.log" 2>&1


#!/usr/bin/env bash
set -euo pipefail

# Detach the lease-owning launcher from the caller's RPC/session lifetime.
# The launcher itself waits for the exact one-shot container and therefore
# retains fd 9 until that container exits.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
launcher="$repo_root/qwen35-performance-optimization/scripts/run_qwen35_gdn_runtime_t12_npu03.sh"
: "${VARIANT:?set VARIANT}"
: "${OUTPUT_ROOT:?set OUTPUT_ROOT to a new directory under /cache/austinov}"

case "$VARIANT" in
  candidate|candidate-prefill|candidate-prefill-t21|candidate-prefill-no-prefetch|candidate-super-kernel|candidate-fused-prefill|candidate-fused-prefill-decode-view|candidate-fused-prefill-conv-prepack|candidate-fused-prefill-conv-prepack-fused-decode|control) ;;
  *) echo "unsupported VARIANT: $VARIANT" >&2; exit 64 ;;
esac
case "$OUTPUT_ROOT" in
  /cache/austinov/*) ;;
  *) echo "OUTPUT_ROOT must be under /cache/austinov" >&2; exit 64 ;;
esac

supervisor_log="${OUTPUT_ROOT}.supervisor.log"
supervisor_pid_file="${OUTPUT_ROOT}.supervisor.pid"
[[ ! -e "$OUTPUT_ROOT" ]] || {
  echo "refusing to reuse OUTPUT_ROOT: $OUTPUT_ROOT" >&2
  exit 44
}
[[ ! -e "$supervisor_log" && ! -e "$supervisor_pid_file" ]] || {
  echo "refusing to reuse supervisor artifacts" >&2
  exit 44
}
command -v setsid >/dev/null

umask 022
nohup setsid "$launcher" >"$supervisor_log" 2>&1 </dev/null &
supervisor_pid=$!
printf '%s\n' "$supervisor_pid" >"$supervisor_pid_file"

sleep 2
if ! kill -0 "$supervisor_pid" 2>/dev/null; then
  set +e
  wait "$supervisor_pid"
  rc=$?
  set -e
  echo "supervisor exited during startup with code $rc" >&2
  sed -n '1,200p' "$supervisor_log" >&2
  exit "$rc"
fi

printf 'supervisor_pid=%s\n' "$supervisor_pid"
printf 'supervisor_log=%s\n' "$supervisor_log"

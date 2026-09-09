#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
capture="$root/qwen35-performance-optimization/scripts/capture_qwen35_t12_tp4_msprof.sh"

bash -n "$capture"
grep -Fq 'com.c1917797.qwen35-t12' "$capture"
grep -Fq 'official image id mismatch' "$capture"
grep -Fq 'unsafe NPU device declaration' "$capture"
grep -Fq 'source overlay into vLLM workspace is forbidden' "$capture"
grep -Fq 'PROFILING_MODE=dynamic' "$capture"
grep -Fq 'QWEN35_ASCEND_MONKEYPATCH=0' "$capture"
grep -Fq 'Worker_TP${rank}' "$capture"
grep -Fq 'dynamic_profiling_socket_${worker_pid}' "$capture"
grep -Fq -- '--task-time=l2' "$capture"
grep -Fq -- '--aic-metrics=PipeUtilization' "$capture"
grep -Fq 'for rank in 0 1 2 3' "$capture"
grep -Fq 'performance_evidence": False' "$capture"
! grep -Eq 'docker[[:space:]]+(run|stop|commit|cp)([[:space:]]|$)' "$capture"
! grep -Fq -- '--device /dev/davinci4' "$capture"

echo 'PASS: t12 TP4 msprof attach contract'

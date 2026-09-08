#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script="$root/qwen35-performance-optimization/scripts/stop_qwen35_gdn_runtime_t12.sh"

bash -n "$script"
grep -Fq 'com.c1917797.qwen35-t12' "$script"
grep -Fq 'com.c1917797.qwen35-variant' "$script"
grep -Fq 'com.c1917797.qwen35-output-root' "$script"
grep -Fq 'docker stop --time 30 "$container_name"' "$script"
! grep -Eq 'docker (rm|kill)|docker stop .*(\$\(|\*|ps -q)' "$script"

echo 'PASS: exact-container t12 stop contract'

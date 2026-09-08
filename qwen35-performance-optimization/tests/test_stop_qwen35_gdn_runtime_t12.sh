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

docker() {
  case "$1" in
    inspect)
      case "$3" in
        *qwen35-t12*) printf '%s\n' 1 ;;
        *qwen35-variant*) printf '%s\n' candidate ;;
        *qwen35-output-root*) printf '%s\n' /cache/test-output ;;
        *) return 91 ;;
      esac
      ;;
    stop)
      [[ "$2" == --time && "$3" == 30 &&
         "$4" == qwen35_gdn_runtime_t12_candidate_npu03 ]]
      printf '%s\n' qwen35_gdn_runtime_t12_candidate_npu03
      ;;
    *) return 92 ;;
  esac
}
export -f docker
stop_output="$(mktemp)"
trap 'rm -f "$stop_output"' EXIT
VARIANT=candidate OUTPUT_ROOT=/cache/test-output \
  bash "$script" >"$stop_output"
grep -Fxq qwen35_gdn_runtime_t12_candidate_npu03 "$stop_output"

echo 'PASS: exact-container t12 stop contract'

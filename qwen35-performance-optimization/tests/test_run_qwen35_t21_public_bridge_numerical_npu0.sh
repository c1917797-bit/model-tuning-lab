#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script="$repo_root/scripts/run_qwen35_t21_public_bridge_numerical_npu0.sh"
tool="$repo_root/tools/qwen35_t21_public_bridge_numerical.py"

bash -n "$script"
python3 -m py_compile "$tool"
grep -F -- '--device /dev/davinci0' "$script" >/dev/null
for forbidden in davinci1 davinci2 davinci3 davinci4 davinci5 davinci6 davinci7; do
  ! grep -F -- "--device /dev/$forbidden" "$script"
done
grep -F 'flock -w' "$script" >/dev/null
grep -F 'physical NPU0-3 are occupied' "$script" >/dev/null
grep -F 'view_vs_contiguous_bit_exact' "$tool" >/dev/null
grep -F 'STRESS_ITERATIONS' "$tool" >/dev/null
echo "PASS: T21 public bridge numerical runner contract"

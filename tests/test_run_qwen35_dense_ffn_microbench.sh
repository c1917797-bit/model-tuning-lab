#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runner="$repo_root/scripts/run_qwen35_dense_ffn_microbench.sh"

grep -q '^physical_npu=4$' "$runner"
grep -q '^logical_npu=0$' "$runner"
grep -q -- '--device /dev/davinci4:/dev/davinci0' "$runner"
grep -q -- '--cpuset-cpus 0-23' "$runner"
grep -q 'physical NPU4 is not idle' "$runner"
grep -q 'forbidden_physical_npus=0,1,2,3' "$runner"
grep -q 'ASCEND_RT_VISIBLE_DEVICES="$logical_npu"' "$runner"

if grep -q 'DEVICE_SET' "$runner"; then
  echo "single-card runner must not allow resource remapping" >&2
  exit 1
fi
if grep -Eq -- '--device /dev/davinci[0-3](:|/)' "$runner"; then
  echo "runner unexpectedly maps a forbidden physical NPU" >&2
  exit 1
fi
if grep -q -- '--quantization' "$runner"; then
  echo "runner unexpectedly enables quantization" >&2
  exit 1
fi

echo "PASS: dense FFN microbenchmark resource guards"

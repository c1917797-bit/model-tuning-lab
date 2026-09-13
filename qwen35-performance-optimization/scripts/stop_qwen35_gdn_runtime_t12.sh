#!/usr/bin/env bash
set -euo pipefail

variant="${VARIANT:?set VARIANT to candidate, candidate-prefill, candidate-prefill-t21, candidate-prefill-no-prefetch, candidate-super-kernel, or control}"
output_root="${OUTPUT_ROOT:?set OUTPUT_ROOT to the exact service artifact directory}"
case "$variant" in
  candidate|candidate-prefill|candidate-prefill-t21|candidate-prefill-no-prefetch|candidate-super-kernel|candidate-fused-prefill|candidate-fused-prefill-decode-view|candidate-fused-prefill-conv-prepack|control) ;;
  *) echo "VARIANT must be candidate, candidate-prefill, candidate-prefill-t21, candidate-prefill-no-prefetch, candidate-super-kernel, or control" >&2; exit 64 ;;
esac
container_name="${CONTAINER_NAME:-qwen35_gdn_runtime_t12_${variant}_npu03}"

actual_marker="$(
  docker inspect --format '{{index .Config.Labels "com.c1917797.qwen35-t12"}}' \
    "$container_name"
)"
actual_variant="$(
  docker inspect --format '{{index .Config.Labels "com.c1917797.qwen35-variant"}}' \
    "$container_name"
)"
actual_output_root="$(
  docker inspect --format '{{index .Config.Labels "com.c1917797.qwen35-output-root"}}' \
    "$container_name"
)"
if [[ "$actual_marker" != 1 ||
      "$actual_variant" != "$variant" ||
      "$actual_output_root" != "$output_root" ]]; then
  echo "refusing to stop container with mismatched t12 identity" >&2
  exit 45
fi

docker stop --time 30 "$container_name"

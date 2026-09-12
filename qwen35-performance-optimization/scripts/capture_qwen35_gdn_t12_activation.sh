#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
checker="$repo_root/qwen35-performance-optimization/scripts/check_qwen35_gdn_t12_activation.py"
port="${PORT:-10010}"
: "${OUTPUT_ROOT:?set OUTPUT_ROOT to the live t12 service artifact directory}"

[[ -d "$OUTPUT_ROOT" ]] || { echo "missing OUTPUT_ROOT: $OUTPUT_ROOT" >&2; exit 66; }
[[ -f "$OUTPUT_ROOT/service.log" ]] || { echo "missing service log" >&2; exit 66; }
[[ -f "$OUTPUT_ROOT/variant.txt" ]] || { echo "missing variant.txt" >&2; exit 66; }
variant="$(cat "$OUTPUT_ROOT/variant.txt")"
case "$variant" in
  candidate|candidate-prefill|candidate-prefill-t21|candidate-prefill-no-prefetch|candidate-super-kernel|control) ;;
  *) echo "invalid recorded variant: $variant" >&2; exit 66 ;;
esac
container_name="${CONTAINER_NAME:-qwen35_gdn_runtime_t12_${variant}_npu03}"
for output in container-inspect.live.json container-top.live.txt npu-smi.live.txt models.live.json container-logs.live.txt activation-report.json; do
  [[ ! -e "$OUTPUT_ROOT/$output" ]] || {
    echo "refusing to overwrite activation artifact: $OUTPUT_ROOT/$output" >&2
    exit 44
  }
done

docker inspect "$container_name" >"$OUTPUT_ROOT/container-inspect.live.json"
docker top "$container_name" -eo pid,ppid,args >"$OUTPUT_ROOT/container-top.live.txt"
npu-smi info >"$OUTPUT_ROOT/npu-smi.live.txt"
curl -fsS "http://127.0.0.1:$port/v1/models" >"$OUTPUT_ROOT/models.live.json"
docker logs "$container_name" >"$OUTPUT_ROOT/container-logs.live.txt" 2>&1

PYTHONDONTWRITEBYTECODE=1 python3 "$checker" \
  --log "$OUTPUT_ROOT/container-logs.live.txt" \
  --inspect "$OUTPUT_ROOT/container-inspect.live.json" \
  --npu "$OUTPUT_ROOT/npu-smi.live.txt" \
  --top "$OUTPUT_ROOT/container-top.live.txt" \
  --models "$OUTPUT_ROOT/models.live.json" \
  --variant "$variant" \
  --output "$OUTPUT_ROOT/activation-report.json"

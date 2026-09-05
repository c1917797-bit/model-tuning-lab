#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
service_launcher="$repo_root/scripts/run_qwen35_shortgpt_bi_service.sh"
collector="$repo_root/scripts/collect_qwen35_shortgpt_bi.py"
analyzer="$repo_root/scripts/analyze_qwen35_shortgpt_bi.py"
dataset="${DATASET:-/cache/cch/query_rewrite.jsonl}"
dataset_sha256="${DATASET_SHA256:-a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e}"
source_commit="${SHORTGPT_SOURCE_COMMIT:-18c4d061529d226dd0d699d9e3e1df16dadf29d7}"
port="${PORT:-10020}"
model_name="${MODEL_NAME:-Qwen3-5/Qwen3.5-27B}"
container_name="${CONTAINER_NAME:-qwen35_shortgpt_bi_npu4_7}"
readiness_timeout="${READINESS_TIMEOUT_SECONDS:-1800}"
stamp="${STAMP_OVERRIDE:-$(date -u +%Y%m%dT%H%M%SZ)}"
output_root="${OUTPUT_ROOT:-/cache/austinov/eval-runs/exp-20260905-qwen35-shortgpt/bi-$stamp}"
bi_dir="$output_root/bi"
started=0

case "$output_root" in
  /cache/austinov/eval-runs/exp-20260905-qwen35-shortgpt/*) ;;
  *)
    echo "OUTPUT_ROOT is outside the ShortGPT experiment root" >&2
    exit 64
    ;;
esac
if [[ -e "$output_root" ]]; then
  echo "refusing to reuse output root: $output_root" >&2
  exit 44
fi
mkdir -p "$output_root"

capture_logs() {
  if (( started )); then
    docker logs "$container_name" >"$output_root/service.log" 2>&1 || true
  fi
}

cleanup() {
  capture_logs
  if (( started )); then
    docker rm -f "$container_name" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

QWEN35_BI_DIR="$bi_dir" CONTAINER_NAME="$container_name" PORT="$port" "$service_launcher" >"$output_root/container-id.txt"
started=1

ready=0
deadline=$((SECONDS + readiness_timeout))
while (( SECONDS < deadline )); do
  if [[ -n "$(docker ps -q --filter "name=^/$container_name$")" ]] &&
      curl -fsS --max-time 5 "http://127.0.0.1:$port/health" >/dev/null; then
    ready=1
    break
  fi
  if [[ -n "$(docker ps -aq --filter "name=^/$container_name$" --filter status=exited)" ]]; then
    break
  fi
  sleep 10
done
if (( ! ready )); then
  echo "ShortGPT BI service did not become ready" >&2
  exit 70
fi

# Eager startup/profile calls may execute the model before readiness. Preserve
# those aggregate records separately and exclude them from request ranking.
mkdir "$output_root/startup-bi"
shopt -s nullglob
startup_records=("$bi_dir"/*.jsonl)
if (( ${#startup_records[@]} )); then
  mv -- "${startup_records[@]}" "$output_root/startup-bi/"
fi
shopt -u nullglob

set +e
python3 "$collector" --base-url "http://127.0.0.1:$port" --model "$model_name" --dataset "$dataset" --dataset-sha256 "$dataset_sha256" --limit 32 --seed 1024 --source-commit "$source_commit" --output "$output_root/collection.json"
collect_rc=$?
set -e

capture_logs
docker rm -f "$container_name" >/dev/null
started=0

set +e
python3 "$analyzer" "$bi_dir" --output "$output_root/analysis.json" --expected-layers 64 --stability-splits 4 --candidate-sizes 8,16,20 --min-observations-per-layer 8 --min-spearman 0.80
analysis_rc=$?
set -e

find "$output_root" -type f ! -name SHA256SUMS -print0 |
  sort -z |
  xargs -0 sha256sum >"$output_root/SHA256SUMS"
if (( collect_rc != 0 )); then
  echo "Block Influence collection failed with status $collect_rc" >&2
  exit "$collect_rc"
fi
if (( analysis_rc != 0 )); then
  echo "Block Influence ranking is not ready to freeze (status $analysis_rc)" >&2
  exit "$analysis_rc"
fi
printf 'SHORTGPT_BI_READY %s\n' "$output_root"

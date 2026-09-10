#!/usr/bin/env bash
# Execute generated HumanEval code only in a tightly bounded CPU container.
set -euo pipefail

samples="${SAMPLES:?set SAMPLES to a prepared JSONL file}"
problems="${PROBLEMS:-/cache/austinov/eval-data/general/unpack/humaneval/data/HumanEval.jsonl.gz}"
source_root="${HUMANEVAL_SOURCE:-/cache/austinov/eval-data/general/unpack/humaneval}"
runner_root="${RUNNER_ROOT:-$(cd "$(dirname "$0")" && pwd)}"
result_dir="${RESULT_DIR:-$(cd "$(dirname "${samples}")" && pwd)}"
image="${IMAGE:-quay.io/ascend/vllm-ascend@sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a}"

[[ -f "${samples}" ]] || { echo "missing SAMPLES: ${samples}" >&2; exit 66; }
[[ -f "${problems}" ]] || { echo "missing PROBLEMS: ${problems}" >&2; exit 66; }
[[ -f "${source_root}/human_eval/execution.py" ]] || { echo "invalid HUMANEVAL_SOURCE" >&2; exit 66; }
samples_name="$(basename "${samples}")"
[[ -d "${result_dir}" ]] || { echo "missing RESULT_DIR: ${result_dir}" >&2; exit 66; }
case "${problems}" in
  *.gz) problems_target=/problems.jsonl.gz ;;
  *) problems_target=/problems.jsonl ;;
esac

exec docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 128 --memory 8g --cpus 4 \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=2g \
  --mount "type=bind,src=${samples},dst=/samples.jsonl,readonly" \
  --mount "type=bind,src=${result_dir},dst=/output" \
  --mount "type=bind,src=${source_root},dst=/readonly/humaneval,readonly" \
  --mount "type=bind,src=${problems},dst=${problems_target},readonly" \
  --mount "type=bind,src=${runner_root}/humaneval_container_entrypoint.py,dst=/runner.py,readonly" \
  "${image}" python3 /runner.py --source /readonly/humaneval \
  --samples /samples.jsonl --problems "${problems_target}" \
  --result "/output/${samples_name}_results.jsonl" --workers 4 --timeout 3

#!/bin/sh
set -eu
if [ "$#" -ne 2 ]; then
  echo "usage: $0 RESULT_JSON SCORE_JSON" >&2
  exit 2
fi
RESULT=$(readlink -f "$1")
OUT=$(readlink -m "$2")
OUTDIR=$(dirname "$OUT")
mkdir -p "$OUTDIR"
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DATA=/cache/austinov/eval-data/general/prepared/HumanEval.jsonl.gz
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 64 --memory 2g --cpus 2 \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m \
  -e HUMANEVAL_SANDBOX=1 \
  -v "$REPO:/repo:ro" -v "$DATA:/data/HumanEval.jsonl.gz:ro" \
  -v "$RESULT:/input/result.json:ro" -v "$OUTDIR:/output:rw" \
  quay.io/ascend/vllm-ascend:v0.23.0 \
  python3 /repo/scripts/score_humaneval_sandbox.py \
    --result /input/result.json --data /data/HumanEval.jsonl.gz --output "/output/$(basename "$OUT")"

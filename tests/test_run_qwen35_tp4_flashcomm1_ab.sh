#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scratch="$(mktemp -d "$repo_root/tests/.tp4-fixed-reference-test.XXXXXX")"
trap 'rm -rf -- "$scratch"' EXIT

mkdir -p "$scratch/existing"
set +e
RUN_ID=test OUTPUT_ROOT="$scratch/existing" "$repo_root/scripts/run_qwen35_tp4_candidate_vs_original.sh" >"$scratch/existing.out" 2>"$scratch/existing.err"
status=$?
set -e
[[ "$status" == 44 ]]
grep -q "refusing to reuse immutable output root" "$scratch/existing.err"

set +e
RUN_ID=test OUTPUT_ROOT=relative "$repo_root/scripts/run_qwen35_tp4_candidate_vs_original.sh" >"$scratch/relative.out" 2>"$scratch/relative.err"
status=$?
set -e
[[ "$status" == 64 ]]
grep -q "OUTPUT_ROOT must be absolute" "$scratch/relative.err"

set +e
RUN_ID=test OUTPUT_ROOT="$scratch/future" CANDIDATE_MODE=unknown \
  "$repo_root/scripts/run_qwen35_tp4_candidate_vs_original.sh" \
  >"$scratch/unknown.out" 2>"$scratch/unknown.err"
status=$?
set -e
[[ "$status" == 64 ]]
grep -q "unsupported CANDIDATE_MODE" "$scratch/unknown.err"

set +e
RUN_ID=test OUTPUT_ROOT="$scratch/ngram-future" CANDIDATE_MODE=ngram-gpu \
  CANDIDATE_CONFIG="$scratch/missing-ngram.yaml" \
  "$repo_root/scripts/run_qwen35_tp4_candidate_vs_original.sh" \
  >"$scratch/ngram.out" 2>"$scratch/ngram.err"
status=$?
set -e
[[ "$status" == 66 ]]
grep -q "candidate config does not exist" "$scratch/ngram.err"

echo "PASS: TP4 fixed-original candidate guards"

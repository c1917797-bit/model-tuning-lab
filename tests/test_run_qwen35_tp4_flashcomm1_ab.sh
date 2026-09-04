#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scratch="$(mktemp -d "$repo_root/tests/.tp4-ab-test.XXXXXX")"
trap 'rm -rf -- "$scratch"' EXIT

mkdir -p "$scratch/existing"
set +e
RUN_ID=test OUTPUT_ROOT="$scratch/existing" "$repo_root/scripts/run_qwen35_tp4_flashcomm1_ab.sh" >"$scratch/existing.out" 2>"$scratch/existing.err"
status=$?
set -e
[[ "$status" == 44 ]]
grep -q "refusing to reuse immutable output root" "$scratch/existing.err"

set +e
RUN_ID=test OUTPUT_ROOT=relative "$repo_root/scripts/run_qwen35_tp4_flashcomm1_ab.sh" >"$scratch/relative.out" 2>"$scratch/relative.err"
status=$?
set -e
[[ "$status" == 64 ]]
grep -q "OUTPUT_ROOT must be absolute" "$scratch/relative.err"

echo "PASS: TP4 FlashComm1 A/B guards"

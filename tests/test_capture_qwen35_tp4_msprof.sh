#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scratch="$repo_root/.test-capture-msprof-$$"
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/profile" "$scratch/artifact"

set +e
env PROFILE_RUN_ID=test CONTAINER_NAME=test-msprof PROFILE_RANK=4 \
  PROFILE_DIR="$scratch/new-invalid-profile" \
  ARTIFACT_DIR="$scratch/new-invalid-artifact" \
  "$repo_root/scripts/capture_qwen35_tp4_msprof.sh" \
  >/dev/null 2>"$scratch/invalid-rank.err"
status=$?
set -e
[[ "$status" == 64 ]]
grep -q "PROFILE_RANK must be one of" "$scratch/invalid-rank.err"

set +e
env PROFILE_RUN_ID=test CONTAINER_NAME=test-msprof PROFILE_MODE=profile-msprof-unsupported PROFILE_DIR="$scratch/new-invalid-mode-profile" ARTIFACT_DIR="$scratch/new-invalid-mode-artifact" "$repo_root/scripts/capture_qwen35_tp4_msprof.sh" >/dev/null 2>"$scratch/invalid-mode.err"
status=$?
set -e
[[ "$status" == 64 ]]
grep -q "PROFILE_MODE must be" "$scratch/invalid-mode.err"

set +e
env PROFILE_RUN_ID=test CONTAINER_NAME=test-msprof DEVICE_SET=0-3 PROFILE_DIR="$scratch/new-invalid-device-profile" ARTIFACT_DIR="$scratch/new-invalid-device-artifact" "$repo_root/scripts/capture_qwen35_tp4_msprof.sh" >/dev/null 2>"$scratch/invalid-device.err"
status=$?
set -e
[[ "$status" == 64 ]]
grep -q "DEVICE_SET must be 4-7" "$scratch/invalid-device.err"

set +e
env PROFILE_RUN_ID=test CONTAINER_NAME=test-msprof \
  PROFILE_DIR="$scratch/profile" \
  ARTIFACT_DIR="$scratch/new-artifact" \
  "$repo_root/scripts/capture_qwen35_tp4_msprof.sh" \
  >/dev/null 2>"$scratch/existing-profile.err"
status=$?
set -e
[[ "$status" == 44 ]]
grep -q "refusing to reuse immutable output path" "$scratch/existing-profile.err"

set +e
env PROFILE_RUN_ID=test CONTAINER_NAME=test-msprof \
  PROFILE_DIR="$scratch/new-profile" \
  ARTIFACT_DIR="$scratch/artifact" \
  "$repo_root/scripts/capture_qwen35_tp4_msprof.sh" \
  >/dev/null 2>"$scratch/existing-artifact.err"
status=$?
set -e
[[ "$status" == 44 ]]
grep -q "refusing to reuse immutable output path" "$scratch/existing-artifact.err"

grep -Fq 'profile-msprof-mmar-off|profile-msprof-mmar-on' "$repo_root/scripts/run_qwen35_tp4_dev_service.sh"
grep -Fq '"$mode" == profile-msprof-mmar-on' "$repo_root/scripts/run_qwen35_tp4_dev_service.sh"
grep -Fq '"$repo_root/scripts/run_qwen35_tp4_dev_service.sh" "$profile_mode"' "$repo_root/scripts/capture_qwen35_tp4_msprof.sh"

echo "capture msprof guards: ok"

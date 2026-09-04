#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scratch="$repo_root/.test-capture-profile-$$"
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/profile" "$scratch/artifact"

set +e
env PROFILE_RUN_ID=test CONTAINER_NAME=test-profile PROFILE_DIR="$scratch/profile" ARTIFACT_DIR="$scratch/new-artifact" "$repo_root/scripts/capture_qwen35_tp4_profile.sh" >/dev/null 2>"$scratch/existing-profile.err"
status=$?
set -e
[[ "$status" == 44 ]]
grep -q "refusing to reuse immutable output path" "$scratch/existing-profile.err"

set +e
env PROFILE_RUN_ID=test CONTAINER_NAME=test-profile PROFILE_DIR="$scratch/new-profile" ARTIFACT_DIR="$scratch/artifact" "$repo_root/scripts/capture_qwen35_tp4_profile.sh" >/dev/null 2>"$scratch/existing-artifact.err"
status=$?
set -e
[[ "$status" == 44 ]]
grep -q "refusing to reuse immutable output path" "$scratch/existing-artifact.err"

echo "capture profile guards: ok"

#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d "$repo_root/tests/.guard-test.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

mock_bin="$tmp/bin"
mkdir -p "$mock_bin"
docker_log="$tmp/docker.log"

cat >"$mock_bin/docker" <<'MOCK'
#!/usr/bin/env bash
if [[ "${1:-}" == container && "${2:-}" == inspect ]]; then
  exit 1
fi
printf '%s\n' "$*" >>"$DOCKER_LOG"
MOCK
chmod +x "$mock_bin/docker"

cat >"$mock_bin/npu-smi" <<'MOCK'
#!/usr/bin/env bash
cat <<'INFO'
| NPU     Chip              | Process id    | Process name             | Process memory(MB)      |
| 0       0                 | 4111982       | VLLMWorker_TP            | 27952                   |
INFO
MOCK
chmod +x "$mock_bin/npu-smi"

set +e
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi"   CONTAINER_NAME=guard-test-occupied   PROFILE_DIR="$tmp/profile-occupied"   "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" profile   >"$tmp/occupied.out" 2>"$tmp/occupied.err"
rc=$?
set -e
[[ "$rc" == 42 ]]
grep -q "NPU0-3 are not idle" "$tmp/occupied.err"
[[ ! -e "$docker_log" ]]

cat >"$mock_bin/npu-smi" <<'MOCK'
#!/usr/bin/env bash
cat <<'INFO'
| NPU     Chip              | Process id    | Process name             | Process memory(MB)      |
INFO
MOCK
chmod +x "$mock_bin/npu-smi"
mkdir "$tmp/profile-existing"

set +e
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi"   CONTAINER_NAME=guard-test-profile-dir   PROFILE_DIR="$tmp/profile-existing"   "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" profile   >"$tmp/profile.out" 2>"$tmp/profile.err"
rc=$?
set -e
if [[ "$rc" != 44 ]]; then cat "$tmp/profile.err" >&2; fi
[[ "$rc" == 44 ]]
grep -q "refusing to reuse profile directory" "$tmp/profile.err"
[[ ! -e "$docker_log" ]]

PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-profile-fresh \
  PROFILE_DIR="$tmp/profile-fresh" \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" profile \
  >"$tmp/profile-fresh.out" 2>"$tmp/profile-fresh.err"
grep -q -- '--profiler-config.profiler torch' "$docker_log"
if grep -q -- '--async-scheduling' "$docker_log"; then
  echo "profile mode unexpectedly enabled async scheduling" >&2
  exit 1
fi

: >"$docker_log"
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" NPU_SMI_BIN="$mock_bin/npu-smi" \
  CONTAINER_NAME=guard-test-baseline-fresh \
  "$repo_root/scripts/run_qwen35_tp4_dev_service.sh" baseline \
  >"$tmp/baseline-fresh.out" 2>"$tmp/baseline-fresh.err"
grep -q -- '--async-scheduling' "$docker_log"
if grep -q -- '--profiler-config.profiler' "$docker_log"; then
  echo "baseline mode unexpectedly enabled profiling" >&2
  exit 1
fi

echo "PASS: run_qwen35_tp4_dev_service guards"

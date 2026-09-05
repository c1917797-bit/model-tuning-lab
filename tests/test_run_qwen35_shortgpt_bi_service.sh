#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d "$repo_root/tests/.shortgpt-bi-guard.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT
mock_bin="$tmp/bin"
mkdir -p "$mock_bin"
docker_log="$tmp/docker.log"

cat >"$mock_bin/docker" <<'MOCK'
#!/usr/bin/env bash
if [[ "${1:-}" == container && "${2:-}" == inspect ]]; then
  exit 1
fi
if [[ "${1:-}" == ps && "${2:-}" == -q ]]; then
  printf '%s' "${MOCK_DOCKER_RUNNING_IDS:-}"
  exit 0
fi
if [[ "${1:-}" == inspect && "${2:-}" == reservation ]]; then
  echo '/foreign /dev/davinci4 /dev/davinci5 /dev/davinci6 /dev/davinci7'
  exit 0
fi
printf '%s\n' "$*" >>"$DOCKER_LOG"
echo mock-container-id
MOCK
chmod +x "$mock_bin/docker"

cat >"$mock_bin/npu-smi" <<'MOCK'
#!/usr/bin/env bash
cat <<'INFO'
| NPU     Chip              | Process id    | Process name             | Process memory(MB)      |
INFO
MOCK
chmod +x "$mock_bin/npu-smi"

cat >"$mock_bin/ss" <<'MOCK'
#!/usr/bin/env bash
exit 0
MOCK
chmod +x "$mock_bin/ss"

source_root=/cache/cch/.worktrees/exp-20260905-qwen35-shortgpt-vllm
source_commit=18c4d061529d226dd0d699d9e3e1df16dadf29d7

set +e
PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" MOCK_DOCKER_RUNNING_IDS=reservation DOCKER_BIN="$mock_bin/docker" NPU_SMI_BIN="$mock_bin/npu-smi" SS_BIN="$mock_bin/ss" SHORTGPT_SOURCE_ROOT="$source_root" SHORTGPT_SOURCE_COMMIT="$source_commit" BI_ALLOWED_ROOT="$tmp" QWEN35_BI_DIR="$tmp/busy/bi" "$repo_root/scripts/run_qwen35_shortgpt_bi_service.sh" >"$tmp/busy.out" 2>"$tmp/busy.err"
rc=$?
set -e
[[ "$rc" == 48 ]]
grep -q 'reserves physical NPU4-7' "$tmp/busy.err"
[[ ! -e "$tmp/busy/bi" ]]

PATH="$mock_bin:$PATH" DOCKER_LOG="$docker_log" DOCKER_BIN="$mock_bin/docker" NPU_SMI_BIN="$mock_bin/npu-smi" SS_BIN="$mock_bin/ss" SHORTGPT_SOURCE_ROOT="$source_root" SHORTGPT_SOURCE_COMMIT="$source_commit" BI_ALLOWED_ROOT="$tmp" QWEN35_BI_DIR="$tmp/ready/bi" "$repo_root/scripts/run_qwen35_shortgpt_bi_service.sh" >"$tmp/ready.out" 2>"$tmp/ready.err"

grep -q -- '--device /dev/davinci4:/dev/davinci0' "$docker_log"
grep -q -- '--device /dev/davinci7:/dev/davinci3' "$docker_log"
grep -q -- 'VLLM_ASCEND_QWEN35_BI_DIR=' "$docker_log"
grep -q -- 'qwen35_shortgpt.py:' "$docker_log"
grep -q -- 'patch_qwen3_5.py:' "$docker_log"
grep -q -- '--enforce-eager' "$docker_log"
grep -q -- '--no-async-scheduling' "$docker_log"
grep -q -- '"mlp":{"gate_up":0.1,"down":0.0}' "$docker_log"
if grep -q -- '--quantization' "$docker_log"; then
  echo "ShortGPT BI service unexpectedly enabled quantization" >&2
  exit 1
fi
echo "PASS: Qwen3.5 ShortGPT BI service guard"

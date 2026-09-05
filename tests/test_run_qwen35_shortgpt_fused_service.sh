#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d "$repo_root/tests/.shortgpt-fused-guard.XXXXXX")"
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
if [[ "${1:-}" == inspect && "${2:-}" == --format &&
      "${*: -1}" == reservation ]]; then
  echo '/foreign /dev/davinci4 /dev/davinci5 /dev/davinci6 /dev/davinci7'
  exit 0
fi
printf '%s\n' "$*" >>"$DOCKER_LOG"
echo mock-container-id
MOCK
chmod +x "$mock_bin/docker"

cat >"$mock_bin/npu-smi" <<'MOCK'
#!/usr/bin/env bash
echo '| NPU     Chip              | Process id    | Process name             | Process memory(MB)      |'
MOCK
chmod +x "$mock_bin/npu-smi"
cat >"$mock_bin/ss" <<'MOCK'
#!/usr/bin/env bash
exit 0
MOCK
chmod +x "$mock_bin/ss"

layer_set="$tmp/layers.json"
cat >"$layer_set" <<'JSON'
{
  "schema": "qwen35-shortgpt-layer-set/v1",
  "status": "frozen",
  "source_commit": "18c4d061529d226dd0d699d9e3e1df16dadf29d7",
  "model_config_sha256": "191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab",
  "removed_layer_count": 8,
  "layers": [0, 1, 2, 3, 4, 5, 6, 7],
  "env_spec": "0-7"
}
JSON
layer_hash="$(sha256sum "$layer_set" | awk '{print $1}')"
common_env=(
  PATH="$mock_bin:$PATH"
  DOCKER_LOG="$docker_log"
  DOCKER_BIN="$mock_bin/docker"
  NPU_SMI_BIN="$mock_bin/npu-smi"
  SS_BIN="$mock_bin/ss"
  SHORTGPT_LAYER_SET_FILE="$layer_set"
  SHORTGPT_LAYER_SET_SHA256="$layer_hash"
)

set +e
env "${common_env[@]}" MOCK_DOCKER_RUNNING_IDS=reservation CONTAINER_NAME=shortgpt-fused-busy "$repo_root/scripts/run_qwen35_shortgpt_fused_service.sh" shortgpt-fused-tail >"$tmp/busy.out" 2>"$tmp/busy.err"
rc=$?
set -e
[[ "$rc" == 48 ]]
grep -q 'reserves physical NPU4-7' "$tmp/busy.err"

env "${common_env[@]}" CONTAINER_NAME=shortgpt-fused-ready "$repo_root/scripts/run_qwen35_shortgpt_fused_service.sh" shortgpt-fused-tail >"$tmp/ready.out" 2>"$tmp/ready.err"
grep -q -- '--device /dev/davinci4:/dev/davinci0' "$docker_log"
grep -q -- '--device /dev/davinci7:/dev/davinci3' "$docker_log"
grep -q -- 'VLLM_ASCEND_QWEN35_SKIP_LAYERS=0-7' "$docker_log"
grep -q -- 'VLLM_ASCEND_QWEN35_REMOVED_LAYER_COUNT=8' "$docker_log"
grep -q -- 'qwen35_shortgpt.py:' "$docker_log"
grep -q -- 'decode_mmar_add_rmsnorm_fusion_pass.py:' "$docker_log"
grep -q -- 'vllm_ascend_C.cpython-312-aarch64-linux-gnu.so:' "$docker_log"
grep -q -- '"fuse_decode_mmar_add_rmsnorm":true' "$docker_log"
grep -q -- '--async-scheduling' "$docker_log"
if grep -q -- '--quantization' "$docker_log"; then
  echo "ShortGPT fused service unexpectedly enabled quantization" >&2
  exit 1
fi
>"$docker_log"
env "${common_env[@]}" CONTAINER_NAME=shortgpt-retained-ready "$repo_root/scripts/run_qwen35_shortgpt_fused_service.sh" shortgpt-retained >"$tmp/retained.out" 2>"$tmp/retained.err"
grep -q -- 'VLLM_ASCEND_QWEN35_SKIP_LAYERS=0-7' "$docker_log"
if grep -q -- 'fuse_decode_mmar_add_rmsnorm' "$docker_log"; then
  echo "ShortGPT retained service unexpectedly configured fused tail" >&2
  exit 1
fi
echo "PASS: Qwen3.5 ShortGPT plus fused-tail service guard"

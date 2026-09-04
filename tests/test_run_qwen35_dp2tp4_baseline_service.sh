#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scratch="$repo_root/.test-dp2tp4-launcher-$$"
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/bin"

cat >"$scratch/bin/npu-smi" <<'EOF'
#!/usr/bin/env bash
cat <<'SNAPSHOT'
| NPU     Chip              | Process id    | Process name             | Process memory(MB)      |
| 4       0                 | 9999          | VLLMWorker_TP             | 28000                   |
SNAPSHOT
EOF
cat >"$scratch/bin/docker" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == container && "$2" == inspect ]]; then
  exit 1
fi
echo "docker run must not be reached while NPU4 is occupied" >&2
exit 99
EOF
chmod +x "$scratch/bin/npu-smi" "$scratch/bin/docker"

set +e
env NPU_SMI_BIN="$scratch/bin/npu-smi" DOCKER_BIN="$scratch/bin/docker" CONTAINER_NAME=test-dp2tp4 MANIFEST_PATH="$scratch/manifest.json" "$repo_root/scripts/run_qwen35_dp2tp4_baseline_service.sh" >"$scratch/stdout" 2>"$scratch/stderr"
status=$?
set -e

[[ "$status" == 42 ]]
[[ ! -e "$scratch/manifest.json" ]]
grep -q "NPU0-7 are not exclusively idle" "$scratch/stderr"
grep -q "NPU4:pid=9999" "$scratch/stderr"

cat >"$scratch/bin/npu-smi" <<'EOF'
#!/usr/bin/env bash
echo "| NPU     Chip              | Process id    | Process name             | Process memory(MB)      |"
EOF
cat >"$scratch/bin/docker" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == container && "$2" == inspect ]]; then
  exit 1
fi
printf '%s\n' "$@" >"$DOCKER_LOG"
echo fake-container-id
EOF
chmod +x "$scratch/bin/npu-smi" "$scratch/bin/docker"

env NPU_SMI_BIN="$scratch/bin/npu-smi" DOCKER_BIN="$scratch/bin/docker" DOCKER_LOG="$scratch/docker.args" CONTAINER_NAME=test-dp2tp4-idle MANIFEST_PATH="$scratch/idle-manifest.json" "$repo_root/scripts/run_qwen35_dp2tp4_baseline_service.sh" >"$scratch/idle.stdout"
[[ -s "$scratch/idle-manifest.json" ]]
grep -q '^quay.io/ascend/vllm-ascend:v0.23.0$' "$scratch/docker.args"
grep -q '^/dev/davinci0$' "$scratch/docker.args"
grep -q '^/dev/davinci7$' "$scratch/docker.args"
grep -q '^ASCEND_RT_VISIBLE_DEVICES=0,1,2,3,4,5,6,7$' "$scratch/docker.args"
grep -q '^--data-parallel-size$' "$scratch/docker.args"
grep -q '^--tensor-parallel-size$' "$scratch/docker.args"
python3 - "$scratch/idle-manifest.json" <<'PY'
import json
import sys
payload = json.load(open(sys.argv[1]))
assert payload["runtime_sha256"] == "e74fcb3444bbc94d5c71086b279b4c08d94295b17499700b7b8c75aa0098b7c6"
PY

echo "PASS: DP2/TP4 launcher ownership and render guards"

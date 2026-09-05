#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d "$repo_root/.tmp-shortgpt-queue-test.XXXXXX")"
trap 'rm -rf "$tmp_dir"' EXIT

printf '%s\n' R15_DONE >"$tmp_dir/r15.log"
mkdir -p "$tmp_dir/bin" "$tmp_dir/output"

printf '%s\n' '#!/usr/bin/env bash' 'if [[ "$1" == ps && "$2" == -q ]]; then exit 0; fi' 'echo "unexpected docker invocation: $*" >&2' 'exit 1' >"$tmp_dir/bin/docker"
printf '%s\n' '#!/usr/bin/env bash' '[[ "$1" == info ]]' >"$tmp_dir/bin/npu-smi"
printf '%s\n' '#!/usr/bin/env bash' '[[ "$1" == -lntH ]]' >"$tmp_dir/bin/ss"
printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail' '{' '  printf "OUTPUT_ROOT=%s\n" "$OUTPUT_ROOT"' '  printf "CONTAINER_NAME=%s\n" "$CONTAINER_NAME"' '  printf "PORT=%s\n" "$PORT"' '} >"$CAPTURE_FILE"' >"$tmp_dir/bin/launcher"
chmod +x "$tmp_dir/bin/"*

env PATH="$tmp_dir/bin:$PATH" R15_LOG="$tmp_dir/r15.log" PREDECESSOR_PID=99999999 PREDECESSOR_START_TICKS=1 OUTPUT_PARENT="$tmp_dir/output" LAUNCHER="$tmp_dir/bin/launcher" DOCKER_BIN="$tmp_dir/bin/docker" NPU_SMI_BIN="$tmp_dir/bin/npu-smi" SS_BIN="$tmp_dir/bin/ss" WAIT_TIMEOUT_SECONDS=5 POLL_SECONDS=0 STABLE_IDLE_CHECKS=2 IDLE_CHECK_INTERVAL_SECONDS=0 STAMP_OVERRIDE=20260905T150000Z CAPTURE_FILE="$tmp_dir/capture" "$repo_root/scripts/queue_qwen35_shortgpt_bi_after_v10.sh"

grep -qx "OUTPUT_ROOT=$tmp_dir/output/bi-20260905T150000Z" "$tmp_dir/capture"
grep -qx 'CONTAINER_NAME=qwen35_shortgpt_bi_npu4_7' "$tmp_dir/capture"
grep -qx 'PORT=10020' "$tmp_dir/capture"

echo "queue_qwen35_shortgpt_bi_after_v10: PASS"

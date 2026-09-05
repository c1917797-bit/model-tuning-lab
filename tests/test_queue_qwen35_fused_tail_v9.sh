#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d "$repo_root/.tmp-queue-test.XXXXXX")"
trap 'rm -rf "$tmp_dir"' EXIT

printf '%s\n' OVERLAP_AB_DONE >"$tmp_dir/overlap.log"
printf '%s\n' MC2_AB_DONE >"$tmp_dir/mc2.log"

mkdir -p "$tmp_dir/bin" "$tmp_dir/output"
cat >"$tmp_dir/bin/docker" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == ps && "$2" == -q ]]; then
  exit 0
fi
echo "unexpected docker invocation: $*" >&2
exit 1
EOF
cat >"$tmp_dir/bin/npu-smi" <<'EOF'
#!/usr/bin/env bash
[[ "$1" == info ]]
EOF
cat >"$tmp_dir/bin/ss" <<'EOF'
#!/usr/bin/env bash
[[ "$1" == -lntH ]]
EOF
cat >"$tmp_dir/bin/launcher" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
{
  printf 'RUN_ID=%s\n' "$RUN_ID"
  printf 'OUTPUT_ROOT=%s\n' "$OUTPUT_ROOT"
  printf 'CANDIDATE_MODE=%s\n' "$CANDIDATE_MODE"
  printf 'CANDIDATE_ID=%s\n' "$CANDIDATE_ID"
  printf 'DEVICE_SET=%s\n' "$DEVICE_SET"
  printf 'PORT=%s\n' "$PORT"
} >"$CAPTURE_FILE"
EOF
chmod +x "$tmp_dir/bin/"*

env PATH="$tmp_dir/bin:$PATH" OVERLAP_LOG="$tmp_dir/overlap.log" MC2_LOG="$tmp_dir/mc2.log" OUTPUT_PARENT="$tmp_dir/output" LAUNCHER="$tmp_dir/bin/launcher" DOCKER_BIN="$tmp_dir/bin/docker" NPU_SMI_BIN="$tmp_dir/bin/npu-smi" SS_BIN="$tmp_dir/bin/ss" WAIT_TIMEOUT_SECONDS=5 POLL_SECONDS=0 STABLE_IDLE_CHECKS=2 IDLE_CHECK_INTERVAL_SECONDS=0 STAMP_OVERRIDE=20260905T120000Z CAPTURE_FILE="$tmp_dir/capture" "$repo_root/scripts/queue_qwen35_fused_tail_v9.sh"

grep -qx 'RUN_ID=fused-tail-v9-20260905T120000Z' "$tmp_dir/capture"
grep -qx "OUTPUT_ROOT=$tmp_dir/output/mmar-add-rmsnorm-v9-20260905T120000Z" "$tmp_dir/capture"
grep -qx 'CANDIDATE_MODE=mmar-on-weight-prefetch-gateup-0p1-fused-tail' "$tmp_dir/capture"
grep -qx 'CANDIDATE_ID=mmar-add-rmsnorm-decode-v9' "$tmp_dir/capture"
grep -qx 'DEVICE_SET=4-7' "$tmp_dir/capture"
grep -qx 'PORT=10010' "$tmp_dir/capture"

echo "queue_qwen35_fused_tail_v9: PASS"

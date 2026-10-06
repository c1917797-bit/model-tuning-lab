#!/usr/bin/env bash
set -euo pipefail

WORKTREE=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
RECORDS=$WORKTREE/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend
OUTPUT_ROOT=/cache/cch/hypic-qwen36-e2e-2048-20261006

export HYPIC_WORKTREE=$WORKTREE
export HYPIC_OUTPUT_ROOT=$OUTPUT_ROOT
export HYPIC_MODEL_NAME=qwen36-hypic-e2e-2048
export HYPIC_PORT=8223
export HYPIC_CPUSET=112-191
export HYPIC_BASELINE_CONTAINER=qwen36_hypic2048_baseline_npu0_3_v1
export HYPIC_TREATMENT_CONTAINER=qwen36_hypic2048_treatment_npu0_3_v1
export HYPIC_EXPERIMENT_ID=hypic-qwen36-e2e-2048-20261006
export HYPIC_HOST_NPU_FIRST=0
export HYPIC_HOST_NPU_LAST=3
export HYPIC_VISIBLE_DEVICES=0,1,2,3
export HYPIC_CONTAINER_DEVICE_FIRST=0
export HYPIC_TP_SIZE=4
export HYPIC_HCCL_PORT_RANGE=27000-27100
export HYPIC_MAX_NUM_BATCHED_TOKENS=40960
export HYPIC_QUALITY_MAX_OUT_LEN=2048
export HYPIC_REFERENCE_SHA256=204b01d76eff8a0fd69a4a048de44da8385c6bfdc250c1efb8af542b63fb438c

bash "$RECORDS/resume_hypic_historical_reproduction.sh" "$@"

if [[ ${1:-} == --self-test ]]; then
  exit 0
fi

python3 "$RECORDS/audit_hypic_historical_reproduction.py" \
  --root "$OUTPUT_ROOT" \
  --output "$OUTPUT_ROOT/hypic-e2e-2048-evidence-audit.json" \
  --quality-max-out-len 2048

sha256sum \
  "$OUTPUT_ROOT/historical-reproduction-summary.json" \
  "$OUTPUT_ROOT/HISTORICAL_REPRODUCTION_REPORT.md" \
  "$OUTPUT_ROOT/hypic-e2e-2048-evidence-audit.json" \
  > "$OUTPUT_ROOT/FINAL_E2E_SHA256SUMS"

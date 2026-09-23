#!/usr/bin/env bash
set -euo pipefail

RECORDS=/cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend

export HYPIC_OUTPUT_ROOT=/cache/cch/hypic-qwen36-formal-npu4-5-tp2-20260906
export HYPIC_MODEL_NAME=qwen36-formal-npu4-5-tp2
export HYPIC_PORT=8224
export HYPIC_CPUSET=46-95
export HYPIC_BASELINE_CONTAINER=qwen36_hypic_nocache_baseline_npu4_5_tp2
export HYPIC_TREATMENT_CONTAINER=qwen36_hypic_only_npu4_5_tp2
export HYPIC_EXPERIMENT_ID=hypic-qwen36-formal-npu4-5-tp2-20260906
export HYPIC_HOST_NPU_FIRST=4
export HYPIC_HOST_NPU_LAST=5
export HYPIC_CONTAINER_DEVICE_FIRST=0
export HYPIC_VISIBLE_DEVICES=0,1
export HYPIC_TP_SIZE=2
export HYPIC_HCCL_PORT_RANGE=26600-26700
export HYPIC_MEMORY_LIMIT=48g
export HYPIC_REFERENCE_SHA256=204b01d76eff8a0fd69a4a048de44da8385c6bfdc250c1efb8af542b63fb438c

exec bash "$RECORDS/resume_hypic_historical_reproduction.sh" "$@"

#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
service="$repo_root/scripts/run_qwen35_tp4_dev_service.sh"
orchestrator="$repo_root/scripts/run_qwen35_tp4_candidate_vs_original.sh"
config="$repo_root/configs/qwen35-query-rewrite-selective-ffn-nz-candidate.yaml"

grep -q 'selective-ffn-nz is restricted to physical NPU4-7' "$service"
grep -q 'selective_ffn_nz_commit="71c25ec9"' "$service"
grep -q 'VLLM_ASCEND_ENABLE_DENSE_FFN_NZ="$selective_ffn_nz_env"' "$service"
grep -q '/vllm-workspace/vllm-ascend/vllm_ascend' "$service"
grep -q 'selective-ffn-nz)' "$orchestrator"
grep -q 'VLLM_ASCEND_ENABLE_DENSE_FFN_NZ: "1"' "$config"
grep -q 'quantization: null' "$config"
grep -q 'physical_devices: \[4, 5, 6, 7\]' "$config"

echo "PASS: selective FFN NZ integration guards"

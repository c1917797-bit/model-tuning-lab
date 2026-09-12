# T24 built-in npu_ffn BF16 admission gate

Status: rejected from the BF16 service path; no new NPU run was needed.

## Candidate

The unchanged official `quay.io/ascend/vllm-ascend:v0.23.0` image exports
`torch_npu.npu_ffn`, and the installed Python-facing documentation lists
BF16 tensors and `swiglu` activation. This made the built-in operator the
preferred upstream implementation to examine before any new dense-FFN code.

## Authoritative runtime evidence

The repository already contains a real-weight TP4 benchmark and an immutable
result from the same official image:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/ffn-bf16-layout-npu4-20260904T220321Z-v2/report.json`

It used the real layer-0 Qwen3.5 weights, BF16 rank-0 shards and exact
M=1/5/8/16 shapes. Every `npu_ffn(..., "swiglu")` cell failed in
`aclnnFFNV2` with error 161002: without expert tokens, the installed kernel
accepts FP16 input but rejects BF16. The public schema and prose therefore
overstate the usable dtype support for this dense path. Changing model/runtime
dtype to FP16 is outside the quality contract and cannot be used as a
workaround.

The exact T16 profile independently shows the existing decode SwiGLU at shape
`[1, 8704]` has a four-rank median of about 4.39 us per layer. This is far
below the installed operator guidance's approximately 30-us small-vector
threshold, so an activation-only substitution is also uneconomic.

## Communication boundary

Even if a future CANN release enables BF16 `npu_ffn`, the operator returns a
local dense output and does not preserve the current fused
Matmul-AllReduce boundary. It must be benchmarked as
`fused FFN + standalone TP all-reduce` against the existing
`gate_up + SwiGLU + MatmulAllReduce` chain. A local GEMM win is not a valid
service claim.

## Decision

`reject-builtin-npu-ffn-for-current-bf16-runtime`.

Do not rerun this exact v0.23.0 BF16 candidate, cast to FP16, or write a
parallel FFN implementation. Reopen only if a pinned supported CANN/operator
release changes the BF16 kernel contract, then require exact numerical,
whole-chain TP4, end-to-end performance and model-quality gates.

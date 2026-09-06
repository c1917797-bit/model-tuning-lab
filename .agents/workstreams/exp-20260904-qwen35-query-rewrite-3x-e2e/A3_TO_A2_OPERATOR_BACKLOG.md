# Atlas A3 to A2/910B4 operator backlog

Status date: 2026-09-06. This document records source-derived eligibility and
prior real measurements. It does not claim performance for an unbenchmarked
operator port.

## Real profile boundary

The retained non-speculative TP4 profile on physical Ascend 910B4 NPU0-3
attributes 64.9357% of summed kernel duration to collectives and 24.4934% to
matmul. `MatmulAllReduceMc2AicpuKernel` contributes 48.1818%, ordinary matmul
23.4185%, and `MatmulAllReduce` 16.6553%. The trace contains approximately 128
row-parallel MMAR calls per decode step. The op-summary SHA256 is
`45b376e3401961dd3ffb90a92fa7fb45e5c4d185aacf4177011c25ef62c19dc0`.

Evidence root:
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/profiles/tp4-npu03-qwen35-gdn-prefetch0p1-nospec-msprof-v1-20260906T131000Z`.

## Priority decision

| Priority | Operator or path | Repository support evidence | Applicability to current dense TP4 service | Decision |
|---|---|---|---|---|
| P0 | `MatmulAllReduce` A2/910B4 BF16 kernel and tiling | `/cache/cch/ops-transformer/mc2/matmul_all_reduce/README.md` marks Atlas A2 supported and Atlas A3 unsupported; API source selects `ASCEND910B` and AICPU mode | Directly matches the dominant real profile path | Optimize the existing A2 path; this is not an A3 port. Benchmark exact Qwen row-parallel shapes before E2E |
| P1 | `AttentionToFFN` | README marks Atlas A3 supported and Atlas A2 unsupported; inputs include expert IDs, expert-rank tables and separate Attention/FFN workers | Not directly applicable to this dense model, which has no routed experts or disaggregated FFN workers | Do not port for the current loop. Reconsider only with an explicit attention/FFN-disaggregation architecture experiment |
| P1 | `FFNToAttention` | README marks Atlas A3 supported and Atlas A2 unsupported; function sends FFN-worker tokens to Attention workers and uses expert offsets | Same mismatch as `AttentionToFFN` | Do not port for the current loop |
| P2 | `RecurrentGatedDeltaRule` and `ChunkGatedDeltaRule` | Both READMEs already mark Atlas A2 supported | Relevant to Qwen3.5 GDN, but not an A3-to-A2 gap; current real profile attributes only 1.0842% to GDN decode | Keep as a later micro-optimization after MMAR |
| Reject repeat | `MatmulAllReduceAddRmsNorm` and inplace variant | READMEs already mark Atlas A2 supported and Atlas A3 unsupported | Direct fusion shape is relevant, but the v13-v17 integration series already produced an all-cell E2E regression | Do not repeat unchanged; require a materially different graph match or kernel implementation |
| Out of scope | `FusedCausalConv1d` | README supports Ascend 950 and marks both Atlas A3 and A2 unsupported | Current causal-conv profile share is 0.6407%, and this is not an A3 port | Do not prioritize for the current target |

## What to change if operator development is available

The useful operator task is therefore an A2-native MMAR optimization, scoped
to the exact BF16 TP4 Qwen3.5 row-parallel shapes observed in the trace:

1. Export the exact MMAR shape/frequency distribution from the retained trace.
2. Add an ASCEND910B-specific tiling candidate in the existing
   `matmul_all_reduce` A2 path; do not copy an A3-only operator whose contract
   assumes expert routing or disaggregated workers.
3. Prove numerical equivalence against current CANN MMAR on NPU0-3.
4. Require a predefined operator microbenchmark gate, then wire it into the
   vLLM-Ascend graph and run the real query_rewrite c1/c5/c8/c16 P95 matrix.
5. Record raw outputs, runtime activation proof, manifests and SHA256 hashes.

No source-only result in this file is performance evidence. Promotion still
requires real 910B4 E2E data and the semantic quality gate.

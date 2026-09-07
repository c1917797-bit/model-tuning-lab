# Atlas A3 to A2/910B4 operator backlog

Status date: 2026-09-07. This document records source-derived eligibility and
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
| P1 | `FFN` A3 kernel ported as an A2-native BF16 dense SwiGLU specialization | `ffn/ffn/README.md` marks Atlas A3 supported and A2 unsupported; its no-expert form computes two matmuls with activation | Structurally relevant to the dense MLP, but the installed A2 contract does not support Qwen3.5's BF16 gated SwiGLU shape | Worth implementing only as a new A2 BF16 gated kernel plus vLLM graph integration. It is unverified and secondary to MMAR because collectives dominate the real profile |
| P1 | `AttentionToFFN` | README marks Atlas A3 supported and Atlas A2 unsupported; inputs include expert IDs, expert-rank tables and separate Attention/FFN workers | Not directly applicable to this dense model, which has no routed experts or disaggregated FFN workers | Do not port for the current loop. Reconsider only with an explicit attention/FFN-disaggregation architecture experiment |
| P1 | `FFNToAttention` | README marks Atlas A3 supported and Atlas A2 unsupported; function sends FFN-worker tokens to Attention workers and uses expert offsets | Same mismatch as `AttentionToFFN` | Do not port for the current loop |
| P2 | `RecurrentGatedDeltaRule` and `ChunkGatedDeltaRule` | Both READMEs already mark Atlas A2 supported | Relevant to Qwen3.5 GDN, but not an A3-to-A2 gap; current real profile attributes only 1.0842% to GDN decode | Keep as a later micro-optimization after MMAR |
| Reject repeat | `MatmulAllReduceAddRmsNorm` and inplace variant | READMEs already mark Atlas A2 supported and Atlas A3 unsupported | Direct fusion shape is relevant, but the v13-v17 integration series already produced an all-cell E2E regression | Do not repeat unchanged; require a materially different graph match or kernel implementation |
| Out of scope | `FusedCausalConv1d` | README supports Ascend 950 and marks both Atlas A3 and A2 unsupported | Current causal-conv profile share is 0.6407%, and this is not an A3 port | Do not prioritize for the current target |
| Out of scope | A3-only MoE/disaggregation MC2 family: `BatchMatMulReduceScatterAlltoAll`, `AlltoAllAllGatherBatchMatMul`, `AttentionToFFN`, `FFNToAttention`, `MoeDistribute*`, `AlltoAllvGroupedMatMul` | Repository READMEs mark A3 supported and A2 unsupported | Contracts require routed experts, all-to-all, or separate Attention/FFN workers; none appears in the retained dense TP4 graph | Do not port for this goal |

## 2026-09-07 activation and parameter screens

- Lowering `HCCL_BUFFSIZE` from the retained 512 to 64/128/256 did not pass
  the exact-shape NPU0-3 MMAR microbenchmark gate. No candidate improved both
  real decode shapes by at least 1.02x; retain 512 and do not spend an E2E
  matrix on these values.
- Disabling MMAR and enabling the sequence-parallel compiler pass exposed 832
  ordinary `all_reduce` nodes, but produced zero `reduce_scatter` and zero
  `all_gather` nodes in the rank-0 compiled graph. Reject before E2E: the
  optimization did not activate.
- Sequence-parallel activation evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/activation-probes/tp4-npu03-gdn-proj-sp-mmaroff-v1-20260907T000000Z`.
- The practical P0 operator task remains a materially new A2/910B4 MMAR
  implementation that reduces AICPU/HCCL overhead for M=1 decode, rather than
  another compiler flag or an A3 expert-routing port.

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

## MMAR-off E2E closure

A real MMAR-off E2E screen rejected simple decomposition. The activated
rank-0 graph had zero MMAR and 832 ordinary all-reduce occurrences, yet c1
TTFT/TPOT P95 regressed by 0.527248%/0.220490% versus the retained stack.
Evidence manifest SHA256:
`21deab1aa598edb04bfd38f6c88bd30118c3a6b1f04ed244e68cc403d12f964f`.
Therefore the P0 implementation must preserve or improve fusion rather than
replacing MMAR with the existing unfused sequence.

The follow-up selective screen also rejects ordinary matmul plus all-reduce
for attention/GDN `o_proj/out_proj`: TPOT P95 regressed 14.224519% while
the activated graph retained 384 MMAR occurrences for the complementary
family. Keep MMAR on this smaller projection family. The source control lives
at commit `5d2c6e648f75bac11774a1e2886c8b7a65c4c9a2`; this is screening
infrastructure, not a promoted optimization.

The complementary MLP `down_proj` selective fallback is also rejected.
Its real c1 TTFT/TPOT P95 regressed 0.199734%/0.077779%; the rank-0 graph
retained 320 MMAR and exposed 768 ordinary all-reduce occurrences. Evidence
manifest SHA256:
`78e15989e9fcb9580428c702fc83fed65535b93db22455953ca3f8ac8d6886d8`.
This closes all existing MMAR-decomposition variants. P0 is now strictly a
materially new ASCEND910B arch22 MMAR kernel/tiling optimization for the
observed BF16 M=1 shapes, not another enable/disable or prefix split.

## M=1 matmul-core scan closure

The first P0 kernel experiment is also closed. Reducing the physical launch
width violated arch22 Mc2SyncAll/HCCL participation and corrupted output.
After separating full launch width from matmul `usedCoreNum`, real NPU0-3
scans covered 8, 12, 16, 18, 20 and 22 matmul cores. None passed correctness
plus the 1.02x all-shape gate; correct candidates regressed at least one of
the K=1536/K=4352 shapes.

Do not repeat core-count tuning. The remaining P0 implementation target is the
fixed M=1 HCCL orchestration path itself: reduce or overlap the
AllReduce/Commit/Wait/Finalize cost, or amortize it through a materially new
fusion with positive whole-model economics. Full launch participation, BF16
equivalence, TP4 correctness, and exact-shape microbench gates remain
mandatory.

## Active FFN feasibility branch

The next materially different branch tests whether the source-level
`ascend910b` registration can support a dense BF16 SwiGLU specialization,
despite the README marking A2 unsupported and the existing high-performance
SwiGLU contract as FP16-only. This is not yet a supported port or performance
claim.

The exact TP4-local shapes are M in 1/5/8/16, K1=5120, N1=8704, K2=4352 and
N2=5120. Require deterministic correctness and at least 1.10x latency
improvement over the current local three-op chain before vLLM integration.
The row-parallel all-reduce remains required after the local FFN output.

## A2 BF16 dense SwiGLU feasibility closed at M=1 gate

The isolated operator branch
`work/exp-20260907-qwen35-a2-bf16-swiglu-gated-mlp` at commit
`f0a5a5c` replaces the unavailable private `ExecMmOp` dependency with
self-contained MM1, SwiGLU and MM2 stages. Physical 910B4 NPU0 tests used the
exact TP4-local BF16 M=1 shape, deterministic sparse nonzero data, 20 warmups,
100 iterations and five repeats.

Both the candidate and a process-isolated system ACLNN
`MatMul -> SwiGLU -> MatMul` baseline produced four expected nonzero outputs
with zero maximum absolute error against the BF16-rounded analytic reference.
The system baseline median was `197.9728 us`; candidate v1 was `180.2859 us`,
or `1.098104733x`. This misses the predeclared `1.10x` promotion gate, so
do not integrate it into vLLM or extend the M=5/8/16 matrix.

A follow-up that reduced the SwiGLU stage launch count to its three M=1 tiles
preserved correctness but regressed to `206.3268 us`; it was reverted.
Candidate v1 package SHA256 is
`f19d80d998d1db084fe201533b8aacaa0627d08efcd723abcc744431dbe1c1b9`.
Rejected v2 package SHA256 is
`9a65281c2431be1f5cc88c8dfcb80c3d45fdc5184586cc9bcdcfe8e6a03b9e21`.
Full harness and decision details are in
`experimental/ffn/swiglu_gated_mlp/docs/QWEN35_A2_BF16_FEASIBILITY.md`
on the operator branch.

Harness lesson: do not mix system `libopapi` and custom `libcust_opapi` in
one process, and execute each system ACLNN executor before constructing the
next stage. Both unsafe patterns produced heap corruption.

The old `p0` workload was repeatedly relaunched on NPU0-3 by an external
mechanism during this screen. Exact competing containers were stopped or
reversibly renamed to create clean measurement windows. NPU4-7 were not used.

# Dk64 normalization exactness and endpoint-headroom audit

Date: 2026-09-12. Outcome: rejected before implementation. The joint target is
not achieved, and this audit produced no new NPU, graph-timing, endpoint, or
accuracy result.

## Question

After the raw-Q/K Stage 2 operator failed exact output and complete FP32-state
parity at batch1 step1, determine whether a portable exact normalization
primitive could replace it and still remove enough measured work to justify a
new implementation iteration.

## Exact source and compiled evidence

The active source is
`/cache/austinov/src/vllm/vllm/model_executor/layers/fla/ops/l2norm.py`
at commit `0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665`, SHA256
`520f4513ef4fc97e6b88dc07877cca8e29da0d34e44673fe989e3af002d86381`.
For Dk64 it loads BF16, extends to FP32, squares in FP32, reduces 64 values
with Triton `tt.reduce` and FP32 addition, adds epsilon, applies
`math.rsqrt`, multiplies the original FP32-extended input, truncates to BF16,
and stores a materialized normalized tensor.

The captured compiled artifact targets `Ascend910B4`. Its TTIR preserves
`tt.reduce`, `math.rsqrt`, FP32 multiply, and final `arith.truncf` to
BF16. Compiler metadata also records backend-specific lowering and FP-fusion
settings. The failed AscendC implementation used the same high-level formula,
but a generic AscendC reduction and rsqrt path does not guarantee the same
reduction tree, lowering, or rounding. The Stage 2 failure therefore proves
only that the tested implementation missed the predeclared bitwise gate; it
does not prove a storage fault or that the mathematical formula is wrong.

Preserved artifact root:

`/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/dk64-normalization-exactness-audit-v1`

| Artifact | SHA256 |
| --- | --- |
| `l2norm_fwd_kernel2.ttir` | `34d8e2bbbafcd197cf91fdf1e1cacd230e06be766833bbc98c66e3ec45b71d56` |
| `l2norm_fwd_kernel2.ttadapter` | `6963ad42791fcd569f99a659b56e5ba89e024bbfbff5d06bbdabe19dc8c479c1` |
| `l2norm_fwd_kernel2.npubin` | `5bf915acfcdb2a808435a08fe6602bceef1f6c0584ebe9ecb08c04b6b2b8c5d3` |
| `l2norm_fwd_kernel2.json` | `21baacbf291c0aeb8cbd30ba4d1eb68b600bf6e7ff64343e4b0180a1c96650f9` |
| `__grp__l2norm_fwd_kernel2.json` | `0336ad2563df54fe744d66b19c4c452388dd84df8fd2b76bd994b62d7e80f983` |

No reusable CANN L2-normalization primitive was found in the available
`ops-transformer` reference that promises this compiler-specific bitwise
contract across qualified SoCs and runtime versions. Layer-normalization
examples use explicit reduction and rsqrt building blocks; algebraic
equivalence is not a portability guarantee.

## Endpoint-headroom bound

The frozen energy-Dk64 endpoint is 141.564496 output tok/s. The 10 percent
dense-relative boundary is 148.656716909 tok/s, leaving a 5.009887 percent
candidate gap. Under an intentionally optimistic inverse-TPOT model, Dk64 TPOT
would have to fall from 66.689384 ms to 63.507719 ms, a 3.181665 ms saving per
output token.

The four-rank, 30-decode-step profile gives:

| Seam | Aggregate | Per decode step | Perfect-removal throughput ceiling |
| --- | ---: | ---: | ---: |
| separate L2 normalization | 6.055360 ms | 0.201845 ms | 0.303584% |
| full packed front end | 61.383355 ms | 2.046112 ms | 3.165236% |
| recurrent operator | 55.046810 ms | 1.834894 ms | not removable under unchanged semantics |

Even deleting the entire packed front end would leave about 1.135553 ms per
token to recover, or 61.886582 percent of the observed recurrent time. The
recurrent state update cannot disappear while preserving the current
algorithm. These are optimistic serial ceilings, not additive critical-path or
throughput predictions, so they can reject insufficient headroom but cannot
claim an achievable speedup.

## Duplicate-work audit

`DrrqrPlan.transform_weights` already selects retained Q and K projection
rows and the matching causal-convolution rows before the original model loader
and TP sharding. Rank-0 traces also show the reduced GDN projection width
(N=3584 for Dk64 versus N=4096 dense). Therefore a proposed “direct aligned
Dk64 projection-weight slicing” iteration would repeat active behavior rather
than create a new saving.

## Decision and reusable lesson

Reject the normalization-fusion branch at the source/cost gate. Do not build a
new operator, run another parity attempt, weaken exactness, or run an endpoint
screen for this boundary. Do not pivot to duplicate projection or convolution
slicing.

The next DRRQR iteration must introduce a materially different algorithm/state
mechanism. Before implementation it must prove:

1. the saving is not already present in the loaded plugin path;
2. the held-out objective covers recurrent output, not only state or energy;
3. the Dk-specific compute/state/data-movement change has a credible path to a
   material portion of the remaining approximately 3.182 ms per-token gap;
4. logical rank and semantics stay independent of alignment, tiling, compiler,
   and SoC dispatch, with an explicit fallback and per-environment evidence.

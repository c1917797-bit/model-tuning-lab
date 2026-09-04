# Qwen3.5 selective dense FFN NZ

## Paper contract

The implementation is grounded in the small-batch inference principles from
DeepSpeed Inference (arXiv:2207.00032): weight movement dominates many
latency-oriented GEMMs, so inference engines need layout/scheduling
specialization and should fuse only regions with enough measured vector cost.
The paper's GPU speedups are not treated as Ascend evidence.

## Ascend translation

The real TP0 profile on Ascend 910B4 attributes 70.702% of post-prefill summed
kernel duration to MatMulV2. The dominant dense FFN shapes are:

- gate/up: 1x5120 by 8704x5120
- down: 1x4352 by 5120x4352

SwiGLU is only 0.9623% of summed whole-request kernel duration and averages
4.85 microseconds per call. Full FFN fusion is therefore uneconomic unless a
microbenchmark disproves the profile. The installed npu_ffn operator also
rejects the required BF16 SwiGLU path; FP16 substitution and quantization are
not allowed.

The selected treatment retains BF16, global weight_nz_mode=1 and
MatmulAllReduce, but converts only dense MLP gate/up weights to FRACTAL_NZ.
The row-parallel down projection stays ND because the v0.23.0
MatmulAllReduce kernel requires an ND x2 tensor. Attention and recurrent
weights also remain ND.

## Real microbenchmark

The valid artifact is:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/operator-microbench/ffn-bf16-layout-npu4-20260904T220321Z-v2`

It used real layer-0 model weights, TP4 rank-0 shards, BF16, physical NPU4,
M=1/5/8/16, 20 warmups, 100 timed iterations and five rotated-order repeats.
Format checks proved ND=2 and NZ=29.

| M | ND us | gate/up NZ speedup | both NZ speedup |
|---:|---:|---:|---:|
| 1 | 197.629 | 1.0516x | 1.0803x |
| 5 | 200.304 | 1.0546x | 1.0837x |
| 8 | 202.156 | 1.0559x | 1.0841x |
| 16 | 208.426 | 1.0497x | 1.0905x |

Both-NZ geometric-mean speedup is 1.0846x and gate/up-only geometric-mean
speedup is 1.0529x; every output is bit-identical to the ND reference. The
earlier non-v2 directory is preserved but invalid for layout attribution
because internal formats were disabled and its requested NZ tensors remained
ND.

## E2E integration learning

The first E2E startup attempt intentionally applied the microbenchmark winner
to both projections. During graph-capture warmup, down_proj entered
aclnnMatmulAllReduce as FRACTAL_NZ and failed with error 161002 / EZ0017:
x2 must be ND. No benchmark request was measured. The failure is preserved at:

`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/selective-ffn-nz-fixedorig-npu4-7-20260904T2218Z`

This proves that standalone GEMM layout wins cannot be promoted across a
fused communication boundary without an E2E compatibility gate. The retry
therefore keeps the independently profitable gate/up NZ treatment and leaves
down_proj ND while retaining MMAR.

## Corrected E2E result and decision

The gate/up-only retry completed the full immutable quick32 matrix on physical
NPU4-7. Every cell completed 32/32 requests with zero errors and natural stop.

| Concurrency | TTFT p50 ms | TTFT vs original | TPOT p50 ms | TPOT vs original |
|---:|---:|---:|---:|---:|
| 1 | 446.293 | 2.080x | 28.882 | 1.332x |
| 5 | 505.376 | 2.161x | 38.928 | 1.383x |
| 8 | 503.979 | 2.148x | 44.393 | 1.523x |
| 16 | 534.193 | 3.884x | 54.942 | 1.471x |

The fixed-original comparison proves the cumulative MMAR plus gate/up-NZ
runtime is faster, but it does not attribute all of that gain to the layout
treatment. Against the already measured MMAR-only candidate, gate/up NZ
changed TPOT by 0.992x, 1.002x, 1.025x and 0.951x; the geometric mean is
0.992x, or about 0.8% slower. Its c16 TTFT improvement is not consistent with
c1/c5/c8 and is treated as a single-run outlier rather than operator evidence.

Cross-run response hashes drift even for the no-treatment control, so the
automated decision remains hold-exact-hash-drift. A separate correctness-only
c1 control used the same BF16, MMAR-on, NZ1, no-quantization runtime and the
same 32 records. Control and candidate both completed 32/32 with zero errors,
six normalized-whitespace exact matches and mean normalized character
similarity 0.1875. Together with bit-identical operator microbench outputs,
this passes the correctness gate without storing any raw question, answer or
response text.

The final stack decision is therefore: keep MMAR as the current best treatment
and reject gate/up NZ from the cumulative stack because it provides no
incremental TPOT gain. Preserve the implementation and failure evidence for
future kernels, but do not enable the feature flag in the next E2E stack.

## Integration contract

- vLLM-Ascend base: 5cb98caa (v0.23.0)
- experiment commit: 71c25ec9
- flag: `VLLM_ASCEND_ENABLE_DENSE_FFN_NZ=1`
- scope: `*.mlp.gate_up_proj` only; `*.mlp.down_proj` is explicitly ND
- default: disabled
- quantization: none
- rollback: unset the flag and remove the three read-only source overlays

The E2E and privacy-safe correctness gates are complete. Candidate profiling
is skipped because the layout treatment was not retained; the next loop should
start from MMAR and target the remaining TPOT gap.

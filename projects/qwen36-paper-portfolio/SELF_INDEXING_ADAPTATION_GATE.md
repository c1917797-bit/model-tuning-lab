# Self-Indexing Attention: Qwen3.6 Ascend investment gate

Start 2026-09-23 15:30 UTC; stop or decide this paper by 2026-09-24
15:30 UTC. This document is a pre-registered diagnostic plan, not a new
performance or accuracy result.

## Paper and fidelity boundary

The primary source is https://arxiv.org/html/2609.13205v1. Its decode path
applies one fixed randomized Hadamard rotation per layer/KV head to RoPE-applied
Q and K, stores key signs and norms, pools all GQA query heads assigned to one
KV head using coordinate-wise absmax sign, scores cached tokens by
`max(sign_agreement - d/2, 0) * key_L2_norm`, and selects token positions while
forcing prefix and recent windows inside the budget. Each Q head then performs
ordinary QK/softmax/V on the *same selected tokens*.

No verified author implementation repository was located in the first source
audit. Any code here is an equation-derived diagnostic, **not** an official
port. In particular, the exact author's random-sign stream and production
bit-packed kernels are unverified; a fixed per-layer/KV-head sign generator
and unpacked equality count may establish selection quality, but cannot
establish the paper's selector speed or exact author's outputs.

## Applicability and measured opportunity

The deployed Qwen3.6-27B has 16 full-attention layers of 64, 24 Q heads,
4 KV heads and head dimension 256; TP4 maps six Q heads and one KV head to
each worker. This matches the paper's GQA grouping and `d/2=128` score
threshold. It is not the paper-evaluated Qwen3.6-35B-A3B checkpoint.

The frozen four-rank decode trace records `FusedInferAttentionScore` as
27.40025% of summed operator time and MatMulV2 as 50.297%. These sums are
diagnostic, not critical-path shares or an E2E speedup envelope. The paper's
selector and selected-token attention must beat dense **after** rotation,
index maintenance, top-K, gather and graph/scheduler overhead. The previous
Quest 25%/50% page-selected attempt failed a scoped real-Q/K/V quality
investment gate; that does not decide this different token selector.

The current v0.23 native FIA consumes a request-level paged block table. It
does not by itself express arbitrary token indices. `ops-transformer`
BlitzSparseAttention's inspected ABI consumes dense K/V plus sparse block
indices, not this live paged-KV cache. A production port therefore needs a
proven token-gather/sparse-attention bridge or an algorithm-specific plugin
operator; no drop-in claim is made. Reuse an existing source/operator only
after exact ABI, dtype, shape and graph checks.

## One-variable first experiment

An opt-in non-mutating plugin will sample one real decode position at each
of layers 3, 31 and 63 on all four TP ranks. It returns the original dense
output unchanged. On identical live Q/K/V it will validate the rotation
dot-product identity, compare full-support FP32 math with native BF16 FIA,
then evaluate selected exact probability mass and selected-output error for
the paper's 5%-with-768-minimum budget. 10% and 25% are sensitivity points,
not paper defaults. Prefix64/recent64 are always inside each budget.

This is **only** a numerical investment gate. Intermediate tensor error is
not the user's final one-percentage-point LongBench-v2/GSM8K tolerance.
Even good mass is insufficient: next gates would be plugin-owned storage,
NPU eager/graph/multistep numerical correctness, TP4 service dispatch,
profiler-off dense/candidate fixed-1024 E2E performance, then final tasks.

Run only with fresh fail-closed physical NPU4-7 ownership and immutable
artifacts. Do not touch NPU0-3 or unrelated containers. A negative result
must identify whether it rejects this equation-derived selector, the tested
budget/prompt, or the broader paper, and advance without exceeding 24 hours.

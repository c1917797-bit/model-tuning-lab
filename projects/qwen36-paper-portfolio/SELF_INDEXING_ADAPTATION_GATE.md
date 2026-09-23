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

## First real-model NPU diagnostic (v1)

One 20,718-token request generated 12 samples: every TP rank at layers 3,
31 and 63, each with 20,719 live tokens. No probe failure event occurred.
The randomized Hadamard QK dot-product identity had maximum absolute error
`9.16e-5`. Full-support FP32 mathematical attention differed from native
BF16 dense FIA by at most `0.06485` maximum absolute. Thus the sparse
selector gap cannot be attributed solely to the transform implementation
or the full-support mathematical oracle.

| Selected tokens | Min/mean exact mass, across 72 local Q heads | Largest selected mathematical output max-abs vs native dense |
| --- | ---: | ---: |
| 5%, 1036 | 13.954% / 55.339% | 6.157 |
| 10%, 2072 | 18.930% / 70.709% | 3.818 |
| 25%, 5180 | 36.673% / 85.166% | 1.538 |

The first-call transform, score and selection wall times ranged up to 82.65,
64.87 and 48.90 ms respectively; warm samples were far smaller, but none
is a deployable bit-packed selector benchmark. The serving response stayed
dense and HTTP succeeded. The owned container was stopped with exit 0;
physical NPU4-7 returned to process-free ~2.87 GiB HBM, and NPU0-3 were
untouched. Immutable artifacts outside Git:

- `/cache/cch/self-indexing-qwen36-v1/audit.jsonl`: SHA256
  `031b9e24364a8ceb377590963fab6dc2a0f92e1a7fecbe3e55ca5ddaa9536fee`.
- `/cache/cch/self-indexing-qwen36-v1/request-summary.json`: SHA256
  `6ad9498e761d69b0b9036edad9812d61bcb9fcfd4851c0ea52731e820b230396`.
- `/cache/cch/self-indexing-qwen36-v1/admission.json`: SHA256
  `5a4d1c99d8026d394916c5a3b97f34045dd239b13abfcb65e14a1aa442891471`.

This result rejects immediate operator investment for the tested pooled
sign-selector/budget/prompt combination, **not** the paper or the user's
task-accuracy target. The next, distinct falsification asks whether
per-Q-head sign scores or exact-logit Top-K on the same live Q/K can recover
mass at the same 5%/10%/25% budgets. If even the exact-logit oracle is poor,
the budget is the limiting factor; if it is strong and the sign variant is
weak, the index/score is the limiting factor. A new immutable v2 root and
one new run are required; never overwrite v1.

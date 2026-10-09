# HYPIC BF16 RoPE numerical screen — bounded diagnostic

## Scope and source

This is a CPU-only, deterministic arithmetic screen of the **actual**
`hypic_vllm_ascend.patches.attention._anchor_rope` function at plugin commit
`c12060cd47e7575ead059983d7a8bb4704165c98`. It uses Qwen3.6-27B
`config.json` SHA256
`69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c`:
BF16, head dimension 256, rotary dimension 64, and theta 10,000,000. The
RoPE cache is **synthetic**, not captured from a live worker. Seed 17 produces
1024 keys × 4 KV heads. Only the 64 rotary dimensions are scored; the other
192 dimensions are asserted unchanged.

Run on chicaihong01 without allocating an NPU:

```sh
/cache/cch/python-envs/model-tuning-lab-py311/bin/python -B \
  .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_hypic_rope_bf16_screen.py \
  --plugin-root /cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008 \
  --model-config /cache/efim/Qwen3.6-27B/config.json
```

The comparator widens only the inverse/forward RoPE arithmetic to FP32.
It still quantizes the canonical cached K to BF16 between the two rotations,
so it does not assume an unrealistic FP32 material cache.

| Anchor | Current BF16 MAE | FP32-compute/BF16-store MAE | Current changed elements | Widened changed elements |
|---:|---:|---:|---:|---:|
| 1 | 0.00057943 | 0.00007653 | 13.16% | 4.39% |
| 128 | 0.00127557 | 0.00019924 | 28.73% | 9.80% |
| 4096 | 0.00159202 | 0.00027553 | 36.55% | 13.60% |
| 16384 | 0.00196373 | 0.00027453 | 43.49% | 13.56% |

The current implementation has measurable BF16 round-trip loss that increases
with these sampled anchors. A computation-only widening reduces this synthetic
same-position error while keeping BF16 storage. But same-position recovery is
not the production oracle: the cached key is made at a source anchor and
relocated to a different target anchor. The direct native BF16 target key is
the relevant comparator. The verifier also exercises that path:

| Source → target anchor | Current MAE vs direct target | Widened MAE vs direct target | Current changed elements | Widened changed elements |
|---:|---:|---:|---:|---:|
| 1 → 4096 | 0.00064516 | 0.00133205 | 12.06% | 31.81% |
| 128 → 4096 | 0.00141168 | 0.00164524 | 26.44% | 37.00% |
| 4096 → 16384 | 0.00178415 | 0.00195941 | 34.54% | 43.19% |

Thus FP32-compute/BF16-store is **not admitted as a repair**: in all three
sampled cross-anchor comparisons it is farther from the direct native BF16
target. This does not establish that RoPE caused the frozen r13 LongBench-v2
quality change (230/381 to 219/381), nor that the current path is acceptable
on NPU. The original FP32-only source-unit test did not cover BF16 or
cross-anchor relocation. No r13 result, acceptance gate, plugin source, or
immutable raw root was changed. The lesson is to use the target runtime's
native finite-precision output as the correctness oracle, not only
mathematical round-trip identity.

## Next falsification gate

Before any quality rerun or source fix, compare the pinned runtime's actual
fused-MRoPE cache and NPU K tensors for a fixed full-attention segment.
Measure direct native target K against current canonicalize/relocate, then
trace whether the difference reaches attention output/logits. Do not promote
the widened variant based on the same-position screen. Separately test GDN
transition parity. Pre-register the first-divergence criterion and
one-switch scope in a new immutable diagnostic root. Reject the RoPE
hypothesis if its differences do not propagate materially; never
retroactively reclassify r13.

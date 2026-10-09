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
error while keeping BF16 storage. This **does not establish** that RoPE caused
the frozen r13 LongBench-v2 quality change (230/381 to 219/381), nor that a
widened path is safe or faster on NPU. The FP32 source-unit test had not
covered this BF16 case. No r13 result, acceptance gate, plugin source, or
immutable raw root was changed.

## Next falsification gate

Before any quality rerun or source fix, compare the exact pinned runtime's
fused-MRoPE cache and actual NPU K tensors for a fixed full-attention segment.
Measure original cache-write/read versus the current canonicalize/relocate
path and a computation-only widened variant, with the same BF16 material
storage and physical NPU0–3 isolation. Also test the independent GDN state
transition path. Pre-register the first-divergence tensor/logit criterion and
one-switch scope in a new immutable diagnostic root. If RoPE differences do
not propagate materially to the relevant output/logits, reject this
hypothesis; do not retroactively reclassify r13.

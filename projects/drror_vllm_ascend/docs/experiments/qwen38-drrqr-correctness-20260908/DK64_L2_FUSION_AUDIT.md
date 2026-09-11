# Dk64 L2-only fusion audit

Decision: do not build an L2-only recurrent fusion as the next primary
candidate. Broaden the exact seam to packed-QKV plus L2 plus recurrent so the
prototype can remove a material rearrangement as well as normalization
materialization.

## Actual path

- Ascend GDN source SHA256:
  `d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816`.
- Imported vLLM L2 source SHA256:
  `520f4513ef4fc97e6b88dc07877cca8e29da0d34e44673fe989e3af002d86381`.
- Qwen GDN base source SHA256:
  `885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0`.
- Runtime import resolved to
  `/vllm-workspace/vllm/vllm/model_executor/layers/fla/ops/l2norm.py`.
- `USE_DEFAULT_FLA_NORM=0`, so decode uses
  `l2norm_fwd_kernel2`.
- Semantics are FP32 square and reduction, `rsqrt(sum + 1e-6)`, followed by
  BF16 output materialization. Recurrent then reloads that BF16 Q/K and applies
  its scale/state arithmetic.

Any packed fusion must preserve the BF16 rounding boundary explicitly. A
mathematically close FP32-only fusion is not an exact replacement.

## Cost ceiling

The existing four-rank, 30-step Dk64 diagnostic profile reports:

- decode rank-mean kernel envelope: 1350.83691 ms;
- `l2norm_fwd_kernel2`: 6.05536 ms, about 0.448 percent of that envelope;
- recurrent: 55.04681 ms.

These diagnostic aggregates are not additive critical-path proof. They are
sufficient to reject L2-only fusion as the primary route: even free removal of
the L2 kernels cannot close the remaining roughly 5.01 percent candidate
throughput gap, and in-kernel normalization is not free.

At batch16, Q plus K contains 16 KiB per layer. L2-only fusion can avoid about
32 KiB of normalized-Q/K global write and reread plus two launches per layer.
The broader packed composition can additionally avoid the Q/K/V concatenating
copy and its launch, so it has the stronger saved-versus-added case.

## Next bounded candidate

The next iteration consumes the causal-convolution packed QKV tensor directly,
uses explicit packed offsets for Q/K/V, normalizes Q/K locally with the exact
epsilon and BF16 rounding boundary, and reuses the validated recurrent state
path. The existing unfused composition remains the portable fallback. NPU
numerical/state/graph parity is mandatory before timing.

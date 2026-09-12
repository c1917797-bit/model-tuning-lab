# T26: upstream parallelism and MC2 applicability audit

Status: closed without device use. This is an admission audit, not a
performance result.

## Fixed boundary

The delivery contract remains BF16, TP4/DP1 on physical NPU0-3, unchanged
official vLLM-Ascend v0.23.0 image, MTP/speculation/quantization disabled, and
a removable runtime Python monkeypatch. The current c1 target still requires
about 6.10 ms/token additional saving. T20 bounded prefill remains only a TTFT
component.

## Dense FFN NZ is already closed

The explicit runtime setting
`VLLM_ASCEND_ENABLE_DENSE_FFN_NZ=0` is an evidence-backed rollback, not an
unexamined default. Exact real-weight BF16 microbenchmarks found gate/up-only
NZ about 1.0529x faster in isolation and both projections about 1.0846x faster,
with bit-identical outputs. However, the corrected gate/up-only full service
had only 0.992x geometric-mean incremental TPOT speedup versus the retained
MMAR candidate and regressed some cells. Down-projection NZ also violates the
MMAR input contract. Do not repeat this candidate unchanged.

## Fine-grained MLP TP is inapplicable

The pinned v0.23 source already contains `mlp_tensor_parallel_size`, but its
configuration rejects dense models. Later upstream documentation relaxes that
model restriction while clarifying that MLP fine-grained TP shards across the
DP axis and is effective only when standard `tensor_parallel_size == 1`.
Therefore it cannot optimize the required TP4/DP1 service. The related TP2/DP2
topology has also already been rejected by capacity gates and by a real 32K
conditional E2E run whose TPOT regressed in every concurrency cell.

## Other MC2 routes

- `AttentionToFFN` and `FFNToAttention` are A3-only expert-routing /
  disaggregated-FFN operators. Their contracts require expert IDs and separate
  Attention/FFN workers; they do not match this A2 dense graph.
- `MatmulAllReduceAddRmsNorm` and its inplace form support A2 BF16, but the
  prior v13-v17 integration already regressed the complete E2E matrix despite
  a strong isolated operator result. Upstream later removed the vLLM-Ascend
  pass as deprecated/internal. Do not revive it unchanged.
- The clean ops-transformer v9.1.1 source is aligned with the installed CANN
  9.1 runtime. Its supported A2 BF16 base `MatmulAllReduce` is already the
  retained service path; the local newer master snapshot provides no
  demonstrated replacement A2 BF16 dense-chain implementation.
- HCCL AIV, sequence-parallel decomposition, MMAR-off, buffer/core scans,
  online tiling, async finalize, AICPU-first, and IPC fullmesh have existing
  negative gates and remain closed.

## Decision

No configuration-only or existing upstream operator substitution found in
this audit can credibly close the remaining c1 decode gap under TP4. Device use
is therefore not justified for these routes.

The next candidate must be materially new while still beginning from the
supported ops-transformer A2 BF16 MMAR implementation. It must change a
profile-proven complete projection/collective critical path, not merely one
overlapping AICPU interval, and must first demonstrate a conservative
whole-token budget capable of approaching 6.10 ms/token. Any operator package
must remain read-only and optional; final activation and rollback stay within
the runtime monkeypatch boundary.

# T37 upstream paged-attention workspace reuse findings

## Decision

Reject the exact upstream paged-attention workspace-reuse backport on the
official vLLM-Ascend v0.23.0 target stack. Remove the implementation and its
activation/test plumbing from the delivery branch. Retain this document and
the immutable target artifacts so the same treatment is not repeated without
a materially different compatibility explanation.

## Upstream boundary

T37 was an exact source-shaped backport of vLLM-Ascend commit `827a11d3`.
That change reuses the result of
`torch_npu._npu_paged_attention_get_workspace` for compatible attention
entries within one `update_graph_params` pass. The reuse key covered live
sequence-length storage, query/cache/block-table/output shapes and dtypes,
head counts, and scale. Reuse never crossed a decode step.

The Qwen3.5-specific work was limited to a fail-closed v0.23.0 runtime
monkeypatch seam, four-rank activation proof, and lifecycle integration. No
model weights, operator math, quantization, speculative decoding, framework
source tree, or base image was replaced.

## What passed

Artifact root:
`/cache/austinov/qwen35-t37-pa-workspace-service-20260914-v2`.

- unchanged official image ID
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`;
- Qwen3.5-27B BF16, TP4, physical NPU0-3 only;
- all four ranks emitted the workspace-reuse activation marker;
- activation report passed and has SHA-256
  `bf5ff77547f8b9b09f5561e78c1195e6f3623c3162058784a256222f389ceefe`;
- one smoke request completed with zero errors and natural EOS.

These checks prove that the intended code executed; they do not admit its
behavior or performance.

## Why it failed

For the same first smoke prompt, retained T36 produced 104 completion tokens
with response SHA-256
`6f2f76bcca70604c4c152bfa3754c14406c3351d2614bc8c16d9310fddfe9131`,
while T37 produced 113 completion tokens with response SHA-256
`6b1728172d88b4be63ba84394a962954492e69a34faef8016f58bc90510dd694`.
The query-rewrite dataset has empty reference answers, so neither response is
an accuracy oracle, but a supposedly workspace-only optimization must not
change deterministic greedy output. The mismatch is therefore a fail-closed
behavioral rejection.

The subsequent formal c1 job also failed to emit a result within the
900-second outer timeout, whereas comparable retained T36 runs completed in
about 208-215 seconds. The service remained healthy, so the failure is not
explained by normal startup or a crashed worker. This is a severe target-stack
latency/liveness regression.

## Durable lesson

Upstream provenance is necessary but not sufficient. A change reported as
functional-equivalent on another CANN/device/release combination must still
pass the exact target's fixed-prompt hash, bounded completion-time, c1
fail-fast, full concurrency matrix, and reference-backed quality gates.
Workspace lifetime and graph-update ordering are compatibility boundaries.
Do not retry `827a11d3` unchanged on v0.23.0.

The retained optimization base remains T32 fused prefill plus the experimental
T35/T36 decode stack. T36 still misses the c1 TPOT target by 0.511 ms/token;
the next candidate must be non-overlapping, upstream-derived, numerically
gated, and budget-credible above that remaining gap.

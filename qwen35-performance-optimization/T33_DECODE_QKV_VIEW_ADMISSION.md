# T33: upstream-derived zero-copy M1 decode QKV admission

## Decision

Admit an opt-in live c1 screen for a zero-copy M=1 QKV layout path. This is a
decode candidate, not a performance claim.

## Current budget

The retained T32 fused-prefill candidate measured c1 TPOT P95
`28.2763 ms/token`. The corrected 10-percent target from the fresh v14
control is `26.018 ms/token`, leaving `2.2583 ms/token`.

The exact T16 profile contains 48 GDN layers per decode token. Upstream
vLLM-Ascend commit `2bb515688` measured a redundant QKV rearrange at about
70 microseconds per GDN layer for a single decode token in a mixed batch.
That is a directional upper bound of about `3.36 ms/token`; it is not added
to any overlapping operator duration.

## Implementation

The existing monkeypatch already backports upstream Qwen3.5 six-way input
projection fusion. The new opt-in path extends the upstream rearrange-reuse
principle to the exact pure-decode M=1 shape:

1. split the packed `[1, q+k+v]` tensor into Q, K, and V column views;
2. reshape those views to the existing recurrent-kernel ABI;
3. use them only when all three views are contiguous;
4. fall back to the official rearrange implementation for every other shape.

Because the leading dimension is one, PyTorch's contiguity rule ignores its
larger stride and each column slice is already contiguous. No tensor values,
dtype, head order, collective order, or state update is changed.

The service variant is
`candidate-fused-prefill-decode-view`. It retains the T32 fused-prefill path,
disables the retired weight-prefetch hooks, maps only physical NPU0-3, and
uses the unchanged official vLLM-Ascend v0.23.0 image.

## Gates

- device-free M1 storage-alias, value, shape, and contiguity tests;
- explicit non-M1 fallback test;
- four-rank activation with no source overlays;
- real-request natural EOS with zero errors;
- c1/32 fail-fast against the frozen fresh v14 control;
- retain only if TTFT reduction remains at least 20 percent and TPOT reduction
  reaches at least 10 percent.

Failure at any live gate retires this exact implementation; threshold rounding
or an unchanged rerun is not allowed.

## Live result

Rejected after the warmed same-service c1/32 fail-fast on 2026-09-13.

- Artifact root: `/cache/austinov/qwen35-fused-prefill-decode-view-service-20260913-v1`.
- Activation passed on the unchanged official image with one read-only
  monkeypatch mount, physical NPU0-3 only, no source overlay, no custom OPP,
  and all four TP worker bindings proven.
- One real smoke request completed with zero errors and natural EOS.
- The separate warmup completed 32/32 with zero errors and natural EOS.
- The formal cell completed 32/32 with zero errors and natural EOS.
- Formal TTFT P95 was `609.652 ms`, a `27.515%` reduction from the fresh
  control median `841.073 ms`; this passes the `672.858 ms` gate.
- Formal TPOT P95 was `29.530 ms`, a `2.147%` regression from the fresh
  control median `28.909 ms`; this fails the `26.018 ms` gate.

The zero-copy M=1 view changed storage preparation but did not remove enough
of the measured decode critical path. Do not rerun this exact implementation
unchanged and do not compose it into the retained T32 prefill component.

Evidence SHA256 values:

- activation: `d5a254803e4a3b53c0ce3a71079ae7ffe778d685fa7633474c4769761e44c1a7`
- smoke: `d96944a938782f60fc21627c779a12b1236a01b07ee486b339d386270353e569`
- warmup: `611aeeb2cb93d587a524bb3128098bc1ae86eb3ac7cb74aaab4217d30f093259`
- formal c1: `97ce877b827296d5e63dba23eb75ecb9b55736f8baac827b19c553089de34aec`

The `EngineDeadError` at the end of `service.log` follows the explicit
SIGTERM shutdown sequence after all formal requests completed; it is teardown
noise, not a benchmark request failure.

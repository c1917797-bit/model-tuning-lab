# T32 upstream fused GDN prefill findings

## Scope

Backport the upstream vLLM-Ascend `torch_npu.npu_chunk_gated_delta_rule`
prefill path from commit `77d13e2c0` into the unchanged official v0.23.0
image. Compose it with this workstream's Qwen3.5 six-way GDN projection
fusion and weight-prefetch lifecycle. Keep the treatment removable through a
single read-only Python monkeypatch mount.

## Numerical admission

The official-image NPU0 comparison against the v0.23 Triton reference passed
for 64, 257, and 1807 tokens. Output and recurrent-state relative L2 errors
were below 0.44 percent. Evidence roots:

- `/cache/austinov/qwen35-fused-prefill-numerical-20260913T074053Z`
- `/cache/austinov/qwen35-fused-prefill-numerical-20260913T074256Z`

This admits the operator to service integration; it does not prove end-to-end
quality or performance.

## Service integration failures retained

### v1

Artifact root: `/cache/austinov/qwen35-fused-prefill-service-20260913-v1`.
The service became ready and passed static activation, but the first request
failed before producing a token. The injected `_forward_core` called
`self._qwen35_probe_fused_chunk()`. At that boundary, `self` is
`QwenGatedDeltaNetAttention`, while the helper is installed on
`AscendGatedDeltaNetAttention`.

### v2

Artifact root: `/cache/austinov/qwen35-fused-prefill-service-20260913-v2`.
The service became ready, passed the complete four-rank activation report,
and mapped only physical NPU0-3. The first real request then failed on all
ranks with:

`AttributeError: 'QwenGatedDeltaNetAttention' object has no attribute '_qwen35_fused_chunk_gated_delta_rule'`

The probe call had been bound to the backend class, but the actual fused
helper call still used `self`. Both injected helper calls must be explicitly
bound to `AscendGatedDeltaNetAttention`; startup/activation markers alone do
not exercise the compiled request path.

## Durable gate

The source contract now requires both exact backend-class calls. A candidate
is not admitted to performance testing until a real request produces the
device-probe-passed marker on all four TP ranks, returns tokens, terminates by
natural EOS, and leaves the service healthy.

## Resume point

Start a fresh v3 service from the corrected monkeypatch, recapture activation,
then run a separate 32-request c1 warmup. Only a clean warmup may proceed to
the formal c1 fail-fast gate against the fresh v14 control thresholds.

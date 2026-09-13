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

## v3 valid fail-fast result

Artifact root: `/cache/austinov/qwen35-fused-prefill-service-20260913-v3`.
The service passed activation, and all four TP ranks passed the actual-device
probe with zero fallback markers. A separate 32-request warmup completed with
zero errors and natural EOS. The formal c1/32 run also completed 32/32 with
zero errors and natural EOS:

| Metric | Fresh v14 control | v3 candidate | Reduction | Required |
|---|---:|---:|---:|---:|
| TTFT P95 | 841.073 ms | 617.432 ms | 26.590% | >=20% |
| TPOT P95 | 28.909 ms | 28.276 ms | 2.189% | >=10% |

The upstream fused GDN prefill is retained as a valid TTFT component, but it
is not a final candidate because it misses the TPOT gate. Do not run the full
concurrency matrix for this component alone.

Evidence SHA256 values:

- activation report: `cdb699da8807ba9899f7c15ba759529cb79ccd81a8c19419c152979f67479a55`
- warmup result: `c9b679feeb2f766c9a88874dc3ee6029aec23aaf64bb7b0322a184a0e1c14ee5`
- formal c1 result: `561acf2aa85d38a6b4e924fee445809dab892875df4ee19bcbe55019e04fe875`
- final service log: `6f8257b01365e5d272575e6e59295216ea270134c46c26097a709e85a48617ca`

## Resume point

Keep the v3 fused-prefill treatment as the TTFT base. Continue the upstream
audit on the decode/collective path and add only a profile-grounded component
that can close the remaining TPOT gap without sacrificing the TTFT win. Run a
fresh c1 fail-fast on the combined stack before any full matrix or quality
promotion.

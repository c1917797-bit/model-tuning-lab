# Dk64 native packed gating/recurrent audit

Date: 2026-09-12

## Decision

Admit a staged, uniquely named native Ascend candidate that ultimately consumes the causal-convolution packed QKV representation and spans Q/K normalization, gating, and recurrent FP32 state traffic. Do not promote it to an endpoint screen until each added semantic boundary passes its own NPU numerical and NPUGraph gate.

This candidate directly enables the accepted energy-Dk64 DRRQR algorithm. It is not a generic replacement for the dense path and does not change the selector, logical rank, or recurrence definition.

## Measured reason to implement

The existing four-rank, 30-decode-step profile reports the following Dk64 rank-mean kernel aggregates:

- packed QKV slice: 11.808380 ms;
- beta/A slice: 10.883665 ms;
- Q/K/V concat: 21.657215 ms;
- fused gating: 10.978735 ms;
- two L2 normalizations: 6.055360 ms;
- recurrent gated delta rule: 55.046810 ms.

The packed front end totals 61.383355 ms and the front end plus recurrent totals 116.430165 ms. These sums identify a materially larger implementation seam than L2-only fusion. They are diagnostic aggregates, not an additive critical path and not a prediction of endpoint throughput.

The fixed dense baseline is 135.142469917 output tok/s and the 10 percent target is 148.656716909 output tok/s. Energy-Dk64 reached 141.564496 output tok/s, so the candidate still needs about 5.009887 percent additional throughput. The prior packed-QKV/L2 Triton composition reached only 140.583188 output tok/s and was rejected.

## Authoritative execution contract

The actual Ascend decode path is causal convolution, packed-QKV rearrangement, `DeviceOperator.fused_gdn_gating`, two `l2norm_fwd` calls, and `torch.ops._C_ascend.npu_recurrent_gated_delta_rule`. Service traces use BF16 Q/K/V/beta, FP32 g, and FP32 recurrent state. The v0.23.0 reference source commit is `5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`.

Before changing the interface, the plugin-owned native separate-Q/K/V control was rerun with the service's FP32 state contract. Batch 1 and 16, eight changing steps, eager and NPUGraph replay all passed exact BF16 output and complete mutable FP32-state comparison, guard and untouched-slot checks, stable storage pointers, and provenance capture. The report is:

`/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/dk64-native-layout-control-v1/native-control-parity-v1-fp32/report.json`

SHA256: `2a83504c777205525e33055e097b21152eac583a8aed23b489004d1fb9e6e303`

This proves only the native control ABI and storage behavior. It does not prove packed addressing, arithmetic fusion, endpoint speedup, task accuracy, or cross-environment performance.

## Staged implementation

1. Stage 1 consumes one packed already-normalized BF16 Q/K/V tensor and retains the frozen recurrent arithmetic. It must match the separate-Q/K/V native control bitwise for output and full FP32 state in eager and NPUGraph modes.
2. Stage 2 consumes raw packed BF16 Q/K/V and performs Q/K normalization with FP32 square, reduction, and reciprocal square root using epsilon `1e-6`. It must materialize the same BF16 rounding boundary before recurrence. Its numerical tolerance must be declared before running.
3. Stage 3 adds gating only if Stage 2 is correct and graph-path timing justifies the complexity. It must preserve the softplus threshold, BF16 beta rounding, and FP32 g behavior of the loaded path.

The operator derives Dk, Dv, and value-head count from state, derives key-head count from packed width, validates exact divisibility and grouping, and keeps logical rank independent of kernel tiling. It has a unique name, explicit opt-in dispatch, and the existing composition as correctness fallback. All source, build, and artifact identity remains plugin-owned.

## Stage 1 result

Stage 1 is implemented and passed its exact target-runtime gate in one run on physical NPU4. Batch 1 and 16, eight changing steps, eager execution and NPUGraph replay matched the native separate-Q/K/V reference bitwise for BF16 output and the complete mutable FP32 state. Guard regions, untouched slots, storage pointers, metadata and finite-value checks also passed.

The report is:

`/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/dk64-packed-recurrent-stage1-parity-v1/report.json`

SHA256: `caf98324fd5ac5f5177abb2d291d0fbc60e289b715c80871f7f01f4a8c1f5174`

The build manifest SHA256 is `dd8516b2ed7d108125f47d21e82193853675f72e07ba7e5f788ac11790209d62`; the loaded bridge SHA256 is `8abdfc778c64466b766797d8915167520f411ee065fea3fa7bf2f73573e5ee41`; and the loaded candidate opapi SHA256 is `a1f6478acdf47a3a65e263338c235e8042596754d7c96befcd96cec8119ad8b3`.

This result proves only packed addressing, shape derivation, storage behavior and unchanged recurrent ABI correctness on the qualified 910B environment. It does not prove raw-Q/K normalization, gating, vLLM integration, endpoint speedup, task accuracy, or cross-environment performance. The next bounded step is Stage 2 raw packed-Q/K normalization with a numerical gate declared before execution.

## Rejected repetitions

- Do not repeat the K64-only reduction specialization: it passed parity but regressed NPUGraph replay.
- Do not repeat L2-only fusion: its measured surface is too small for the remaining endpoint gap.
- Do not repeat a Triton packed materializer in front of the unchanged recurrent call: it lost endpoint performance versus energy-Dk64.
- Do not run final accuracy until a candidate survives the fixed-output endpoint screen.

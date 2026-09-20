# Qwen3.6 GDN decode mega-op requirements

## Scope

Create one independent Ascend operator and a thin vLLM-Ascend plugin adapter
for the Qwen3.6 decode-only GDN path. The candidate must preserve the existing
model computation and state semantics; it is not a new approximate algorithm.

## Observed production seam

The v0.23 decode path performs these operations per GDN layer and decode step:

1. transpose static causal-convolution weights;
2. causal convolution with in-place convolution-state update;
3. unpack/rearrange mixed QKV;
4. fused GDN gating;
5. independent Q and K L2 normalization;
6. recurrent gated-delta-rule execution with indexed in-place FP32 state
   update.

The current profile attributes 14.15340% of decode operator time to the
shape-filtered chain. The implementation is useful to the final objective only
if it can cover that exact seam and reach at least 2.79680x local speedup before
end-to-end testing.

## Interface truth to resolve before freezing spec

The following facts must be copied from the actual v0.23 schemas, adapters, and
arch22 kernels rather than guessed:

- tensor names, rank, logical axes, physical layout, and contiguity;
- BF16/FP32/INT32 dtype contract;
- batch, local Q/K head count, local V head count, Dk, Dv, convolution width,
  and slot/state-index constraints;
- which inputs and outputs alias;
- exact convolution-state and recurrent-state mutation order;
- gating formulas and the placement/epsilon of Q/K normalization;
- eager versus graph-mode constraints;
- workspace, alignment, and tiling requirements.

## L0 semantic composition

CannBot classification is `FusedComposite`. Candidate paradigms are
`LayoutTransform`, `Reduction`, `SlidingWindow`, `Recurrence`,
`Stateful`, `NumericalStable`, and `FusedComposite`, subject to strict
registry validation.

Use only registered white-box primitives:

- `permute`, `conv`, `slice`, and optionally `concat` for packed QKV;
- `elementwise_unary`, `elementwise_binary`, and `reduce` for gating and
  L2 normalization;
- `gemm` plus elementwise primitives for the recurrent delta-rule update;
- `cast` only where the observed ABI requires it.

Do not add a fictitious `recurrence` primitive. The `Recurrence` paradigm
describes cross-step semantics; composition remains an explicit dataflow.

## Delivery and compatibility

- All authored source, build scripts, adapters, tests, and manifests live in
  this project directory.
- The operator has a unique project name and cannot replace global upstream
  registrations silently.
- Activation is explicit and disabled by default.
- The adapter probes runtime capability and fails closed on unsupported
  versions, shapes, dtypes, layouts, or NPU architectures.
- v0.23-specific symbol binding stays in a thin adapter; L0 semantics and
  operator implementation must not depend on the vLLM-Ascend source path.
- Current implementation target is Ascend 910B4 / DAV_2201. Other architectures
  require a separately validated implementation path.

## Verification order

1. CannBot-generated `spec.yaml`, completed by hand and strict 11-stage PASS.
2. Host reference tests for shape/dtype/dispatch logic only; these do not prove
   performance or NPU correctness.
3. One bounded real-NPU multi-step stateful correctness matrix on physical
   NPU4-7.
4. Eager and graph-replay determinism plus loaded-library hashes.
5. Local affected-route gate.
6. Paired profiler-off service A/B, fixed output 1024, three repetitions.
7. Final paired LongBench-v2 and GSM8K, thinking disabled, max_tokens=2048,
   normal EOS.

No later stage may override a failure in an earlier gate.

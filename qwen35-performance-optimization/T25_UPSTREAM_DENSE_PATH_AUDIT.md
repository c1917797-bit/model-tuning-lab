# T25 upstream dense-path audit

Date: 2026-09-11. Branch-local evidence; no NPU was used and no candidate is
promoted.

## Decision

The newly inspected upstream changes do not supply a compatible missing
Qwen3.5-27B BF16 dense-decode implementation for the pinned
vLLM-Ascend 0.23.0 / Ascend 910B4 stack. Do not port the 310P ACLGraph path,
the MRV2 replay synchronization patch, or the unresolved experimental
SwigluGatedMlp ACLNN wrapper.

## Evidence

- vLLM-Ascend commit `4b1d43a6264fc9bbbbb06786922300326ac16216`
  is already an ancestor of the pinned target commit
  `5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`. Its implementation is confined
  to `_310p` Python code and `causal_conv1d_v310` kernels. It integrates the
  310P recurrent GDN operator; it is not a generic A2/910B4 dense-MLP fusion.
- The related RGDR optimization `928fa1d862a99230e3cfc69c394dcb8a01c334be`
  is also 310P-only. Its reported gains are scalar-pipe and UB-conflict
  reductions in `recurrent_gated_delta_rule_v310`, not the measured
  `gate_up -> SwiGLU -> K4352 MatmulAllReduce` critical path.
- Later accuracy fixes `0867d57ca` and `9154baadc` document 310P-specific
  graph/state hazards. This is additional evidence against transplanting that
  path into the 910B4 service merely because the model name matches.
- vLLM-Ascend `804317471` replaces a device-wide graph replay barrier with
  stream ordering, but only under the later MRV2 worker. The pinned service is
  MRV1, so it has no compatible seam for a runtime backport.
- vLLM-Ascend `432743d83` moves causal-conv metadata fully onto device
  tensors. The pinned target's Python GDN path already passes device metadata
  into `npu_causal_conv1d_custom`; the later commit also changes the custom-op
  ABI and kernels. Its published performance result is a small A5
  MTP/quantized throughput gain, not evidence for the present BF16 dense,
  MTP-off TPOT gap.

The ops-transformer audit was refreshed from its real checkout at
`/cache/cch/ops-transformer`. The current 9.1 release ref is
`0684247214bae5abb5cb6dc7d90b34a6ad401cdd`; current master is
`d967eeb08ceef7c394d0d5e27767e5b08b77aa58`. In both, experimental
`SwigluGatedMlp` still calls the private
`Ops::NN::ExecMmOp(...)` symbol. No later change replaces this dependency or
adds a vLLM-Ascend adapter. Therefore the T21 unresolved-symbol rejection is
still current. Supplying a private replacement symbol would conceal an
upstream ABI defect and remains forbidden.

## Performance implication

No candidate above can credibly supply the required approximately
`95.29 us/layer` saving from the exact T16 dense-tail union. The retained
`candidate-prefill` remains the TTFT component; none of these changes earns
TPOT credit.

## Next admission

Continue from the exact T16 non-overlapping profile and search supported A2
BF16 mechanisms that materially change dense weight movement or the complete
projection/collective chain. Reject candidates before device use unless their
measured or conservative bound can contribute to the roughly
`6.10 ms/token` c1 TPOT gap. Preserve the official MMAR collective, the
unchanged image, runtime-monkeypatch delivery, and all numerical/service
quality gates.

## Later supersession

The unresolved-symbol rejection above was accurate for the unchanged package
but is superseded by T27. T27 uses the official CANN 9.1 six-argument
`ExecMmOp` export and does not add a replacement matmul. This only admits the
adapted upstream operator to guarded device validation; it changes no
numerical, performance, integration, or promotion gate.

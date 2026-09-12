# DrrqrPackedRecurrentV1

This is an independently named, opt-in staged DRRQR research operator. The
current Stage 2 source consumes one token-major raw BF16 Q/K/V tensor,
normalizes Q/K in FP32 with epsilon 1e-6, materializes the normalized values
through BF16, and then executes the frozen Ascend recurrent gated-delta-rule
arithmetic. It reuses a normalized Q/K head across value heads handled by the
same block. It is not enabled by the vLLM plugin by default.

The implementation was mechanically derived from
`vllm-ascend/csrc/attention/recurrent_gated_delta_rule` at v0.23.0 commit
`5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`. The transformation isolates all
operator identifiers, changes Q/K/V input addressing to the packed row,
derives and validates head dimensions from the packed width plus state shape,
and leaves recurrent arithmetic and state semantics unchanged. Stage 2 also
uses the active vLLM FLA l2norm_fwd_kernel2 arithmetic boundary as its
reference; that source identity is recorded in provenance.json.
`provenance.json` records the immutable upstream file hashes.

Acceptance for this control is deliberately strict: BF16 output and the full
mutable FP32 state must be finite and bitwise identical to the native operator
for the declared TP4 Dk64 eager and NPU-graph matrix. That gate passed on
physical NPU4 for batch 1 and 16 across eight changing steps; the report SHA256
is `caf98324fd5ac5f5177abb2d291d0fbc60e289b715c80871f7f01f4a8c1f5174`.
It proves only the immutable Stage 1 packed addressing, shape derivation,
storage behavior and unchanged recurrent ABI correctness on the qualified
910B environment. The current Stage 2 source is not covered by that report
until a fresh build and raw-Q/K parity matrix passes. No current evidence
proves Stage 2 normalization, gating, endpoint speedup, accuracy,
cache-manager integration, or portability to untested Ascend stacks.

The copied CANN sources retain their original CANN Open Software License 2.0
headers. The torch adapter header retains its upstream Apache-2.0 header.

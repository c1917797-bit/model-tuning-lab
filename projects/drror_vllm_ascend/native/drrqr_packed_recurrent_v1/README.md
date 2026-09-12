# DrrqrPackedRecurrentV1

This is an independently named, opt-in DRRQR Stage 1 research operator. It
consumes one token-major packed, already-normalized BF16 Q/K/V tensor while
reproducing the frozen Ascend recurrent gated-delta-rule arithmetic and
mutable-state behavior exactly. It is not enabled by the vLLM plugin by
default.

The implementation was mechanically derived from
`vllm-ascend/csrc/attention/recurrent_gated_delta_rule` at v0.23.0 commit
`5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`. The transformation isolates all
operator identifiers, changes Q/K/V input addressing to the packed row,
derives and validates head dimensions from the packed width plus state shape,
and leaves recurrent arithmetic and state semantics unchanged.
`provenance.json` records the immutable upstream file hashes.

Acceptance for this control is deliberately strict: BF16 output and the full
mutable FP32 state must be finite and bitwise identical to the native operator
for the declared TP4 Dk64 eager and NPU-graph matrix. That gate passed on
physical NPU4 for batch 1 and 16 across eight changing steps; the report SHA256
is `caf98324fd5ac5f5177abb2d291d0fbc60e289b715c80871f7f01f4a8c1f5174`.
It proves only packed addressing, shape derivation, storage behavior and
unchanged recurrent ABI correctness on the qualified 910B environment. It
does not prove normalization or gating correctness, endpoint speedup,
accuracy, cache-manager integration, or portability to untested Ascend stacks.

The copied CANN sources retain their original CANN Open Software License 2.0
headers. The torch adapter header retains its upstream Apache-2.0 header.

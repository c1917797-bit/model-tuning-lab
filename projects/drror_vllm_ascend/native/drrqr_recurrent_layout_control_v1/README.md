# DrrqrRecurrentLayoutControlV1

This is an independently named, opt-in DRRQR research control operator. Its
first purpose is to reproduce the frozen Ascend recurrent gated-delta-rule
arithmetic and mutable-state behavior exactly while giving the plugin an
auditable build and load boundary. It is not yet an optimization and is not
enabled by the vLLM plugin by default.

The implementation was mechanically derived from
`vllm-ascend/csrc/attention/recurrent_gated_delta_rule` at v0.23.0 commit
`5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`. The initial transformation only
renamed the GE op type, ACLNN symbols, kernel entry, filenames, namespaces and
header guards. `provenance.json` records the immutable upstream file hashes.

Acceptance for this control is deliberately strict: BF16 output and the full
mutable FP32 state must be finite and bitwise identical to the native operator
for the declared TP4 Dk64 eager and NPU-graph matrix. Passing that gate proves
only arithmetic/state ABI equivalence. It does not prove endpoint speedup,
accuracy, cache-manager integration, or portability to untested Ascend stacks.

The copied CANN sources retain their original CANN Open Software License 2.0
headers. The torch adapter header retains its upstream Apache-2.0 header.

# Qwen3.6 TP4 GDN decode mega-op: generation and ABI audit

Date: 2026-09-20  
Status: L0 contract and native NPU golden oracle verified; no candidate AscendC implementation or end-to-end performance result yet.

## Scope and fail-closed boundary

This workstream targets only the Qwen3.6-27B TP4, BF16, non-speculative decode path on Ascend 910B. Prefill, speculative decode, mixed prefill/decode batches, FP16 activation, other TP degrees, and changed head layouts must fall back to the current vLLM-Ascend chain.

The optimization target is the exact current decode chain:

1. transpose the static convolution weight;
2. mutable causal-convolution state update and SiLU;
3. packed Q/K/V split and contiguous materialization;
4. fused GDN gate and beta;
5. two FP32-accumulating L2 normalizations with epsilon 1e-6;
6. mutable FP32 recurrent gated-delta state update;
7. BF16 token output.

The operator is independently named and opt-in. It must not replace the upstream operators globally.

## CannBot generation provenance

CannBot repository commit:

- `d5e0d44b7a1d2e90c5f0b9fb62970fb3bac89ec3`

The initial skeleton was created by running:

```text
python3 ops/ops-spec-gen/scripts/generate_spec.py
  --op-name qwen36_gdn_decode_megaop
  --category FusedComposite
  --paradigms LayoutTransform,Reduction,SlidingWindow,Recurrence,Stateful,NumericalStable,FusedComposite
  --paradigm-groups fusion
  --axis-source fixed
  --inputs mixed_qkv:bfloat16;conv_weight:bfloat16;conv_bias:bfloat16;conv_state:bfloat16;a_log:float32;a:bfloat16;b:bfloat16;dt_bias:float32;recurrent_state:float32;actual_seq_lengths:int32;conv_cache_indices:int32;ssm_state_indices:int32
  --outputs output,conv_state_out,recurrent_state_out
  --chips Ascend910B
  --output-dir /opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-gdn-decode-megaop/operators/qwen36_gdn_decode_megaop
```

The generated defaults were not accepted as truth. They were replaced using the audited runtime ABI and formulas in `spec.yaml`.

Tool hashes:

| Artifact | SHA256 |
| --- | --- |
| `ops-spec-gen/scripts/generate_spec.py` | `c68214edf48166385a09060f20b862c4669ac71ad1169ed94b2292f645235467` |
| `ops-spec-gen/scripts/validate_spec.py` | `bdf9386e0543b25d5a367df737c76f02edf6c9d8fdb08026383b7a349e20140e` |

## Runtime source identity

The audited vLLM-Ascend tree is tag v0.23.0, commit:

- `5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`

| Source | SHA256 |
| --- | --- |
| Qwen3.6-27B `config.json` | `69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c` |
| `vllm_ascend/ops/gdn.py` | `d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816` |
| vLLM `qwen_gdn_linear_attn.py` | `885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0` |
| recurrent torch adapter | `96cf511bedd953c0b332bf97d88f535663c759fc81235baeb3044e66605d6a0c` |
| recurrent kernel entry | `74af73bbe19fef7f8163c953e2de0ee70df49ed3b76e7d2db1c8aab32af17c03` |
| causal-conv kernel entry | `3001e398478b3f532510b1b130e9ab2a97d9c12ec367437e49ed8f97fb7afb7b` |
| causal-conv update header | `1678810248bb470ac87769804ee8bd2b8682010184ae05b02d89b74f11e3f2ac` |
| causal-conv op definition | `8bb47bb6be57184a94d2d220194e96aad8d9b6e5c43ee531d94d24ebfe6b90b7` |

## Fixed TP4 ABI

- 64 transformer layers, with 48 GDN layers.
- local key heads: 4.
- local value heads: 12.
- key/value head dimension: 128.
- packed QKV width: `2 * 4 * 128 + 12 * 128 = 2560`.
- convolution kernel width: 4.
- convolution state: `[slots, 3, 2560]`, BF16.
- recurrent state: `[slots, 12, 128, 128]`, FP32.
- output: `[tokens, 12, 128]`, BF16.
- recurrent scale: `1 / sqrt(128)`.
- Q/K normalization epsilon: `1e-6`.

Both state tensors are mutable. The adapter must preserve storage identity and graph-visible mutation semantics.

## CannBot validation result

Validation was run in an isolated, CPU-only vLLM-Ascend v0.23.0 container with the CannBot and project trees mounted read-only.

Latest result:

| Stage | Result | Meaning |
| --- | --- | --- |
| 1 schema | PASS | schema closes |
| 2 semantic constraints | PASS | paradigms, errors, invariants and composition close |
| 3 shape closure | PASS | declared output shapes resolve |
| 4 dtype closure | PASS | BF16/FP32/int32 ABI resolves |
| 5 broadcast legality | FAIL | validator treats every heterogeneous top-level input as one broadcast group |
| 6 boundary coverage | PASS | required reduction/sliding/stateful/numerical cases are represented |
| 7 determinism | PASS | determinism contract closes |
| 8 NumPy formula smoke | PASS | executable formula runs on generated tensors |
| 9 oracle reachability | SKIP | no upstream single-call mega-op oracle exists |
| 10 formula/oracle equivalence | SKIP | same reason; NPU golden chain is the required oracle |
| 11 invariant execution | PASS | structural invariants accepted; value execution is not supported for these invariant kinds |

The Stage 5 failure is not waived as a pass. CannBot v1 Stage 5 currently assumes all non-index inputs participate in one broadcast contract. That assumption is false for a stateful fused operator containing weights, two state arenas, packed activation, gating vectors, and metadata. Changing the real shapes to satisfy this validator would falsify the ABI. Until CannBot supports per-primitive or per-input broadcast groups, this remains a documented tooling limitation.

## Required NPU gate before performance

The implementation cannot enter end-to-end benchmarking until a real Ascend test proves, over multiple decode steps and changed state indices:

- candidate output matches the current operator chain under declared BF16/FP32 tolerance;
- the full convolution and recurrent states match after each step;
- all outputs and states are finite for finite valid inputs;
- only addressed slots change;
- storage pointers remain stable;
- eager and graph replay both pass;
- invalid/mixed/speculative inputs fall back without invoking the custom operator.

Only after that gate may the monkeypatch be enabled for the fixed 1024-token performance protocol.

## Native reference result

The first half of the numerical gate is now complete: the unmodified v0.23
operator chain has a reproducible golden oracle on physical NPU4. The probe ran
batch 1 and batch 16 for eight changing-index decode steps in eager and
NPUGraph modes. All steps passed, eager and graph tensors were bitwise equal,
unselected slots and pointers were unchanged, and the independent formulation
matched with maximum output absolute error `9.5367431640625e-07` and maximum
FP32 recurrent-state absolute error `1.2959353625774384e-05`.

External evidence:

- report:
  `/cache/cch/qwen36-gdn-decode-megaop-20260920/native-golden-v1/report.json`
- report SHA256:
  `5df8a431b892cf82bc2be986cd4e6d7b62e06a69d558b86094e8c4822cddaf19`
- probe SHA256:
  `3d26f64a5855d1ef4c420d2c01ea2ff1da0cc3de39e234fb86c82156f390d794`
- vLLM-Ascend `gdn.py` SHA256:
  `d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816`

This does not satisfy the candidate half of the gate. The future direct-invoke
operator must pass the same output, complete-state, unselected-slot, pointer,
eager, and graph checks before any timing result is admissible.

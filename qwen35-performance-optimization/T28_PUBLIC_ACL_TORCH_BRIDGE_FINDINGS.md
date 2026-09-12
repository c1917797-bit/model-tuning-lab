# T28 public ACL / PyTorch bridge findings

## Decision

`BRIDGE AND ZERO-COPY LAYOUT GATES PASS; TP4 SERVICE GATE OPEN`.

The first bridge failed because it referenced a private, non-exported
vLLM-Ascend `NPUBridge` symbol. T28 removes that dependency entirely. The new
bridge builds tensor descriptors with public `aclCreateTensor`, submits the
pinned upstream `aclnnSwigluGatedMlp` ABI through torch-npu's `RunOpApiV2`
task-queue seam on the public current stream,
and registers both `PrivateUse1` and `Meta` kernels as a traceable
`torch.ops.qwen35_t21.swiglu_gated_mlp` node. It contains no replacement
matmul, SwiGLU, or collective implementation.

The bridge was built offline in the unchanged official vLLM-Ascend v0.23.0
image with no network and no NPU mapping. Its undefined-symbol audit contains
neither private bridge nor private storage symbols. The pinned build is:

- artifact: `/cache/austinov/qwen35-t21-public-acl-bridge-20260912-v3`;
- bridge SHA-256:
  `36bf053fd6511ac8a050dd30e08ee99396a76738afcc74fe3788fdc1f001e58a`;
- build runner: `scripts/build_qwen35_t21_public_acl_bridge.sh`.

The official-image device-free registration test passes: importing the
extension installs the torch operator, the Qwen2MoeMLP monkeypatch installs,
and the Meta kernel returns the expected `[M, 5120]` shape without a device.

## Zero-copy layout gate

The Qwen3.5 checkpoint keeps local TP4 weights in vLLM linear layout:

- gate/up: `[8704, 5120]`;
- down: `[5120, 4352]`.

The upstream fused operator consumes `[5120, 8704]` and `[4352, 5120]`.
T28 passes zero-copy `.t()` views with strides `[1, 5120]` and `[1, 4352]`
through public ACL descriptors; it does not allocate persistent transposed
weight copies.

The first torch-operator bridge exposed an intermittent NaN because a direct
ACL execute bypassed torch-npu's enabled host task queue. The v3 bridge now
uses `RunOpApiV2` and captures tensors, workspace, executor, and ACL
descriptors until the queued call is consumed.

On physical NPU0, three fresh runs of M=1/5/8/16 across seeds 1/2/3/4/5
passed 20/20 each. The zero-copy view and contiguous-copy candidate outputs
were bit-exact in every case. The
largest difference from the official torch Matmul -> npu_swiglu -> Matmul
reference was `7.62939453125e-06` maximum absolute error and approximately
`4.68966e-04` relative L2. Each completed run also passed 500 repeated M=1
calls with a finite checksum. Evidence:
`/cache/austinov/qwen35-t21-public-bridge-numerical-20260912-v4`,
`/cache/austinov/qwen35-t21-public-bridge-numerical-20260912-v5`, and
`/cache/austinov/qwen35-t21-public-bridge-numerical-20260912-v7`.

## Qwen3.5-specific project delta

The opt-in runtime hook is deliberately narrower than the upstream operator:

- exact Qwen3.5-27B BF16 TP4 shapes only;
- unquantized weights only;
- M in `[1, 16]` only;
- zero-offset contiguous model weights converted to zero-copy views;
- upstream local fused MLP result composed with vLLM's existing
  `tensor_model_parallel_all_reduce`;
- all ineligible shapes and modes use the unchanged official forward path;
- missing bridge or ABI incompatibility fails startup when the feature is
  enabled;
- `QWEN35_ASCEND_T21_DENSE_MLP=0` is immediate rollback.

This is the independently measurable project delta on top of upstream reuse:
model-specific admission, zero-copy layout/lifecycle integration, traceable
registration, and correct existing-collective composition. It is not a
locally rewritten kernel.

## Remaining gates

Before promotion, start the TP4 `candidate-prefill-t21` service, prove
four-rank activation and natural
EOS, then run official control vs bounded-prefill base vs bounded-prefill+T21
ablation. Only a passing fail-fast result may enter the c1/c5/c8/c16 x3 and
full quality gates.

# Scaling SSMs with Tensor Parallelism: Ascend Piercing Report

## Decision

**Rejected for the current Qwen3.6-27B + Ascend + vLLM-Ascend v0.23 target.**

No candidate was promoted to end-to-end performance or accuracy testing. The
applicability gate found that the current stack already implements the paper's
main SSM-aware TP mechanisms, while the only remaining paper mechanism does not
reduce bytes for the live dtype and cannot reach the required 10% end-to-end
gain under the measured communication ceiling.

This decision is scoped to the current target. It does not reject the paper for
an SSM runtime that lacks TP-aware channel sharding or recurrent-state caching.

## Paper mechanism and evidence boundary

The paper proposes four components for Mamba-style SSM inference:

1. persist convolution history and recurrent state between prefill and decode;
2. channel-wise sharding so convolution and recurrent updates remain local;
3. TP-aware unpacking/placement of packed SSM parameters;
4. quantize remaining AllReduce payloads from FP32 to FP16.

The authors state that the implementation will be released upon acceptance.
No official maintained implementation was available during this piercing, so
the mechanism contract comes from arXiv:2602.21144v1 rather than a code port.
The reported multi-GPU gains are primarily relative to single-GPU inference,
not relative to an already-optimized TP4 Qwen GDN baseline.

## Mapping to the current implementation

The exact vLLM source at commit
`0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665` already:

- calculates recurrent and convolution cache shapes using `tp_size`;
- uses `MergedColumnParallelLinear` for packed Q/K/V/Z and B/A projections;
- shards Q/K/V heads, A-log, dt-bias, convolution weights, and states by TP rank;
- runs convolution and recurrent GDN operations on rank-local contiguous
  tensors; and
- uses a `RowParallelLinear(input_is_parallel=True)` output projection, which
  places aggregation at the block boundary.

The exact vLLM-Ascend source at commit
`5cb98caaadeff42b5b62b996e34bb2aaa29d20fd` consumes those local shards in the
native causal-convolution and recurrent-gated-delta-rule paths. It does not
reconstruct full Q/K/V or recurrent state inside the GDN critical path.

Source identities:

- Qwen GDN TP implementation SHA256:
  `885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0`
- Ascend GDN implementation SHA256:
  `d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816`

## Live NPU evidence

On 2026-09-20, a Qwen3.6-27B service ran on physical NPU4-7 with TP4 in the
v0.23 image. The saved container inspection maps physical devices 4, 5, 6, 7
to container devices 0, 1, 2, 3. Its live engine configuration records:

- `dtype=torch.bfloat16`;
- `tensor_parallel_size=4`;
- HCCL backend with four ranks;
- about 12.8735 GiB of model weights loaded per rank; and
- local recurrent GDN implementation selected for the model.

This is target-device evidence, not a CPU inference proxy.

The reusable NPU profile at
`/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/prefill-mc2-mixed-v1/profile-current-v1/profile-comparison.v1.json`
has SHA256
`9cca1cd11a9eecd12c6e45988505d767c92ac6aa41fe3a857445a50d5b64115b`.
It used the same TP4 Ascend GDN family and records 30 decode steps at
concurrency 16:

- decode kernel envelope: 1388.008835 ms;
- communication without compute: 65.0222 ms;
- rank-mean summed `hcom_allReduce_`: 122.24209 ms.

The critical-path communication ceiling is therefore only
`1388.008835 / (1388.008835 - 65.0222) - 1 = 4.9148%` even under the impossible
assumption that all non-overlapped communication becomes free. The summed HCCL
kernel time is not additive critical-path attribution; even misusing that more
optimistic number gives only about 9.66%.

## Why no candidate run was launched

The paper quantizes FP32 AllReduce payloads to FP16. The live Qwen3.6 service
already communicates BF16 activations, which occupy the same two bytes per
element as FP16. A BF16-to-FP16 cast therefore adds conversion work without a
bandwidth reduction. INT8 communication would be a different algorithm with a
new numerical contract and accuracy risk, not a faithful implementation of the
paper's evaluated mechanism.

Because the implemented mechanisms have no missing delta and the measured
critical-path ceiling is below the 10% acceptance target, launching a paired
1024-token E2E benchmark would not test a supported hypothesis. Per the one-day
paper budget, the correct action is to preserve this no-go and move to the next
ranked paper.

## Re-entry conditions

Re-open this line only if at least one of the following becomes true:

- a target SSM/GDN runtime is found that lacks channel-local TP or local state
  caching;
- profiling shows more than 10% removable non-overlapped TP communication in
  the matched Qwen3.6 workload;
- a correctness-preserving lower-than-16-bit HCCL collective becomes available
  with a full-model accuracy contract; or
- the paper publishes code with a mechanism materially different from the
  v1 description audited here.

# DeltaLog mechanism-to-Ascend audit

Date: 2026-09-20

## Published mechanism

DeltaLog represents the logical recurrent state as a dense base, cumulative
decay, and bounded compact update log. For GDN the selected paper
configuration is M=8, FP32 dense state, BF16 key log, FP32 value-side update
log, and FP32 scalar decay metadata. Append reads the base and live log but
does not write the dense base; merge periodically materializes the represented
state and clears the auxiliary representation.

The paper reports tolerance equivalence rather than bitwise equivalence because
it changes accumulation order. Its published GDN bounds are maximum output
relative error 0.00303 and materialized-state relative error 7.92e-7 over
128-token rollouts. Those values are frozen here before implementation.

## Current Ascend seam

The v0.23 Qwen3.6 path normalizes Q/K, then invokes the custom AscendC
`RecurrentGatedDeltaRule`. The kernel reads each addressed FP32 state tile,
computes the delta-rule transition and output, and unconditionally writes each
updated tile through `CopyOutState`. This directly matches the eager
materialization tax described by the paper.

An Ascend port requires more than replacing one function:

- persistent per-layer/per-slot K, U, decay, and length buffers;
- reset on prefill initialization and slot reuse;
- append and merge semantics inside a graph-compatible static ABI;
- complete-state comparison at every merge boundary;
- fail-closed fallback for prefill, mixed, speculative, non-TP4, and
  unsupported dtype/layout paths.

## Source fidelity boundary

No official implementation repository is linked from the arXiv record, and the
initial primary-source search found none. The implementation must therefore be
described as a paper-equation reimplementation. It may not claim code identity
with the authors' Triton prototype.

## Decision boundary

The prior 4.68675% aggregated recurrent-kernel share is not by itself a
critical-path impossibility proof. Conversely, the paper's 1.08-1.20x H200
results at batch 64-256 cannot be transferred to Ascend concurrency 16. A
candidate earns one service screen only after the 128-step real-NPU gate.

## Real-NPU equation evidence

The first formula draft incorrectly formed the delta prediction from the state
before applying the current token's decay. Auditing against the v0.23 AscendC
instruction order exposed and corrected that error before kernel generation.

The corrected paper-equation implementation passed 128 steps for batch 1 and
16 on physical NPU4 against the deployed native recurrent operator. Maximum
normalized output error was 0.002890173410404624 and maximum merge-state
relative-L2 was 1.2238606976906924e-7, both within the predeclared published
bounds. This validates the equations only. The generic torch/NPU reference
materializes temporary logical state and is explicitly excluded from any
performance claim.

The first direct AscendC append exposed a separate hardware ABI constraint.
Four-byte scalar metadata fields for adjacent heads cannot be independently
updated from separate AIV cores when they share an effective GM write block.
Payload logs were correct, but scalar stores clobbered neighbors. A 32-byte
per-head stride still lost exactly one value in every adjacent head pair, so
the deployed stack requires at least 64-byte isolation. The portable v3 layout
therefore gives every head a 16-element/64-byte metadata row. This is an
Ascend storage adaptation; it does not change DeltaLog's logical recurrence.

With that adaptation, the direct AscendC candidate passed both eager and
NPUGraph replay on physical NPU4 for batch 1 and 16, 128 stateful steps each.
The worst output normalized error was 0.002857142857142857 and the worst state
relative-L2 was 1.3068015839486349e-7, within the frozen paper-derived limits.
Append preserved the dense base, all head metadata agreed, and storage
pointers stayed fixed. This proves the operator and graph boundary only;
service dispatch and end-to-end benefit remain unproven.

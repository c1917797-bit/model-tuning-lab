# Qwen3.6 DeltaLog on Ascend

## Status

- Stage: paper equations passed a 128-step real-NPU gate; AscendC candidate pending.
- Branch: `work/qwen36-deltalog-20260920`.
- Parent checkpoint: GDN fusion no-go `69029e7`.
- Hardware lane: physical NPU4-7 only.
- Delivery: independent explicit opt-in vLLM-Ascend plugin/monkeypatch.

## Paper fidelity

Paper: *DeltaLog: Deferred Materialization of Recurrent States for Linear
Attention Decoding*, arXiv:2608.15533v1.

The paper keeps one dense FP32 base state plus a bounded log of compact updates.
For GDN it uses merge interval M=8, BF16 key log, FP32 value-side update log,
and FP32 decay metadata. Seven append steps leave the dense base unchanged;
the eighth step merges the logical state into the base and clears the log.

The arXiv record and paper do not link an official source repository. This
workstream is therefore a clean reimplementation from the published equations,
operator table, and system invariants, not a claim of source-identical porting.

## Verified current-stack seam

The deployed v0.23 path calls
`torch.ops._C_ascend.npu_recurrent_gated_delta_rule` after native Q/K
normalization. Its AscendC kernel:

1. reads the complete FP32 state tile;
2. applies decay and the delta-rule update;
3. computes the output;
4. calls `CopyOutState` for every value tile at every decode step.

This is the eager dense write-back that DeltaLog targets. The layer already
receives slot indices and prefill writes the initial dense state, so an
explicit plugin can own per-layer log buffers and reset them for prefill slot
assignments without changing upstream sources.

## Why the old opportunity no-go is not sufficient

The portfolio recorded the recurrent operator as 4.68675% of aggregated decode
kernel time. That is useful caution but not a critical-path proof: DeltaLog
changes HBM write traffic, graph phase, and state representation, and kernel
time aggregates may overlap. The paper also reports that its benefit grows
with batch and state size. The current acceptance workload is concurrency 16,
well below the paper's 64-256 service evaluation, so one bounded real-NPU
screen is required after correctness rather than assuming either success or
failure.

## Candidate A

- M=8, capacity C=7.
- Dense base: FP32 `[slots, 12, 128, 128]` per TP rank/layer.
- Key log: BF16 `[slots, 12, 7, 128]`; repeated key heads may be optimized
  only after the faithful layout passes.
- U log: FP32 `[slots, 12, 7, 128]`.
- Decay snapshots and cumulative decay: FP32 scalar per slot/value head.
- Log length: int32 per slot.
- One statically shaped operator handles append and merge by device metadata so
  graph signatures do not depend on host-side phase decisions.
- Prefill and unsupported/mixed/speculative paths fall back to native and reset
  only their addressed auxiliary slots.

## Gates

1. Direct operator probe on physical NPU4: batch 1 and 16, at least 128
   stateful steps, multiple merge cycles, changed slot indices.
2. Compare every output to native dense recurrence. At merge boundaries compare
   the full materialized base state; verify untouched slots and all auxiliary
   metadata.
3. Fail on non-finite values. Predeclared paper-derived limits are maximum GDN
   output relative error 0.00303 and merge-state relative error 7.92e-7; report
   absolute errors as well and do not relax after observing results.
4. Eager and NPUGraph paths must both pass; storage pointers and graph-visible
   state mutation must remain stable.
5. Before service A/B, prove real candidate dispatch on all four TP ranks and
   record the actual library hash.
6. Run one profiler-off fixed-output-1024 screen against the frozen same-stack
   dense baseline. Report throughput, TTFT, and TPOT. If it is not plausibly
   on track for +10%, close the implementation-scoped no-go and move on.
7. Run LongBench-v2 and GSM8K only for a performance-positive candidate.

## Completed equation gate

The CannBot-generated skeleton was replaced by an audited M=8 contract. During
mapping to the native kernel order, the initial draft was corrected so that
prediction uses the state after applying the current `exp(g)` decay. The
formula then passed CannBot stages 1/2/3/4/6/7 and NumPy formula stage 8.
Stage 5 is a documented tool limitation: it attempts to broadcast every input
of a heterogeneous fused/stateful ABI against every other input. The contract
keeps the real shapes instead of falsifying them for validator success.

The one-shot equation gate ran on container logical NPU0 mapped to physical
NPU4 and compared generic NPU DeltaLog equations against the deployed native
recurrent operator:

- batch 1: 128/128 steps passed; maximum normalized output error
  `0.002369668246445498`; 16 merge observations;
- batch 16: 128/128 steps passed; maximum normalized output error
  `0.002890173410404624`; 52 merge observations;
- maximum merge-state relative-L2 was `1.2238606976906924e-7`;
- frozen limits remained output `0.00303` and state relative-L2 `7.92e-7`.

Report:
`/cache/cch/qwen36-deltalog-20260920/equation-gate-v1/report.json`, SHA256
`ad17ac193a472028850c69cc4eddda15bf4acb924b8695261a8c626dd4a92608`.
This is real-NPU algorithm evidence, not kernel, graph, service, or performance
evidence. Its generic `index_copy` state updates deliberately do not claim the
paper's deferred-write performance behavior.

## Immediate next action

Implement the independently named direct-invoke AscendC append/merge operator.
Its append path must not write the dense base, its eighth step must materialize
and reset on device, and it must next pass eager plus NPUGraph state/queue
ordering before any service integration.

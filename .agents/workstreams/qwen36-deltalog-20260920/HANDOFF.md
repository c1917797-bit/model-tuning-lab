# Qwen3.6 DeltaLog on Ascend

## Status

- Stage: paper equations and v3 AscendC eager/NPUGraph numerical gates passed;
  service integration is next.
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
the eighth step merges the logical state into the base and resets the live log
length. Payload bytes need not be physically zeroed once they are invisible.

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

Integrate v3 behind the explicit service opt-in. Allocate persistent
per-layer/per-slot auxiliary buffers, reset the addressed slots on prefill and
slot reuse, and fail closed to the native path for unsupported modes. Before
performance measurement, prove the real candidate library and dispatch on all
four TP ranks. Then run one profiler-off fixed-output-1024 screen against the
frozen dense baseline; no accuracy run is justified until that screen is
performance-positive.

## AscendC implementation status

Direct-invoke v1 compiled and reached physical NPU4. Its first append produced
an output bitwise equal to native and left the dense base unchanged, but the
state gate failed: only some per-head scalar metadata writes survived. K/U log
payloads for all 12 heads were present. The preserved failure is
`candidate-eager-gate-v1/report.json`; the diagnostic is
`candidate-eager-diag-v1/report.json`.

Root cause is an Ascend storage-layout hazard, not a paper equation error:
independent AIV cores wrote different 4-byte metadata values inside the same
32-byte GM block, so scalar `SetValue` operations clobbered neighboring heads.
Candidate v2 padded lambda/decay/length metadata to an eight-element, 32-byte
stride per head and compiled successfully. After stopping (not deleting) the
all-device `agentgpu-910b4-qwen35-4b-v0` sleep-only container, UDA released and
the physical-NPU4 canary passed. The one-shot v2 gate then failed at batch1
step1: output error was exactly zero and all K/U payloads were present, but
state relative-L2 was `0.5446365983176608`; exactly one length value survived
in each adjacent pair of heads. This proves the deployed scalar GM write
granule is at least 64 bytes. Candidate v3 therefore uses a 16-element/64-byte
row per head. Do not rerun v2.

Built v2 library:
`/cache/cch/qwen36-deltalog-20260920/operator-build-v2/libqwen36_gdn_deltalog_decode_ops.so`,
SHA256 `232901f7866c2a2262857d0a20616647a9e4bfe466454285bd4a1d0647a1105c`.

## AscendC v3 numerical gate

The v3 library is
`/cache/cch/qwen36-deltalog-20260920/operator-build-v3/libqwen36_gdn_deltalog_decode_ops.so`,
SHA256 `142ffd6833a34dc6ce975340250a9dcc397950a555e65202ed8de25e03ed75dc`.

The one-shot eager gate on physical NPU4 passed batch 1 and 16 for 128/128
stateful steps each. Maximum normalized output error was
`0.0014792899408284023`; maximum state relative-L2 was
`1.27864878159613e-7`. Report SHA256:
`0500932ac8f9496a3884a538ce458beae4a4f52f6cb8557919fae3738f9b1124`.

The independently captured NPUGraph replay gate also passed batch 1 and 16 for
128/128 steps each, including 68 merge observations. Maximum normalized output
error was `0.002857142857142857`; maximum state relative-L2 was
`1.3068015839486349e-7`. All steps were finite, append left the dense base
unchanged, head metadata agreed, and storage pointers remained stable. Report:
`/cache/cch/qwen36-deltalog-20260920/candidate-npugraph-gate-v3/report.json`,
SHA256 `9566a53eda33f60ce0163d3c6cfa4383ecb0f934332d08a631c075914169471d`.

These are direct-operator numerical and graph-compatibility results, not
service-dispatch, throughput, TTFT/TPOT, or task-accuracy evidence.

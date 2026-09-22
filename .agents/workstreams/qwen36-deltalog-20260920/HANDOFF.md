# Qwen3.6 DeltaLog on Ascend

## Status

- Stage: v4c paper-equation implementation passed eager, synchronized NPUGraph,
  TP4 dispatch, and fixed-output validity, but failed the end-to-end performance
  gate; current implementation is rejected.
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

## v4c memory correction and final numerical gate

The first full-size service attempt OOMed during native prefill because the
auxiliary key log repeated each of four local key heads across all twelve value
heads. v4c stores one BF16 key-log row per key head and expands the fixed 3:1
mapping only for fallback materialization. Per-layer auxiliary storage fell
from 30,401,280 to 23,878,400 bytes, saving 6,522,880 bytes per layer and
about 298.6 MiB across 48 layers on each TP worker.

The v4c library SHA256 is
a3698261d9e6de185b49aba5dd5aee1dc676cbb457e3e172aec826475bb57513.
Its eager 128-step batch-1/batch-16 gate passed. An initial NPUGraph run showed
a late state mismatch while output remained in tolerance; audit proved the
probe copied changing static inputs on the current stream and immediately
replayed the captured graph without a visibility barrier. The unchanged binary
passed after adding torch.npu.synchronize() before replay. The synchronized
report SHA256 is
ee4faf38fb600d2864288de95d5ce009ce50213774b1be5f5a298d28360008e7.
This is a harness correction, not a relaxed numerical threshold.

## End-to-end result and decision

The profiler-off TP4 screen used physical NPU4-7, 40 requests, concurrency 16,
32768 input tokens, 16384 shared-prefix tokens, and exactly 1024 output tokens
per request. All 40 requests completed and all 40960 expected output tokens
were produced.

| Metric | frozen dense | DeltaLog v4c | v4c vs dense |
| --- | ---: | ---: | ---: |
| output throughput (tok/s) | 125.819134 | 112.424603 | -10.646% |
| mean TTFT (ms) | 38,456.890 | 159,935.195 | +315.888% |
| weighted TPOT (ms) | 73.628823 | 99.825471 | +35.581% |

The service audit recorded 2130 per-layer/rank live-log materializations, all
caused by not_pure_decode mixed prefill/decode batches. The fallback uses
Python einsum plus index_copy_ over every active logical state before calling
the native mixed path. This is a concrete integration overhead that can erase
deferred-write savings; it is not evidence against the paper's reported
batch-64-to-256 regime. Even the candidate's first 16 requests showed
112.220 ms mean derived TPOT, so the negative result is not explained only by
later queued requests.

Performance report:
/cache/cch/qwen36-deltalog-20260920/performance-screen-v1/performance.v4c.run1.json,
SHA256
1233643e7dc6695251a88ac48edd0d928f1ed17c648d108976cd8e2ba8ec3da7.

Decision: reject this v0.23 TP4 M=8 implementation at concurrency 16. Do not
run LongBench-v2 or GSM8K for a performance-negative candidate. Reopen only if
a future workload justifies the paper's higher serving batches and a distinct
device-side mixed-batch materialization path is designed. Do not rerun v4c
unchanged.

## Immediate next action

Checkpoint and push the scoped negative result, stop the owned DeltaLog service
without deleting its evidence, and open the next ranked Paper-to-Ascend loop.

The owned service container was subsequently stopped without deletion. Fresh
device evidence showed no processes and baseline HBM on physical NPU4-7.
Commit 5f6fda3 contains the implementation, result, and reusable skill lesson;
its push remains pending because the remote-egress safety review requires
explicit approval for this exact repository payload.

## 2026-09-22 targeted Ascend adaptation follow-on (unverified)

The user explicitly requested HYPIC-style, mechanism-preserving Ascend
adaptation rather than treating a direct port's failure as a paper-level
failure. The v4c service audit gives a concrete removable bottleneck: 2130
mixed-batch fallbacks invoked host-synchronized all-slot materialization.

Plugin v0.2.1 now has a narrower first attempt: when the native v0.23 path
receives a non-spec mixed prefill/decode batch, it materializes only that
batch's decode and prefill state slots. It removes the per-layer
`torch.any(...).item()` and `torch.nonzero()` host synchronization from this
mixed path. The native mixed core remains unchanged, and pure decode retains
the previously validated DeltaLog operator. This is an implementation
hypothesis, not a correctness or speed result.

The subsequent v0.2.2 preparatory change leaves K/U/λ payloads untouched
after materialization and clears only length/decay metadata, because zero
length makes the old payload invisible and the next append overwrites its
entry before use. A dead-entry exponent is masked before `exp` so stale
lambda values cannot create `0 * Inf -> NaN`. The bridge probe checks the
metadata/payload invariant explicitly.
Neither v0.2.1 nor v0.2.2 has a passing NPU bridge gate.

The new `deltalog_mixed_fallback_npu_probe.py` checks the bridge on physical
NPU4, batch 1/16, eager and synchronized NPUGraph, selected state against the
logical/native reference, untouched slots, zeroed selected length/decay,
unchanged selected K/U/lambda payload,
stable pointers, and the following native decode output. The script and
plugin passed syntax and `git diff --check`; Maintainer Skill Tree validation
passed (20 skills).
The next probe revision also poisons dead lambda entries with `-1000` before
the bridge, so the new pre-exponent mask must prevent `0 * Inf -> NaN` in
eager and graph replay. This revision is not yet NPU-validated.

The first isolated probe container
`qwen36_deltalog_mixed_selected_gate_v1` did not reach a tensor operation:
`aclInit` returned 507899 / `Resource_Busy`. Preserve this exited container
and its logs; the output directory was not created. Fresh host `npu-smi`
showed no NPU4-7 process and baseline HBM. Two unrelated Qwen3.5-4B
containers (`agentgpu-910b4-qwen35-4b-aiv-v1` and
`agentgpu-910b4-qwen35-4b-v0`) each declare physical 0-7 while `docker top`
shows only `sleep infinity`. Their declarations may be related to the UDA
failure. The host kernel log confirms `uda_occupy_dev_by_ns` conflict on
physical device 4 during the failed probe, but does not by itself identify
which container owns the namespace. Host Python has no torch/torch_npu, so
there is no same-stack host-side probe shortcut. Because stopping either could
affect someone's 0-3 environment, seek an exact decision before stopping them.
On 2026-09-22, an exact `docker stop --time 10` request for only
`agentgpu-910b4-qwen35-4b-v0` was rejected by the safety reviewer due to its
external ownership and declared 0-3 mapping. No container was stopped and no
alternative command was used. Wait for explicit approval or external release;
do not treat the user's statement that 4-7 are computationally idle as proof
that stopping a shared 0-7 container is authorized.

The user subsequently gave exact approval for `v0`. Fresh checks showed only
`sleep infinity`, and only that container was stopped without deletion. It
exited 137 after Docker's 10-second stop grace. The new nonprivileged canary
`qwen36_deltalog_npu4_uda_canary_v2` mapped only physical 4 to logical 0 and
still failed at `aclInit` 507899 before any candidate tensor operation; the
kernel again logged `uda_occupy_dev_by_ns` conflict for `udevid=4`. Preserve
the exited canary and logs. This rules out `v0` as the sole blocker; it does
not prove which remaining namespace holder is responsible. The `aiv-v1`
container remains running with only `sleep infinity`, but stopping it requires
its own explicit authorization. Do not rerun the unchanged canary or treat
this infrastructure failure as DeltaLog numerical evidence.

Do not rerun the same container unchanged. After a resource-state change,
re-prove NPU4-7 ownership, device mapping, and a fresh non-overwriting output
directory; then run one bridge gate. If eager/graph correctness passes, measure
mixed-batch fallback count and run a paired profiler-off 1024-output E2E
screen before any LongBench-v2/GSM8K spend. If selected-slot materialization
remains expensive, consider an independently named device-side materialize
operator using the reviewed CannBot spec/direct-invoke process; do not claim
it already exists.

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

## TP4 service integration gate

The explicit opt-in plugin was loaded by the API server, engine process, and
all four TP workers on physical NPU4-7. It pinned the deployed GDN source and
v3 candidate-library hashes, allocated persistent per-layer/per-slot auxiliary
buffers, and dispatched the candidate on all 48 GDN layers in every worker
(PIDs 124-127). Unsupported/profile paths used the native fallback and
materialized live auxiliary state before fallback.

A one-token request returned HTTP 200 in 0.638 seconds with output ` Paris`.
A four-token request returned HTTP 200 in 0.560 seconds with four completion
tokens, proving multi-step service state progression. An earlier 16-token
client was terminated by the remote execution layer at its 30-second boundary;
the service remained healthy and later requests passed, so that attempt is
retained as a harness-timeout event, not a candidate failure or performance
result.

Artifacts:

- `/cache/cch/qwen36-deltalog-20260920/service-candidate-v1/audit.jsonl`,
  SHA256 `dbf792ec90bc153445577c93761a810787f5ed3f0752f7d8a0b63d727f4ee080`;
- `first-token-response.json`, SHA256
  `7dd75ef1d5b3bda452e9ae00a6ec2cafd1d5aab00ed7bf24a3020a9186cd3f54`;
- `four-token-response.json`, SHA256
  `b4b984f4f72ba23b151c7a2d946c57a313d5a60b437af02c21b6af57ee70795b`.

This gate proves real service dispatch and short inference only. It is not a
fixed-output performance result and makes no LongBench-v2/GSM8K claim.

# H8 full-v7: actual numerical failure, not paper-wide no-go

Recorded 2026-10-08 01:03Z. Canonical branch work/qwen36-damp-ascend-20261006.
DAMP remains closed; this is the distinct KVBuffer short-horizon H8 continuation.
Physical NPU4–7 only. No additional hugepage release: exactly32GiB authorization
was completed on Oct7; OVS24GiB and whole NUMA3 pool retained.

## Actual terminal authority

Original MA exec-00000000000010e2 ended FAILED, exit1, duration3,363,769ms;
not timed out/cancelled. Whole original is preserved in
H8_FULL_V7_FAILURE_ORIGINAL_20261008.json. Actual RESULT:
`/cache/cch/qwen36-paper-preparation-20261007/recurrent/MAIN-h8-full-runtime-v7-20261008-001/RESULT.json`
13,795,969B, SHA256 ee5418e8c9d07dd7d4b2b20e8ade132ed88ac308f704dcaf98065dfac4f896c8.

Primary: first real matrix child failure on physical7.
First numerical failure: B12, graph, trial2, step102, active12, no reset.
Original output_error=max(abs(actual-expected))/max(abs(expected)) =
0.0031645569620253164 > unchanged0.00303 gate.
Complete-state relative L2=1.2153881810212567e-7; per-head maximum
1.6407555190996168e-7, both below unchanged2e-6.
Finite/guards/pointers/input immutability/untouched slots/nonflush base/log
checks passed. Twelve native expected rows were defined, zero padding rows.
This is NOT the older RSS-observer ProcessLookupError or padding failure.
The human's 1% end-to-end task-loss allowance does not relax this tensor gate.

Retained unanalysed CPU tensor evidence:
`/cache/cch/qwen36-paper-preparation-20261007/recurrent/MAIN-h8-full-runtime-v7-20261008-001/physical-7/gate/raw-step-b12-graph-t2-step102.pt`
78,155,077B, SHA256 aef3c1127b29eb9b2be8a2d0b9548218e92723ac0389acdf0269d7b69924ec12,
independently physically hashed by MA1106. Includes pre/post state, native
pre/post, inputs, outputs, guards, pointers; do not overwrite/delete it.

Partial reports show31 completed matrix cases,5252 checked steps,1 failure.
They are NOT full11520/lifecycle PASS. Physical4–6 reports still say running
because writers were stopped early; actual process/cleanup authority establishes
they are terminally stopped, not ongoing jobs.

## Separate secondary and observer failures

Stable post-cleanup snapshot recorded MemoryError, secondary to the numerical
failure. RSS ledger peak242664KiB,97553 samples, no measurement errors or resource
violation. Soft host-Python VAS256MiB exists; this does not prove ordinary host
RAM exhaustion or imply another authorized hugepage release.
Direct MCP reads of a13.8MB result and5.3MB report failed the8MiB response-body
limit (response serializes duplicate content); bounded stdlib reads/streamed
hashes succeeded. Transport-size errors do not justify rerunning the NPU job.
One header diagnostic MA1107 failed on an accidental str call before stdout;
minimal fixed MA1108 exit0 preserved the primary report's original error.

## Actual release and immutable diagnostic authority

H8_FULL_V7_FAILURE_RELEASE_ORIGINAL_20261008.json is whole MA1106, exit0,
1904ms, 00:54:23Z. Small parsed values are in
H8_FULL_V7_FAILED_SMALL_AUDIT_20261008.json.
All four exact owned CIDs stopped/Pid0/noExec/noOOM, retained not deleted:
- fa1c3f5e6386e029a05982171a7763fb8eeb65958df40fb56ea44e66a8d1911c (4)
- c9192708e3499726711f8248aa05d02b6f2812fc53c25fd61f8ae0c2f0278a9d (5)
- 908e79f6a3ec312554df96b0690007052b52b5e0e4b4785449a4835d244de0d6 (6)
- b115c5b142335ef39d3eddd27d107ae3ba224c0bf6fb90f35d80989e266d4837 (7)

Cleanup5921B SHA256 b093b64696a11c9c2076edee4cfbe796d43b8f51032e62d808230b76fe63d67f,
errors[]; SMI no compute PIDs on4–7, baselineHBM2866/2865/2865/2860MiB.
Physical0–3 and external work were not mutated.

## Preparation only: no model/performance claim

Mixed-v3 actual independent MA10fe audited389 pinned sources; whole original
is H8_MIXED389_SOURCE_ONLY_ORIGINAL_20261008.json. Its prerequisite is actual
full-v7 success, now false; do not run this packet unchanged.

New default-OFF source-only client:
`projects/kvbuffer-parallel-ascend/tools/h8_service_client_v1/`.
Actual MA1104 exit0 passed16 software tests; original in
H8_SERVICE_CLIENT16_SOURCE_ONLY_ORIGINAL_20261008.json.
Pinned same-image completion source demonstrates echo=True plus token IDs
retains prompt identities after empty initial chunks. This was source inspection,
NOT a live API or model PASS. Client records raw SSE, exact token counts, DONE,
queue latency separately, TTFT/TPOT; fixed1024 output screening only.
No ARM producer/model controller/budget or TP4/model-graph validation yet.
No new full/mixed/model/matched-E2E/task-accuracy accepted result.

## Next admissible work and general lessons

### Independent failed-raw diagnosis, 2026-10-08

Whole MA110a exit0/330ms and MA110b exit0/537ms preserved in
H8_FAILED_RAW_STDLIB_ORIGINAL_20261008.json and
H8_FAILED_RAW_POINT_FP64_ORIGINAL_20261008.json. Both host stdlib only, no
Torch/Docker/NPU; streamed exact raw SHA then restricted pickle metadata and
little-endian FP32/BF16 storage reads. Original output metric reproduced exactly.
Eight of18432 BF16 elements differ; all eight are adjacent1-ULP outputs.
Worst[4,9,54]: candidate -0.006622314453125, native -0.00665283203125,
absDiff3.0517578125e-5, maxExpected0.0096435546875.

At that row(slot0, before log length7), FP64 single-step recurrence reconstructed
from actual native-before FP32 state gives -0.0066375734687490594;
from actual H8 logical-before gives -0.006637572787259737.
They straddle the BF16 midpoint -0.0066375732421875 by
-2.265615594437831e-10 and +4.5492776299532744e-10.
Post-native stored-state projection and H8 logical-post projection straddle it
as well. This supports investigation of accumulated FP32 state/reduction
rounding, not an established isolated BF16 cast defect. Some other differing
rows also show native output versus native-state FP64 projection rounding
differences. These are local reconstructions of retained states, not an
all-history FP64 golden or new NPU validation.

Original0.00303 gate remains FAILED. Do not promote a closer-to-oracle output,
relax its threshold, or repeat the full matrix without a source-supported repair.
Canonical local checkpoint a3283c01ae4cd17ab3163b662e6f9c4173e46932
contains the original failure/release and source-only16-test client; not pushed.

1. CPU-only, hash-bound read of failed raw; recompute original metrics, inspect
   worst output/rounding and independent FP64 single-step equations. Do not
   claim a BF16 rounding cause until evidence supports it.
2. If a source-level causal repair follows, preserve v7 negative and use a fresh
   opt-in successor/targeted failing-case NPU gate before wider matrix. Never
   lower the threshold or repeat unchanged deterministic failure.
3. MAIN admits the next frozen SparQ006 or W4native002 packet serially while
   preparers work without device access; future NPU checks must be fresh.
4. Source/software/import/CPU reconstruction cannot substitute for NPU,
   mechanism-complete plugin dispatch, matched E2E or task accuracy.
5. No kernel sum or single raw point proves paper-wide performance no-go.
6. Keep original failure, cleanup, and observer failures separate. Bounded
   streamed report observation should not hold large copied JSON trees.

KV deadline Oct8T08:29:54Z and portfolio deadline Oct9T11:17:31Z unchanged.
Three preparers active; MAIN alone Docker/Torch/NPU/canonical Git.
Normal local checkpoint under the known unchanged authentication blocker;
do not claim pushed or retry credentials/failed publication blindly.

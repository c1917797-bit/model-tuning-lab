# DAMP Ascend — current workstream

Activated 2026-10-06T08:48:03Z; hard deadline 2026-10-07T08:48:03Z.
Status: active DAMP plugin migration; no performance/accuracy result.

Latest 11:17Z checkpoint: read MIGRATION_PREP_RESULT.json. Actual operator v4
compiled/load/schema/Meta PASS is preserved, but restricted native NPU v2 is
FAILED: B1 identity closed-loop packed state was bitwise exact for44 steps;
step45 changed one INT8 code by1, state max-head relative1.3174993668816764e-4
exceeded frozen1e-5. Output, FP16 payload/scales, untouched slots and pointers
passed. Container stopped/retained. Fixture and independent CPU repack bind the
failure to a half-integer boundary. Actual saved-fixture trace v2 supersedes
that CPU FMA hypothesis: updated FP32 state is bitwise native, while vector
Div returned -117.49999237060547 rather than IEEE FP32 -117.5; RNE produced
-117 instead of -118. Target the quantizer division seam, never relax the gate.
General positive-FP32 SR and graph/service correctness remain unproven.

Collector v3 is terminal FAILED/stopped/retained: pure-text MRoPE passed, but
donor-only patching missed the actual Qwen receiver's copied function binding,
observed zero GDN hooks and failed exact48 coverage. A later nested-turn error
was secondary, not the root cause. Source/alias/actual-instance repair is now
in the plugin only. Collector v4 MA exec-0000000000000128 is terminal FAILED,
stopped/retained: both native off/on runs completed, but the original validator
compared external client IDs to internal worker IDs. MAIN's new source-bound
legacy audit MA exec-0000000000000151 passed TP4/all48 layers/anchors/futures
and exact nine-output-token parity. AUDIT.json SHA is
f51cd439a576f44159f2d849b812747838dddeaf445429751966b70d70c8000e.
Original failed validator/raw bytes are unchanged; this proves native collector
smoke only, not compressed recurrence, full calibration or E2E/quality.
New runs observe the original parent-engine add_request return on both arms.
The source-reviewed observer passed12 MAIN software tests. Full capture's native
off arm now has four live source-bound external/internal request identities;
this does not yet prove full capture validation or off/on output parity.

Actual diagnostic trace v1 compiled (MA0148) but failed before kernel launch
on physical4 (MA014f): default4D FP32 output was not physicalND. Original
production binary/state gate remain unchanged. The deployed public
npu_format_cast declaration/export was confirmed without devices (MA0153).
Only the two diagnostic outputs now use that conversion; keep check_tensor.
Trace build-v2 MA0154 and saved-fixture NPU trace MA015d completed PASS;
trace container is stopped/retained. report.json SHA
685e6cf1011d29a4c31f70b254c5192252e1a296717994246a1f5291093ad0b4.
This proves attribution for one immutable failed step only; the original
closed-loop numerical gate remains FAILED. All13 source-body checks pass;
raw report's source_gate_status scalar is stale, not rewritten.
Same-image calibration software19 tests passed (MA0149). Full TRAIN native
capture MA exec-0000000000000161 is RUNNING on physical4-7; poll that same
handle. Native off arm model load/warmup completed; MAIN observed TP worker
PIDs744181/744186/744190/744192 bound to physical4/5/6/7 (MA0179).
Container qwen36_damp_full_capture_tp4_20261006_v1, ID4505fd9eb29e4079768a2b0ea49f2bacd198f77023672bbc297c3c2aa86dd8ff.
36 TRAIN prompts x1024 inputs x4096 reference outputs, batch4, eager,
native off/on. Not formal timing or task evaluation. No full validation,
source lock or fitted plan has passed yet. Collector source remains frozen.
General-SR reference/gate preparation is not NPU proof.

Full TRAIN input builder v3 passed in the same immutable image with NO devices,
isolated pinned PyArrow, exactly36 rows x1024 IDs, fixed4096 reference output,
nine hash-verified TRAIN files and398 disjoint target/context records.
Full manifest file SHA f348e0b0404e2f3a619b986f5c1152427c52f1a3550386ee1f894eafa6986b33.
Five proven template-boundary gaps needed the next unused same-partition TRAIN
reference; no padding, target cuts, author-exact sample claim or eval leakage.
Input readiness is not model calibration. Parallel lanes are integration
real-receiver/media admission, source-bound device trace, and offline generalSR
selector preparation; main owns all NPU/Docker/Git actions.

The previous KIVI closeout and training-free preference were pushed normally
at e63df71 after GitHub HTTPS connectivity recovered. No force push or main
edit occurred. This existing clean target-host checkout is reused on a new
work branch; no ninth worktree is added and all older branches/checkouts are
preserved. Canonical repository remains /opt/host/vnf/austinov/model-tuning-lab.

Primary change: DAMP's offline decay-weighted mixed-precision recurrent-state
storage, not unrelated fusion, MTP, training or distillation. Source is
arXiv 2608.27513v2; no official code link has been verified. Equation-derived
port and project-chosen SR candidate grid must be labeled honestly. Reuse
native Ascend recurrence and existing plugin/operator scaffolds only where
semantics/ABI agree; independently named opt-in code fills the packed-state
update gap if it is proven to exist.

Native source/ABI/reuse audit completed. Nonprivileged physical4->logical0
canary passed. Packing v1 failed FP32 scale bitwise parity; FP16 and INT8
payloads passed. A separate diagnostic isolated1-ULP constant-division lowering.
Revision2 froze an explicit FP32 reciprocal multiply without relaxing gates
and passed packing plus lossless native covariance for batch1/16×160steps.
Full-state max relativeL2 was1.443e-7; max output relativeL2 was3.259e-4.
See STAGE_RESULT.json and PROBE_QA.md: this is NOT compressed recurrence,
graph, service, performance or quality acceptance. Owned gate container is
stopped and retained. Next live collector smoke, remaining quantizer QA and
the genuinely packed recurrent kernel. Collector Agent owns only collector/**;
operator Agent prepares a ready-to-apply source draft, no independent load.
NEXT_KVBUFFER.md preserves another paper's unmet parallel-fold hypothesis;
its preparation has not started its formal24h timer. SCHEDULING.md records
the active30-minute product heartbeat and parallel preparation rules.
Freeze full-precision reference trajectories before selecting any
precision mask. Numerical implementation parity uses the same quantization
algorithm as its oracle; quantized-vs-dense drift is a diagnostic, not the
maintainer's 1% task-accuracy tolerance. Require complete state, untouched
slots, changing inputs, multi-step and graph checks before performance.

The maintained goal remains >=10% fixed-1024 E2E output throughput gain,
TTFT/TPOT separately, and final non-thinking max_tokens=2048 normal-EOS
LongBench-v2/GSM8K. Latest explicit user permits up to 1% E2E task loss:
report both pp and relative loss and also audit the original no-loss target.

At orientation NPU4-7 had no compute PIDs, AICore0 and ~2653 MiB baseline
HBM (card4~2860 after prior gate, still no compute PID/AICore). One external
sleep-only container declares0-7; declaration alone is not
an obstacle. Recheck before every new load. Never stop it without an actual
mapped conflict and applicable narrow authorization. Current collector live
load/phase must be obtained freshly: v2/v3/v4 and trace-v1 are stopped/retained;
trace-build-v2 and saved trace-v2 are stopped/retained. Full-capture-v1 is
currently the owned real TP4 model load. Do not launch a second NPU job.

Artifacts: new non-overwriting /cache/cch/qwen36-damp-20261006 subdirectories;
raw tensors/weights/profiles stay outside Git. Stop and retain only owned
containers after runs. All operation handles must be polled, not relaunched
because an observation times out. Close the current route with scoped
accepted/rejected/failed/inconclusive evidence by its deadline.

## Latest maintainer deadline — 72-hour portfolio closeout

Human instruction observed 2026-10-06T11:17:31Z: finish the existing paper
queue within3 days and deliver at least one usable non-HYPIC technique.
Portfolio cutoff: 2026-10-09T11:17:31Z (14:17:31 Europe/Moscow).
DAMP's earlier individual deadline remains 2026-10-07T08:48:03Z.
Read THREE_DAY_CLOSEOUT.md and SCHEDULING.md. Parallel agents prepare/audit;
MAIN serializes all real NPU4-7 and matched TP4 measurements. A sample,
source/ABI pass or local kernel result does not meet the usable requirement.
No new formal accepted performance/accuracy result exists at this checkpoint.

## 11:33Z live resource and evidence reconciliation

Full-capture MA0161 remains running; native off first four TRAIN requests are
admitted, client rows not yet complete. No full source lock/fitted plan exists.
An external cannbench_ds evaluator genuinely used physical4 (PIDs748251 and
780561, 106+6662MiB), alongside our TP4. MAIN identified its exact device4
grouped_matmul_swiglu_quant launcher subtree. MA01c0 stopped only that subtree,
not the privileged all-device container, its watchers, or anything on0-3.
Original container/files/logs are retained. Four owned workers remain live;
postcheck shows only owned worker744181 on physical4 and HBM26092MiB.
External receipt /cache/cch/qwen36-damp-20261006/external-npu4-release-v1/receipt.json
SHA2569605aeca18e89063c03dbaba13feb46d168a88eb159a4c4f633acd0babc2dbc6.
First release precondition MA01b5 safely failed before signals/output creation:
the native process row combines NPU and Chip in one pipe column. Corrected
parser was checked against the actual snapshot before the bounded release.
Resource interference is recorded; reference capture is not formal timing.

Read PAPER_EVIDENCE_INVENTORY_20261006.md before quoting paper completion counts.
Audit found25 current IDs,3 historical IDs and8 missing archival conclusions.
Several entries are only applicability/diagnostic screens, not full migration.
MXR/GoodEnough old service-opportunity claims used Qwen3.8 profiling and must
not be treated as Qwen3.6 E2E rejection. Later DeltaLog/KVBuffer developed
negative screens supersede stale portfolio opportunity-only labels. No blanket
all-papers-no-benefit conclusion is valid. Parallel lanes now prepare exact
DAMP quantizer, independent mathematical review, and distinct KVBuffer FP32
parallel fold; MAIN alone executes NPU/Docker/Git. Current code/source hashes
used by the live collector must remain frozen across off/on arms.

Checkpoint scope: native collector/calibration, deployed v4 production and
trace source snapshots, existing integration preparation, raw-result summaries
and72h governance. Future reference/generalSR/quantizer drafts remain local,
excluded until MAIN review/build. The staged full whitespace check found only
trailing/extra-EOF whitespace in copied licenses and frozen source files;
retain this negative check and exact source bytes rather than silently changing
the sources bound to existing binaries. See SOURCE_CHECKPOINT.md. This is an
attempt/evidence checkpoint, not correctness, performance or quality acceptance.

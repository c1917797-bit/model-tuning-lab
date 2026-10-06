# DAMP Ascend — current workstream

Activated 2026-10-06T08:48:03Z; hard deadline 2026-10-07T08:48:03Z.
Status: active DAMP plugin migration; no performance/accuracy result.

Latest14:28Z stage overrides older live-status paragraphs below:
native full capture MA0161 is terminal FAILED/stopped/retained. Its off36/36
x4096 outputs completed; ordinary-RAM64GiB admission blocked on before start.
No actual OOM, fitted plans or full source-lock. Preserve off and only resume
missing on under source/config proof; do not repeat off. Protected0-3 now run
external HYPIC workers2058953/2058954/2058955/2058956; never touch them.

Actual NPU4 integer-certificate721cases/37negative and compaction49cases/
5negative passed. New production integer-compaction v3 compiled/exported,
load/Meta passed4positive/44negative calls, and saved-step45 full packed state/
BF16 output repaired bitwise with complete-state error0. Original v4 failure
unchanged; no numerical gate relaxed. Read
projects/damp-ascend/operator/production_integer_compaction_v1/ACTUAL_GATES.md.
The B1/B16 x two restricted variants x160steps matrix MA03c8 ended terminal0:
all640steps, all state/output errors0, full packed bitwise and guards passed.
Report47c6120134ba788ff3e4a40f949aba1de9ae052726745437482a0bcbc3a71444.
Independent reference actual no-device load/schema passed MA03da. General
NPU MA03e5 ended terminal0: six native/reference bitwise anchors and four
synthetic general-positive-FP32 candidate cases,160steps each, all passed;
reported complete/selected state/output errors0. ReportSHA
d4d71a45ae75c36a6ed9f5dc02c23272a1fef44e18f0a62226b4fcb3b35423d8.
NEW restricted graph/metadata MA040d started; poll it rather than relaunch.
Final192 calibrated plans, graph/cache/
service/paired timing/final quality remain missing. Zero new non-HYPIC final
joint-accepted candidates; DAMP and72h deadlines above remain unchanged.

Parallel NEW on-only recovery, KVBuffer service and AdaKV grouped service
drafts remain excluded from this checkpoint until MAIN full review and their
actual prerequisites. Source preparation/software tests are not device success.

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

## 12:08Z reviewed build and live checkpoint

MA027a freshly verified NPU4-7 contain only owned TP4 workers744181/744186/
744190/744192; protected0-3 have no compute PID. Native off client capture has
8/36 completed rows; on has not started. MA0161 remains RUNNING. This is TRAIN
trajectory collection, not a formal timing or task-accuracy result.

MAIN fully reviewed the frozen16-file isolated quantizer and independent
reference/gate. Quantizer NO-device ASC build actually exited0; library SHA
6819530a2ca5c9e11fef283e36090224170c3ac9566b15bd527a73c21dfee9d8.
Its C++ host test116015 pairs had0 mismatch; MA0267 actual load/schema/Meta
also exited0 with npu_executed=false. Never promote these to NPU correctness.
The first build-launch response had no structured route proof; MAIN did not
duplicate it. Later exact-container inspection and terminal receipt confirmed
the owned no-device build outcome. Production v4 remains unchanged/FAILED.

General-SR independent reference now uses public ND conversion for its4D FP32
eager allocation; native copied arithmetic remains source-bound and unchanged.
Raw after-state/output is retained before shape/format/finite/alias assertions,
with complete byte-interval and stable-pointer guards. An anchor-only mode
allows six native-reference cases without rerunning unchanged failed compression.
Initial software MA024a misplaced-test-loop NameError was repaired; the original
failure is not erased. Actual MA0262 native source contract,15 software tests and
ASC build all passed. Library SHA
853f655c45c11cb5de5a1b0810c9a8850c0b66aea4c9aa049e01ac89f1aeccc8.
Independent native NPU anchors are still pending, not yet general-SR acceptance.

Next: preserve live collector bytes, finish full source validation; only then
use newly inspected4-7 mapping for exact-bit quantizer and independent native
anchors. No parallel NPU microtest during TP4 capture. fast_integer_certificate
is a new uncompiled draft, excluded from this reviewed checkpoint, as is the
unreviewed KVBuffer parallel project. Its real CANN Broadcast temporary UB and
producer/consumer synchronization require review before device deployment.

Read SOURCE_GAP_AUDIT_20261006.md: seven ofeight previously unarchived source
titles were verified; OpenReview title remains unresolved. Applicability/source
screens are not eight completed migrations or eight negative service results.
No new non-HYPIC final performance/task acceptance exists. Portfolio cutoff
2026-10-09T11:17:31Z and DAMP cutoff2026-10-07T08:48:03Z remain fixed.

## 12:53Z actual build/load checkpoint and production seam review

MA02eb at12:43:43Z observed native off20/36 TRAIN client rows complete,
4096 outputs each; capture-on had not started. MA0161 is still RUNNING.
Only owned TP4 workers744181/744186/744190/744192 used physical4-7.
Protected0-3 now have an external HYPIC service; do not interfere. No competing
NPU probe is authorized while full capture lives. No full source validator,
source-lock/fitted192 plans, new formal throughput or task quality result exists.

KVBuffer parallel-fold P1 source was fully reviewed. MAIN MA02b0 actually
compiled its seven bound source files; library SHA
0e7c64b53314f1e822a27b5f373376d82d3f73c01264a384cf58ee4bc6e3477b.
MA02d4 actually loaded it, checked mutable schema/prepare registration, B1/B16
positive Meta and25 stdlib tests. All no-device, not NPU correctness.
Results: /cache/cch/qwen36-kvbuffer-parallel-20261006/build-p1-v1/ and
meta-p1-v1/. This is an equation-derived FP32 deferred parallel fold, not an
author-code claim or the already-negative serial implementation. P1 model
integration is eager-only; operator graph proof and full lifecycle/state160step
matrix remain unrun. Candidate119296 auxiliary bytes/layer/slot must fit the
common total memory budget; no persistent candidate-only FP32 shadow state.

DAMP integer-certificate probe v1 MA02be failed when its frozen device header
reached the host pass. V2 MA02dc compiled/linked successfully, actual SO SHA
4fd87e85a0ecf97b4613477f9d52517e80e90c3bb9931f378d5d37238ce21b53,
but MA02f1 no-device load FAILED: undefined
qwen36_damp_integer_certify_bits_kernel. Actual MA02f6/02f7 nm/readelf confirmed
U/UND in both the ASC object and SO. Keep build-v1/build-v2/meta-v1 and exact
source archives unchanged. Their source/compiler success is NOT registration
or NPU acceptance. V3 must keep the annotated kernel definition visible to
host while guarding only device includes/body; no parent2201 gate deletion.
Only MAIN runs the new nonoverwriting build, exported-symbol and load checks.

Read PRODUCTION_QUANTIZER_INTEGRATION_REVIEW.md (MAIN fully reviewed):
preserve raw low FP32 state, unchanged group32 scale/readout/DMA, vector
integer certificate and sparse exact fallback. Accepted lanes must not incur
the diagnostic probe's all-lane scalar scan. A separate packed-mask/GatherMask
count/order/guard/scatter seam is being prepared, not yet compiled/NPU proven.
N448 UB sums are a cautious design, not a measured allocator or speed pass.
Original v4 state gate remains FAILED, threshold1e-5 unchanged. Latest1% user
allowance is task accuracy, not tensor correctness. After actual seam proof,
use a fresh production SO and step45 -> B1/B16x160 -> source-bound generalSR/
all final plans -> graph/typed-cache -> same-dense E2E/task-quality chain.

Current short target directly repairs this proven DAMP quantizer blocker;
parallel KB preparation remains next-paper readiness. Do not replace these
with unrelated fusion, MTP, another paper survey or report-only work.
Individual and portfolio deadlines above remain unchanged.

At12:57:33Z MA0312 observed native-off24/36, capture-on0, all completed rows
have4096 outputs, and only the four owned workers use physical4-7. Native
collector/source/helper/launcher28 file hashes were verified unchanged MA0303.
The actual run/validator bind source bytes, not a changing documentation Git
HEAD; no capture module or protocol is edited by this preparation checkpoint.

V3 kernel642afb... now actually built MA0309, completed12:58:52Z, both compiler
commands0; actual exported launcher is T rather than U. SO SHA
f21105e61577f938fb8e039d1481e912c22760061bcd38a11348af5ec4472619.
New no-device Meta MA031e is running; do not claim its result until terminal.
No real NPU certificate, production repair or compaction pass exists yet.
V1/v2 failed load/compile histories remain unchanged.

Reviewed KVBuffer/operator/source bound checks and scripts/validate-mst.sh
passed MA0303. Staged full whitespace check MA031a exited2 only for three
copied LICENSE.cann trailing-whitespace lines2/16/23; retain exact upstream
license bytes and this negative, not a blanket whitespace PASS. The separate
authored-code/document whitespace check passed. This checkpoint includes the
reviewed21-file KVBuffer preparation and production seam review plus these
maintainer lessons; the evolving certificate/compaction drafts remain outside
this specific commit. No raw tensors/datasets/binaries enter Git. It is not
an accepted performance/quality milestone.

## 13:09Z certificate actual load result and frozen source checkpoint

Normal branch checkpoint 0c9db4557af2345c2c587a7b86c0aef771c7c8d4 was pushed
and its exact remote ref verified MA0324. It contains the reviewed KVBuffer
parallel preparation and scoped maintainer/production-review lessons, not an
accepted serving result. No main/force push or reference runtime edits occurred.

The previously running certificate no-device Meta MA031e now ended terminal0.
Actual report status=pass, SHA
d89c57e3430874707b8a8524ad951e327dfc3088fb0f3a92aff8223054b1eb05,
at /cache/cch/qwen36-damp-20261006/integer-certificate-meta-v2/gate/report.json.
It actually loaded build-v3 SO f21105e61577f938fb8e039d1481e912c22760061bcd38a11348af5ec4472619
and observed both operator schemas, two positive Meta geometries and the
source-bound runner's negative admissions. It explicitly has npu_executed=false,
graph_supported=false and production_integrated=false. Compiled9/runtime16
were unchanged before/after. Do not call this device correctness or performance.

MAIN readback MA0330 verified all30 certificate source/document/audit files,
parsed current Python sources, and observed native-off24/36 rows; native-on
has not started. MA0161 still runs. Only this reviewed certificate subtree
plus this handoff update is checkpointed now. Compaction's separate12-file
draft is excluded pending MAIN review/build; its49 software cases and static
scan are not NPU evidence. No collector/production/frozen helper bytes change.
Keep v1/v2 failures, source archives and their unchanged hashes in the record.

Next physical-device action is still serial after the TP4 collector releases:
isolated quantizer/certificate/compaction and independent native anchors before
any new packed production SO, then step45 and multi-step/general-SR/graph/cache
gates before serving. Individual/portfolio deadlines do not reset. No new
non-HYPIC final throughput/LongBench-v2/GSM8K acceptance exists.

MA0333 checked the actual compiled9/runtime16/source30/SO bindings and current
Python AST/JSON files, and validate-mst.sh passed20 skills. The full staged
whitespace check exited2 solely for13 extra-EOF blank-line notices in frozen
source/helper/template/archive files. Preserve bytes bound to prior runs;
this is a recorded negative style check, not a whitespace PASS or device gate.

## 13:30Z compaction readiness and live capture

Normal checkpoint86c078fe1140027c39b31cb8801c9b892f99be1b was pushed and its
exact remote ref verified. It contains the reviewed30-file certificate, not a
usable performance/quality result.

Full-capture MA0161 is freshly RUNNING at13:30Z. Last completed-row observation
MA0361 at13:26:05Z: native-off28/36, all4096 outputs, native-on0. Full validator,
source lock and fitted192 plans are pending. The fresh resource snapshot
MA0336 at13:12Z had only owned workers744181/744186/744190/744192 on4-7 and an
external HYPIC service on protected0-3. No new NPU load during this TP4 capture.

MAIN fully reviewed the separate compaction probe and its minimal v2 fixes.
V1 MA0335 failed compilation on device std::array indexing and uint8 Duplicate;
original logs and byte-exact source archives are preserved. V2 MA0346 actually
compiled/linked and defined its launcher symbol; MA0358 actually loaded both
schemas and passed Meta plus18 separately recorded negative rejections.
Read projects/damp-ascend/operator/quantizer/compaction_probe/ACTUAL_BUILD_META.md.
SO080075a52c8a9b3736e9077149268bb48481b15a8e855e3dca82617bf8489b9c;
build receiptb874ed8b88d2343e3f4457a6090b34f386b4a891ef047695cb02c8306f53b98d;
parent Meta report5f87f31d1b70a7c481787e6a39a53a740b71c8d4a37642701276b1c8def40bfa.
Compiler8/runtime13 were unchanged. These no-device checks are NOT actual
NPU compaction, production, recurrence, graph, timing or task-quality proof.

Only this reviewed16-file compaction subtree, scoped maintainer lesson and
handoff are included in this checkpoint. New production_integer_compaction_v1
and KVBuffer tools/service drafts are excluded pending MAIN full review.
Production v4 remains FAILED at step45; no threshold changed. After capture
releases, fresh serial device seam/native-anchor gates must precede a new
production run, then full feedback/generalSR/graph/cache and matched service.

Portfolio cutoff2026-10-09T11:17:31Z and DAMP individual cutoff
2026-10-07T08:48:03Z are unchanged. Zero new non-HYPIC techniques have final
performance plus LongBench-v2/GSM8K acceptance. Compilation/sample/shadow or
same-eager screening success must not become the required usable conclusion.

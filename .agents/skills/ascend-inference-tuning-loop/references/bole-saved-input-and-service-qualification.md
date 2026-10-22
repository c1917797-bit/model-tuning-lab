# Saved-input diagnosis and bounded BOLE service qualification

Use after a BOLE/GDN component, native-control, consumer or service-entry failure.
These are verified stage lessons, not a new technology acceptance report.
Read the linked original records before reusing any result; an old PASS grants
neither a new resource lease nor a later-stage PASS.

## Contents

- [Earlier scoped successes](#evidence-backed-successes-and-what-changed-the-next-action)
- [Preparation failures](#failures-that-must-change-preparation)
- [Regression scenarios](#reusable-regression-scenarios)
- [Earlier source records](#source-records-and-remaining-acceptance)
- [Retained first failed entry](#historical-first-failed-entry-retained-not-the-latest-state)
- [Exact readsets and frozen bytes](#exact-readsets-and-frozen-bytes)
- [Metadata-only recovery](#metadata-only-recovery)
- [Executable-file identity](#executable-file-identity)
- [Outcome boundaries and evidence anchors](#outcome-boundaries-and-evidence-anchors)
- [Native collective repeatability](#native-collective-repeatability)

## Evidence-backed successes and what changed the next action

1. **Reuse the exact failed inputs to discriminate causes.** The saved native-AR
   attention replay reproduced all 256 original outputs bitwise. Under unchanged
   pointwise bounds, BF16 had 39 failures with either inner-precision setting;
   FP16 had zero with either setting. This supports a boundary-precision repair
   for that private control, not a general claim that BF16 or production vLLM
   is wrong. Preserve original BF16 results, label FP16 as a new variant, and
   require the subsequent model/control comparison. A source-derived private
   AR implementation is not the untouched production dispatcher.
2. **A narrow reader repair can avoid recapturing model tensors.** R20's receipt
   comparison reused `expected` for a dictionary, overwriting the rank counter.
   The repair renamed only the local cast variable, bound the original producer
   root and recorded the new reader identity; original math and tensor bytes
   stayed unchanged. Preserve the failed parent. Qualify captured completeness,
   ownership, source/raw hashes and the complete independent consumer under a
   new result identity before using the recovered evidence. Do not mark the old
   run PASS or assume all remaining model discrepancies disappeared.
3. **Carry the actual mechanism into an incremental service test.** Service v6
   passed a bounded TP4 first-request test: 131-token prefix, four output tokens,
   component gates, actual scheduler publication, HTTP token-ID joins and
   all-rank retirement. G1 v2 then passed two distinct sequential requests, each
   with two output tokens, including process calibration reuse. These close
   specific service edges. G1 observed no physical slot reuse and zero cross-step
   next-counter acknowledgements; those edges remain unverified. Native-AR
   comparison, long output, graph/concurrency coverage, tasks and formal timing
   cannot inherit this PASS.
4. **Optimize only the paper-linked computation and independently replay it.**
   GDN replay v2 retained the original Torch P construction and checked fused
   O/U and selected states on 192 captured frames in two layouts (384 frame-layout
   cases). Independent original-bound checks passed; P and post-call inputs were
   checked bitwise. This is numerical qualification of that component, not its
   service integration or a measured speedup.
5. **Separate a completed arm from a completed pair.** The later short-state
   BOLE ON and OFF v2 arms each finished their bounded TP4 request and
   all-rank state-receipt checks with no host primary or cleanup error. The
   arm reports still set model/performance qualification false. An independent
   ON/OFF reader must join the exact source, HTTP, state and cleanup evidence
   before state equality can be claimed; two green arm reports do not imply it.

## Failures that must change preparation

- **Validate hook installation order against the real lifecycle.** Service v5
  loaded weights but its first prefill saw a premature target-head wrapper.
  V6 delayed installation until native prefill capture and independently checked
  actual hybrid-cache geometry. A mock that begins after installation misses
  this boundary. Exercise cold prefill -> install -> use -> restore/retire,
  with duplicate/early install negatives and explicit single ownership. Keep
  controller/environment failures separate from the first worker failure.
- **Treat provenance tooling as executable code, not infallible evidence.**
  GDN timing v1 failed before samples because class-level source reflection could
  not locate the dynamically loaded AscendBackend. The source-qualified repair
  binds the actual compiler methods and their files; an unknown method still
  rejects. Its same-image nine-control pass is not an actual timing result.
  Test the real reflection/loader path, not an ordinary static class fixture.
- **Keep the diagnostic runtime inside its own budget.** The saved-reader
  continuation exposed an unavailable CPU-affinity choice and a whole-file hash
  allocation exceeding its controller cap. Use actual effective cgroup CPU
  membership and bounded streaming hashes; include the reader in aggregate
  host budgets. Do not rerun an expensive NPU producer to fix a CPU-reader seam.
- **Match task inputs to the frozen scorer.** The retained task audit identifies
  a removed GSM answer-format instruction while the original strict scorer
  remained. A new input variant must preserve original token IDs where specified,
  prove the exact intended edit and check the actual tokenizer/template on all
  rows. Never relax the scorer to conceal an input-contract defect. Use the
  latest explicit task scope for new runs; do not silently union superseded task
  lists or claim smoke accuracy as full scoring.
- **Test the real bound MODEL entry, not only its preflight.** The short-state
  v1 package passed source audit and same-image software preflight, then its
  actual MODEL entry rejected a streaming client absent from the declared
  dependency closure before NPU work. The new v2 binds both the client and
  timing donor exact Refs into dependencies and adds real-entry positive and
  missing/stale-operand negatives. Collect every runtime-dereferenced operand,
  require exact closure membership and execute the entry prefix without an
  owner before device admission. Preserve the pre-NPU failure and use a new
  source/output identity; a preflight PASS cannot stand in for that entry.
- **Validate the producer's evidence-reference shape in the independent
  reader.** After both v2 arms completed, the first short-pair reader stopped
  before state comparison: cleanup summaries carried path and SHA but no byte
  count, whereas its strict Ref reader required path, bytes and SHA. This is a
  reader/report-contract failure, not a state mismatch. In a new reader version,
  accept only the documented summary shape, reopen the whole file with a
  bounded read, check its computed SHA against the summary, and then run every
  original cleanup and state predicate. Retain the failed reader execution;
  neither loosen the digest equality gate nor rerun the NPU arms for this
  metadata-only defect.

## Reusable regression scenarios

| Trigger | Required action and check | Prohibited promotion |
| --- | --- | --- |
| Saved-reader variable shadowing | Replay original record through the complete repaired consumer; math/source/raw unchanged | Failed parent becomes PASS |
| Native-control precision disagreement | Same inputs, original bitwise replay, independent oracle, explicit boundary variants | Private control represents production dense |
| Two successful sequential requests | Record actual slots, counters, retirements and missing event classes | Sequential requests prove reuse or long decode |
| Dynamic backend reflection failure | Check actual method identity/file hashes; negative unknown method; rerun affected timing gate | No samples means no benefit |
| Device-free reader cannot fit | Repair actual affinity/streaming and joint budget; reuse qualified capture | Needlessly recapture or raise reserves |
| Prompt/scorer mismatch | Freeze new input identity; exact diff and real tokenizer/scorer checks | Rewrite old inputs or loosen scoring |
| Real entry missing declared operand | Execute actual bound MODEL prefix plus missing/stale Ref negatives | CPU preflight implies NPU readiness |
| Paired reader rejects partial cleanup Ref | Reopen exact path, bound bytes, compare declared SHA, then apply all original predicates | Call two completed arms state-equal or recapture NPU |

These checks are future regression requirements, not a claim that new software
or NPU tests were executed during this documentation update. Reuse the existing
[failure-to-action rules](failure-root-cause-and-next-action.md) and
[stage scheduling rules](portfolio-preparation-and-serial-admission.md);
do not create another controller or duplicate global checklist for these cases.
Release a failed device stage after verified own-only cleanup; its device-free
repair must not hold a different ready paper's lease. Verify actual handoff
timestamps before claiming utilization improved.

## Source records and remaining acceptance

All paths below are under
`.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/`:

- `R20_CONSUMER_REPAIR.json`: exact reader edits and unchanged-math identities.
- `NATIVE_AR_FA256_DECISION.json`: original/variant replay and unchanged gates.
- `SERVICE_MODEL_V6_AUDIT.json`: first-request service scope and explicit false
  whole/model/task/performance flags.
- `G1_MODEL_V2_AUDIT.json`: sequential requests and missing reuse/cross-step coverage.
- `GDN_REPLAY_V2_AUDIT.json`: 192 x 2 independent component qualification.
- `GDN_TIMING_V1_FAILURE.json`, `GDN_TIMING_CPU_V2_AUDIT.json`: failure and
  device-free repair, no timing samples.
- `TASK_SCOPE_RECONCILIATION.json`: latest frozen task scope and missing scores.
- `bole_performance_profile_prepare_20261021/successor_layer/state_digest_gate_v3/DELIVERY.json`:
  short-v1 missing-client closure diagnosis and v2 exact source identities.
  The ON/OFF v2 host results are under
  `/opt/host/vnf/austinov/run-bole-short-state-20261021T123841Z-{ON,OFF}-v2/RESULT.json`.
  The first `compare_completed_short.py` invocation failed at the partial
  cleanup Ref before comparing states; paired equality and formal performance
  remain unverified. See `SHORT_STATE_PAIR_READER_V3_FAILURE.json` for the
  exact operation and first failed predicate.

The ingestion checkpoint records which audit files were read and which raw
identity checks remain unconfirmed. These are recorded experiment results, not
new tensor re-adjudication. No new formal throughput or task-accuracy result is
established here. Required final evidence remains the frozen
matched whole-model performance and task contract; do not substitute kernel
timing, short HTTP output or this maintenance work.

## Historical first failed entry (retained, not the latest state)

The following records the earlier model131repair12 attempt. Later scoped
successes above do not rewrite this failure, and this failure must not be used
to claim that the current implementation has never entered the service.

## BOLE E2E case study: verified outcome and recovery lessons (2026-10-20)

Use this case when a BOLE/native-MTP experiment passes admission but fails at
full-model or independent-consumer validation.

- **Verified successes:** after updating the active authorization in the nested
  host and worker gates (not just the top-level manifest), the exact source
  readset reached 312 entries and source audit passed. The same-image software
  suite reached 136/136 only after the current authorization, command/output
  joins, and worker-window binding were consistent. The bounded Ascend run then
  created the TP4 container, launched four workers on physical cards 4–7,
  produced per-rank native MTP load receipts and reached the actual request and
  independent-consumer stages. These are stage successes, not paper acceptance.
- **Verified failure:** the terminal result for
  `run-bole-model131repair12-MAIN-20261020T123000Z` records
  `model_ready=false`, `candidate_qualification=false`, and the primary fault
  `original component mathematical gates failed` in the independent consumer.
  Preserve the raw metrics/vectors and classify this as a numerical/component
  gate failure; do not relabel it as a successful E2E or a performance result.
- **Nested stale gates matter:** the top-level `contract090.py` and
  `owned_substrate.py` were rebound, but the first software runs still failed
  because `worker_bootstrap.py` retained the old time window. Search all
  transitive launch, worker, controller, consumer, command, and receipt modules
  for old batch IDs/cutoff constants before regenerating the readset. Never infer
  closure from one passing source-audit report alone.
- **Unique output is part of provenance:** reusing an already-created output
  root correctly failed the launch gate. Allocate a new immutable output root
  per attempt and update both the source contract and command manifest; do not
  delete/overwrite a prior result just to make a retry fit.
- **Preserve original assertions:** one retry exposed failures in historical
  identity/inverse-edit tests. The right repair is to ledger the intended
  source delta and separate the newly batch-bound worker gate from genuinely
  immutable algorithm source—not to disable mathematical checks or broadly
  rewrite expected results. The eventual 136/136 pass is only a software gate.
- **Interpret load receipts narrowly:** the observed class was the unmodified
  `Qwen3_5MTP`, with `BOLE=false` and `forward_modified=false`. This confirms
  native MTP loading, not that the BOLE intervention is active. The independent
  consumer must verify actual intervention attribution, numerical/component
  invariants, and the registered model-level evidence before any promotion.
- **Control-plane timeouts are ambiguous:** after an AWMCP timeout, poll the
  original operation and inspect the remote process/container before retrying.
  This run remained alive through worker startup and later reached the
  independent consumer; launching a duplicate during that interval would have
  competed for the same leased cards.

For the next BOLE attempt, begin from the preserved terminal result and the
independent consumer's raw per-component metrics. Make one causal repair,
regenerate source and command refs, rerun the same-image suite, and only then
admit a fresh bounded TP4 run. Keep the successful admission/load/request stages
as stage evidence while the mathematical gate remains failed/pending.

## Exact readsets and frozen bytes

Apply these rules when a host audit passes but a declared guest entry or later
consumer rejects an input. Preserve the failed run and repair a new source
version; do not widen a directory mount or bypass the original checked Ref.

- Enumerate every file reopened by the complete declared entry, including old
  layer actors, inverse ledgers, private cold modules, fixture donors and nested
  consumer inputs. Require those exact Refs in both preparation dependencies
  and validator-required inputs, and derive the guest RO mount readset from that
  closure. A host-readable path is not proof of guest visibility.
- G3 v1's 5000-input audit passed while all17 old L4 actors were omitted from
  the guest input set; its actual software child failed before running tests.
  V2 included those17 in both builder dependencies and validator requirements:
  current5017/required4647/parent4559 and ordered host audit5118 passed.
  These count different collections; do not equate or sample them.
- Keep v2's six pure Parent/Prepare controls separate from the still-unrun381
  same-image suite and actual1024 output gate at the handoff checkpoint. Source,
  AST, OFF/help and inverse proofs do not execute the enabled cold service path.
- Treat frozen source bytes as an ABI. An extra final LF can invalidate a
  qualified source even when Python semantics are unchanged. The GDN lineage
  required qualified sourceio1037 bytes; the G2/G3 lineage retained its original
  sourceio1038. Restore the correct whole-file version before sealing, record
  the complete inverse delta, then rebind and audit. Do not normalize all
  lineages, weaken the equality gate, or edit a live bound manifest.
- If frozen copies contain historical whitespace, permit only exact
  baseline-Ref-verified paths/findings in the checkpoint audit. Keep new
  controllers and all other diff checks strict; do not blanket-ignore a
  directory or change frozen bytes to make formatting green.

## Metadata-only recovery

Prefer a new bounded reader over recapturing qualified model tensors when the
failure is in provenance, report interpretation or retained-source projection.

1. Reconstruct the complete original source closure and original software gate.
   Reopen every retained Ref using complete streaming SHA and stable-file checks.
   Keep original raw files, source manifest, failed parent exit and output root
   immutable. Charge the reader to its declared CPU/RAM/disk/clock budget.
   A604MB rank file cannot be read whole under a512MiB address-space cap.
   In this controller, retain the approved Docker/Go child AS wrapper and actual
   RSS bound; do not raise caps to accommodate an unbounded reader.
2. Derive a role's expected resource profile from its pinned source, actual
   create argv, OWNED and saved inspect. A serial GDN model used four CPUs;
   another stream model used three. A guessed profile in a checker is a checker
   defect, not permission to mutate the completed model or accept arbitrary
   CPU/device/memory settings. Preserve the false refusal and reexecute every
   predicate with the exact intended role profile.
3. Diagnose collection-order differences before changing equality. For Docker
   Mounts, first require unique destinations, then compare complete mount
   dictionaries keyed/sorted by destination. Preserve Source, Destination,
   Type, RW, Mode, propagation and all other fields. Reject an attribute change,
   duplicate, missing or extra mount. Do not sort away changes to State,
   HostConfig, Config or security/resource fields.
4. If two captured image-only framework sources are absent on the host, bind
   exact guest Ref3 identities and all-four snapshot/host-binding occurrences.
   Copy only those files from the same source-owned stopped-retained image/CID,
   using readonly Docker cp without start/create/exec. Verify whole bytes and
   saved/current stopped owner metadata before and after. Retain host copies
   and a separate projection manifest as post-execution evidence; do not
   retrofit the original SOURCE_BOUND or add a path-prefix exemption.
   The matched-v5 case joined two files/31121 bytes against eight occurrences
   each. Unknown installed Refs must still reject.
5. Exercise the actual enabled reader CLI to its final collection/output path.
   Default-OFF/help did not expose v3's argparse variable overwritten by a
   numerical metric loop. Bind CLI arguments separately from per-metric values;
   preserve the v3 failure and run all predicates again in v4. Confirm the actual
   traceback and assignment path before attributing a new reader failure to the
   same cause.
6. State what the recovered reader did. The matched-v5 reader checked all384
   saved O/P/U/selected metrics, full source/software/component and all-four MTP
   load joins, stopped owners and840 retained Refs. It did not rerun tensor
   mathematics, import Torch, query live NPU identity or qualify whole-model,
   task, normal EOS or formal performance. Keep those flags false/pending.

## Executable-file identity

Use this distinction when ELF bytes match but strict executable maps identity
does not. Full SHA/buildID equality and map device/inode equality prove
different properties; neither substitutes for the other.

- Retain the complete failing maps, mountinfo, stat and ELF inventory. The
  actual diagnostic saw176 entries:174 overlay mismatches with matching inode
  but mapdev8:8/stat0:77, one matching driver, one original explicit vdso skip.
  Do not disable dev/inode checks, grant capabilities, or allow path prefixes.
- The subsequent readonly copy preserved all174 original ELF contents,
  1267866920 bytes, with largest file280680576. Parse the actual interpreter's
  PT_INTERP and join its followed contents to the unique observed canonical
  loader; do not guess loader paths or alter LD search behavior. Preserve
  executable mode before freezing host files and record changed filesystem
  objects honestly. Whole-copy source success is not mapped identity success.
- A successor must declare all immutable host Refs and explicit canonical guest
  RO aliases, including Python and loader, before container create. Validate
  the original create baseline plus the exact alias delta, its argv inverse
  and the complete actual mount closure; do not permit arbitrary extra RO.
  First pass the original Devices[] CPU metadata/maps gate, then the original
  physical4 singleton128 frames x two fillers =256 native calls.
- Reject unknown libraries from lazy dlopen and preserve that failure. Expand
  only a new source-reviewed exact catalog with actual observations, rerunning
  all required gates. Do not fabricate a CPU PASS, warm up unknown operators,
  change the numerical oracle or relax bounds to get past the next stage.
- Keep earlier FP16 saved-control successes source-scoped. They do not settle
  the later FIA path's original16-frame/32-coordinate numerical failure or prove
  unchanged production native-AR behavior. Resolve each path's own source,
  input, oracle and complete native-call evidence.

## Outcome boundaries and evidence anchors

Treat the following as a historical checkpoint at the authorized transfer,
not current host state or a reusable lease. The source-side scheduler stopped;
the09:12:32 UTC snapshot recorded the already-admitted candidate unit naturally
active/exited with both PIDs0, stopped owned containers and released MAIN.
Earlier09:04 prose still showed a running consumer; use the timestamped fresh
JSON, not a stale sentence. Re-prove live state at a new takeover.

| Scope at that checkpoint | Observed evidence | Still missing |
| --- | --- | --- |
| G2 source13 short stream | Two requests/four tokens, HTTP/ACK/retirement/MTP joins and independent4556 retained Refs | Actual long1024, normal EOS, task and formal performance |
| GDN matched-v5 | Actual384 numerical frames, source732 equality and independent840-Ref metadata recovery | Candidate qualification or whole-model/task/performance acceptance |
| GDN candidate-v5 CPU | Actual240 same-image controls/parser; independent732-source/738-Ref readback | A CPU pass cannot supply model or formal qualification |
| GDN candidate-v5 MODEL | Handoff snapshot contains successful RESULT and a384-frame consumer report | Its own complete independent metadata reader remained pending; matched CID/source cannot substitute |
| G3 v2 | Exact17 dependency repair, full source/host audit and six pure controls | Actual381 same-image/cold and1024 model were not run |
| Native AR bridge | All174 exact ELF copies and actual PT_INTERP content join | Explicit RO bind adapter, original CPU identity gate and256 native calls; numerical failure unresolved |

Apply [maintainer handoff](../../mst-maintainer-handoff/SKILL.md) when transferring
a finite controller. Record original authority and remaining clocks; transfer
does not restart or extend them. The historical window ended at1792597630
(2026-10-21 15:47:10 UTC), phase3600/shared cleanup180; these are run-specific
facts, not universal defaults. New work must use its own latest authorization.

Reopen these records under the source-record directory above; use exact source
and whole-file identities rather than borrowing their counts:

- G3_V1_CPU_FAILURE_AUDIT.json, G3_EXACT_LAYER17_DEPENDENCY_REPAIR_V2.json,
  G3_SOURCE13_ACTUAL_SOURCE_PREPARATION_EXECUTION_V2.json,
  G3_ACTUAL13_PARENT_PREPARE_FIXTURE_CONTROLS_V2.json and G3_V2_HOST_SOURCE_AUDIT.json.
- GDN_MATCHED_V5_MODEL_METADATA_READER_EXECUTION_V1.json through V4.json
  (spell out the full stem for each), GDN_MATCHED_V5_MODEL_METADATA_READBACK.json,
  GDN_CANDIDATE_V5_CPU_METADATA_READBACK.json and
  GDN_MATCHED_V5_MODEL_SUBMISSION_EXECUTION.json / _V2.json.
- GDN_MATCHED_V5_INSTALLED_SOURCE_INSPECT_ORDER_DIAGNOSIS.json,
  GDN_MATCHED_V5_INSTALLED_SOURCE_COPY_EXECUTION_V1.json / _V2.json,
  gdn_matched_v5_installed_sources_v2/PROJECTIONS.json.
- native_ar_elf_bridge_v1/CATALOG.json,
  NATIVE_AR_EXACT174_ELF_COPY_EXECUTION_V1.json,
  CHECKPOINT_V30_FROZEN_SOURCE_WHITESPACE_AUDIT.json,
  CURRENT_NEXT_BACKUP_V30.json and HANDOFF_TO_PAPER_ASCEND_0909_20261021.json.

Source/evidence checkpoint0321f257 and transfer checkpoint51d9d9fd retain the
successes and failures. The associated maintainer decision fixtures are
[the evidence/transfer case](../../../evals/transformation-cases/bole-evidence-and-controller-transfer-20261021.yaml).
This skill update only reopens metadata and checks maintainer decisions; it
does not rerun an experiment or establish any new numerical, task or speed claim.

## Native collective repeatability

Use when identical pre-reduction tensors produce different downstream model
states. Do not immediately classify this as a paper-algorithm defect.

- Save the complete per-rank pre/post tensors and actual runtime flags before
  modifying math. Verify finite values, source/shape/dtype, request/rank identity,
  cross-rank agreement and stable raw hashes with an independent consumer.
- A high-precision exact sum is a useful reference, but differs from a specified
  finite-precision reduction order. A mismatch alone does not prove the native
  collective is incorrect. Possible BF16 addition trees checked per coordinate
  are diagnostic, not proof of one globally shared tree or full error coverage.
- Reuse captured pre-inputs for a small native same-image repeated collective
  test. Change one explicit configuration variable. Reset inputs before each
  call, verify full outputs, and record all-rank flags and observed library Refs.
  An unset HCCL flag is not proof its effective native setting is false.
- In the October22 case, default replay produced eight different full outputs
  per rank; explicit HCCL_DETERMINISTIC=true produced one output across eight
  calls, with four-rank agreement in both variants. This supports a common
  reduction-configuration hypothesis, not BOLE qualification or an HCCL bug claim.
  The standalone WORLD communicator is not the production vLLM TP group.
- The next discriminating test is the actual production path: bind the common
  configuration before worker initialization, verify it in every real worker,
  then rerun the relevant original numerical/state checks. Apply any adopted
  common setting equally to native control and candidate; remeasure both.
  Keep original failed/variable outputs and unchanged numerical thresholds.

Evidence: workstream COLLECTIVE_CAUSAL_CHECKPOINT_20261022T210000Z.md records
the whole-model V5 capture, independent partial BF16 analysis, both actual NPU
replays, terminal raw-file rehashing and verified own-only release. None supplies
formal throughput or task quality. Reusable lesson: a successful isolated
discriminator should shorten the next production test, not grow an unrelated
source/profiling campaign.

The subsequent production V7 diagnostic completed two131-input/8-output
requests. All eight real worker observations reported the explicit common
flag; sixteen complete pre/post files (21463040 bytes) matched across the two
requests and post-reduction agreed across four TP ranks. The independent
consumer also reexecuted the original HTTP/state/lifecycle join (32 rank
frames). This supports repeatability at the captured first prefill projection,
not BOLE mathematics, general decode determinism, task quality or speed.
See STARTUP_HEALTH_REPAIR_CHECKPOINT_20261022T215000Z.md in the workstream.

## Bounded startup calls and recorded operands

- Distinguish an HTTP socket timeout from the outer container command deadline.
  The V6 production startup failed because a4-second Docker/env/Python call
  raised TimeoutExpired; the model had not completed a request. A fresh V7
  source bounded that call by min(30,startup remaining,phase remaining), kept
  the inner2-second HTTP timeout and original overall budgets, and completed.
  These numbers describe this case, not universal defaults. Preserve the
  timeout failure and classify it as startup control, not a paper no-go.
- A timed-out Docker client does not establish that its guest probe exited.
  Do not catch and retry unknown live probes. Here TimeoutExpired remained
  fatal and triggered the original own-only cleanup; only completed nonzero
  health calls could loop. Test server exit and budget exhaustion as well as
  slow completed probes before another model load.
- Some legacy command contracts compare the complete serialized JSON operand.
  A semantically equal Ref with reordered keys can therefore fail the actual
  command gate. Reuse the operand recorded in immutable COMMANDS, including
  nested configuration serialization, rather than reconstructing it with
  sorted keys. The small command_operand_binding_prepare helper exercises the
  actual source_inputs positive/negative path. This is a compatibility seam,
  not a reason to impose key-order rules on unrelated JSON or weaken gates.

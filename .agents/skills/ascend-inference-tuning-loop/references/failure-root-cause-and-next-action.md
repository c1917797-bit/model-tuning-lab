# Root-cause classification must select the next experiment

## Qualify physical layout by its actual consumer

Do not reuse a recurrent-state-only format predicate for an independently
allocated full-attention cache. First preserve native format/type, typed view,
shape/stride/offset, full storage span, rank and allocator provenance for both.
A numeric format label alone neither proves invalidity nor justifies acceptance.
Separate their source-qualified identity checks and retain cross-owner physical
overlap rejection; do not reinterpret BF16 cache bytes as FP32 recurrent state.

AdaKV030's real four-rank plans exposed this reference defect before the first
model output. A new FA-specific check passed193 software regressions including
actual-plan replay and invalid-view negatives, while GDN stayed strict ND.
That software result and a generated deployment tree do not prove new model
numerics, graph/lifecycle correctness or speed. Preserve the failed original
and require the affected real-device gate; if its full budget cannot fit the
fixed paper window, retain an implementation-inconclusive result rather than
shortening coverage or judging the paper. Exact evidence is in the active
workstream's ADAKV030_FA_LAYOUT_AUDIT_FAILURE_20261010.json.

## Author AST fingerprints across interpreter versions

When frozen official-source AST hashes fail, compare identical raw bytes under
the actual host and image interpreters before changing author code or hashes.
CPython3.12 adds empty type_params to definitions absent from CPython3.9 dumps;
unchanged algorithms can therefore be rejected before numerical comparison.

Only after exact-image evidence proves this difference, use a source-qualified
projection of known empty schema extensions on a deep copy. Preserve original
source-byte identity and stored hashes; compile the original tree. Reject changed
bodies, nonempty generics, unknown fields and unsupported interpreter schemas.
Test real author methods and negative mutations, not only a synthetic fixture.

AdaKV026 recovery passed14 host regressions and same-image Devices=[] precheck:
all4 native3.12 hashes differed and all4 projected hashes matched unchanged
originals. This proves the reference serialization defect, not author arithmetic,
real-Torch loading, model numerics, the earlier PA failure or performance.
Carry the precheck into the real before-model entry and rerun the complete
affected model gate. Exact sources/results remain in the workstream.

## Native enum transport versus semantic identity

A source-pinned producer can correctly verify an enum member and then serialize
its str() representation. Its consumer must match the deployed representation,
not an imagined literal. Before a costly model gate, exercise that actual
producer/consumer boundary with original native metadata and a wrong-literal
negative; synthetic fixtures that repeat the consumer's assumption cannot
validate it.

SparQ model007 completed TP4 load and graph capture, then its first warmup
failed before candidate arithmetic: the native producer recorded both values
as AttentionType.DECODER while the reference demanded decoder. Preserve the
failed source/whole terminal and repair only that proved boundary. Replay
all relevant actual records under a new source and run the complete affected
suite. Such replay validates a historical reference seam, not new numerical,
model, resource-admission or performance authority. Keep numerical, ownership,
layout, allocation and deadline gates unchanged; unsupported branches still
reject. Exact source/result identities belong in the workstream causal record.

## Preinitialization: common driver FD is not a compute-context proof

For same-image ABI admission, keep the Devices[] CPU stage strict: no device
nodes, no Ascend FD and no initialized backend. Do not copy that zero-FD
predicate blindly into an already owned hardware canary. A deployed framework
import can open manager/hdc bootstrap handles while its initialization flag stays
false. Preserve before/after flags, exact FD targets, source binding, singleton
device mapping and host ownership. Only accept a source-observed common-handle
case; compute-card/unknown FD, extra device visibility, failed observation or
initialized backend still requires rejection before that explicit stage.
A common FD alone grants no device permission and proves no numerical execution.
Keep the prior CPU source/schema comparison and subsequent actual canary/numeric
gates. Repair a proved wrong-phase predicate with real raw positive/negative
fixtures and a new immutable run, never by skipping the check or raising a
numerical threshold. AdaKV015/MAIN07c5 is this observed reference-test defect,
not an algorithm-negative result; its original logs and exact stop-retain remain.


## Trigger, authority and scope

Apply after any failed paper preparation, native numerical, model, performance
or task-accuracy stage, before changing implementation or moving to another
paper. Practice source: the user's Oct9 instructions to diagnose, repair
adaptation defects and use that diagnosis to choose the next action.

A failed run and a failed method are different claims. Classify the observed
failure AND record whether its cause is proved, suspected or unknown. Do not
force a binary implementation-versus-method verdict when evidence is missing.
This rule grants no device permission and never resets a fixed paper cutoff.

## Required causal record

Preserve the original terminal envelope, exact source/manifest and environment,
full argv, first exception, original inputs and nullable before/after tensors,
actual coverage and untouched partial results, cleanup and resource ownership.
Record the failed gate, classification, causal evidence, alternative explanations,
decision scope, chosen repair or diagnostic, unchanged acceptance thresholds,
new experiment/output identity, owner, remaining budget and successor consumer.

A top-level command exit and a child-suite exit must both be recorded. Partial
passing cases do not make an incomplete aggregate pass. Missing evidence is
explicitly missing, never reconstructed as an original receipt.

## Classification to action

| Classification | Evidence needed | Required next action | Permitted conclusion |
| --- | --- | --- | --- |
| ENVIRONMENT_OR_SCHEDULING | Actual mount/import/native ABI, ownership, quota, memory or deadline evidence; whether algorithm execution occurred | Repair the proved dependency or scheduling boundary; run its missing preflight and a new bounded experiment | This run could not complete valid verification |
| ADAPTATION_IMPLEMENTATION | First failing candidate stage on original input, checked against an independent reference and deployed semantics; or a directly proved runtime/code defect | Fix that seam, add reproducing and negative regression tests, then rerun the affected complete gate | This implementation is defective, not the paper |
| REFERENCE_OR_TEST | The reference, fixture, oracle dtype/order, input producer or consumer contradicts its specified source/ABI | Preserve the failure; repair the test/reference against independent source evidence; run the actual entry, not only a helper | This judgment was invalid or incomplete |
| METHOD_CONFIGURATION_LIMIT | Mechanism fidelity, valid independent NPU correctness and comparable whole-model evidence have passed; no confounding adaptation/measurement defect explains failure | Redesign the paper-specific budget/algorithm path within scope, or close this measured configuration and advance | This method/configuration misses the declared target here |
| UNKNOWN_CAUSE | The first fault is preserved but the above causal evidence is insufficient or unavailable | Run the smallest discriminating same-input control/stage diagnostic or acquire the missing original artifact | Cause unresolved; method remains inconclusive |

Numerical failure alone does not prove METHOD_CONFIGURATION_LIMIT. Compare the
paper's literal/equation reference, the Ascend adaptation and the unmodified
native control on the SAME inputs to separate method approximation, adaptation
error and reference/backend error. Reproduce operation order, intermediate
dtype, masks, state/slot semantics and graph-input synchronization as relevant.
A tensor tolerance is not the user's task-accuracy allowance.

For a performance miss, first prove actual activation, only-paper-delta arms,
identical common optimizations, completed token coverage, observer/profiler OFF,
timing boundary and falls-back/materialization costs. A kernel microbenchmark,
an incomplete run or a mismatched graph/eager control cannot establish a
method-level E2E rejection.

## Repair loop, not stop-at-diagnosis

1. Isolate and preserve the failed scope and any valid predecessor artifacts.
2. Choose ONE evidenced repair or discriminating diagnostic. Reuse a correct
   native primitive; don't rewrite unrelated operators or patch a refuted finding.
3. Freeze a new source identity/experiment and output root; retain failed source
   in Git and large originals outside Git. Never lower thresholds, fabricate PASS,
   exclude observed failures retroactively or retry unchanged deterministic errors.
4. Run complete affected software/CLI/same-image preflight before scarce cards.
   Exercise reused modules and their transitive imports in a fresh process using
   the exact guest entrypoint and source-qualified names. Read-only mounts or
   AST/mock-only tests do not prove import closure; reject foreign cached modules
   and preserve failure before any device initialization.
5. Run the relevant complete NPU numerical/state/lifecycle/graph gate.
6. Only after that passes advance to paired whole-model performance and tasks.
7. Update the causal record: repaired-but-unverified, verified repair, still
   failing, or unresolved. A repair commit is not an NPU or deployment PASS.

A repairable adaptation defect is an action item, not grounds to abandon a
paper and call it ineffective. When the fixed timebox ends, close only the
unfinished implementation as failed/inconclusive with exact missing evidence;
keep the prepared repair for a later explicitly selected continuation. Advancing
the queue does not broaden the negative verdict or reset its deadline.

## Queue recovery linked to the causal decision

Ready means MAIN-reviewed exact source plus actual entry regression and all
device-independent prerequisites, frozen complete case allocation, budgets,
mounts, new outputs and a real next-stage consumer. Source in memory or an
author's ready flag is not executable readiness.

Close NEXT during CURRENT, rather than waiting for terminal to discover
fixture/import/controller defects. Device-free preparation remains parallel.
Use the latest explicit device-concurrency authority: under the current serial
mode, only MAIN admits one paper's device stage. If disjoint device work is
explicitly authorized later, first review compatible controllers and one summed
CPU/RAM/disk ledger. Preserve foreign occupation checks; never mutate a live
source or identity to make an incompatible controller appear concurrent.

TP4/model/profile/formal paired timing remains exclusive across all four cards.
Track actual admission, compute ownership, terminal, release, dispatch and idle
intervals with their concrete blockers. If ready-count is zero, prioritize the
specific failed preparation seam; don't invent external occupation or run dummy
loads. Safe admission and correctness take precedence over artificial utilization.
Report measured reduction of avoidable gaps, not an unverified zero-idle guarantee.

## Early feedback without weakening final acceptance

Before launch, distinguish a relevant diagnostic pilot from the complete
registered acceptance matrix. Close the real downstream model/comparator/task
entry while CURRENT runs, rather than adding unrelated observation frameworks.
A passing pilot may inform a bounded diagnostic model comparison but never
grants complete NPU, formal performance or task acceptance. Existing failed
registered cases remain failed; no retroactive omission or deadline renewal.

## Evidence-backed examples

- SparQ FULL v7 MAIN02a9: 119 tests, 2 failures/4 errors. Duplicate model_ready
  keyword, missing deployed metadata fixture and obsolete allocation/source
  assertions were adaptation/test faults, not paper rejection.
- FULL v9 MAIN02d7: 140 tests still had 4 errors after the first repair.
  A fixture bypassed begin() without mixed_fa and used an unsliceable object for
  production seq_lens. Keep this subsequent failure rather than claiming the
  first repair passed. The corrected fixture must pass the actual suite.
- Native MAIN0227: primary bounded-child timeout, 76/128 completed cases and
  12160/20480 completed steps, no final producer report. Completed case records
  said passed; the aggregate remained failed. Cleanup retained both owned
  containers without OOM. This motivates source-cost-balanced parallel shards,
  not numerical tolerance changes or a paper-wide no-go.

Original source/receipt hashes and changing live queue state belong in the
workstream. These examples explain the decision, not transferable PASS authority.

## Verification

Validate the actual immutable predecessor/producer/consumer chain as a no-load
entry before reserving cards. A fixture based on a successful terminal can miss
the real failed-terminal annotation: AWMCP exit1 may carry error='exit code'.
Accept that exact annotation only with completed exit1, noncancelled/nontimedout,
whole source-bound original proof; continue rejecting transport/unknown errors.
The real0315 dry-entry and36 regressions verified this orchestration repair;
no numerical or paper-performance conclusion follows from it.


Check routing from paper-to-ascend and ascend-inference-tuning-loop plus registry
triggers; run scripts/validate-mst.sh and skill structural validation. Explicitly
review these decision cases: timeout -> scheduling repair; proved code defect ->
adaptation repair; wrong fixture -> reference/test repair; valid comparable
no-gain -> measured-configuration redesign; missing originals -> unknown/inconclusive.
Check concurrency text follows the latest explicit authority, not an old grant.
Documentation validation never grants native/model/performance/task acceptance.

## Cross-phase artifact visibility before NPU admission

A host file's existence and a mocked mount dictionary are insufficient. When
CPU preflight and NPU shards have distinct output aliases, mount the exact ONE
owned experiment tree read-only at the same absolute path in every consumer;
only each controller's own /results alias may be writable. Do not mount a broad
cache root. Include ABI, CPU inspect/ownership/cleanup, allocation/plan, canary
and fresh proof descendants, not just the first file that failed.

A post-release CPU replay may revalidate several historical owners whose source
paths differ from the original CPU consumer's mounts. Build visibility from all
actual inputs the replay inspects, not only that last consumer. If a historical
device-stage directory is needed only for stat identity, mount that exact directory
read-only; it does not justify exposing devices or relaxing the old predicate.
Exercise the real historical records in the same image before the long raw pass.
SKVQ014's offline002 failed because the old TP4 record inspected a driver directory
absent from the new CPU image; actual0600 isolated that single missing source.
The RO repair passed installed31 regressions, but full raw/calibration and model
acceptance remained separate. Keep exact original failures in the workstream.

Before creating a device-bearing container, run the actual same-image no-device
entry that checks the common mount's read-only flag and SHA-bound existing
cross-phase input paths. Derive future mounts from that same reviewed constructor.
Keep software fixtures inside the frozen source closure: a host-only historical
result dependency can itself fail in the image. This is storage/launch readiness,
not numerical or model permission. MAIN031b exposed this defect before arithmetic;
its failed source and original remain preserved and a new identity is required.

## Smoke-first admission and evidence-driven route iteration

Before a NEW experiment starts, preregister both smoke and full gates with
frozen inputs, source/image/model identity, output roots, stage budgets and
independent consumers. Smoke must activate the actual plugin/backend, not a
standalone author sample: representative batch1 and multi-request cases,
eager/graph as applicable, changed inputs, relevant reset/reuse/cache hit and
independent reference. A short sequence that cannot exercise a reset must not
claim reset coverage. Host/same-image CLI/ABI/mount checks precede device smoke.
Each smoke stage has an explicit pass/fail consumer and escalation rule.

Keep production-relevant tensor layouts, cache geometry, precision, ABI and
request ownership in the smoke even when case/request counts are reduced.
Exercise a previously failed seam early. A TP4-only mechanism needs actual
four-worker smoke; a standalone single-card primitive cannot replace it.
Declare unsupported or irrelevant smoke dimensions explicitly. Where failure
depends on a long context, reuse or reset, retain the smallest input that really
triggers it instead of shortening that condition away.

Passing smoke permits only the next preregistered diagnostic/full gate; it never
replaces full numerical/lifecycle coverage, three paired performance runs or
complete task scoring. A short-output model smoke is correctness/activation
only, never the fixed1024 throughput result. Full performance uses fixed1024;
task evaluation uses normal EOS/no-thinking/max2048. Never retrofit smoke into
a live frozen run, omit failed cases or restart a clock to improve coverage.

At every terminal, create one bounded decision record:
failed_stage, cause_class, causal_confidence, first_fault_refs,
independent_control, alternative_explanations, changed_hypothesis,
minimal_repair, regression, unchanged_gates, remaining_budget,
next_exact_entry, decision (REPAIR / DIAGNOSE / ADVANCE / CLOSE_CONFIGURATION /
INCONCLUSIVE). Proved adaptation or test defects select REPAIR; missing cause
selects DIAGNOSE. Only mechanism-faithful, independently correct, valid paired
whole-model evidence supports CLOSE_CONFIGURATION. None proves universal paper
ineffectiveness. No new-evidence-free deterministic retry. Allocate another
iteration only when a concrete change has testable prediction and fits the
existing deadline; protect budget for matched E2E/task acceptance.

The iteration record also states the predicted observable improvement and the
result that would refute it. A valid performance miss needs a measured
paper-linked cost or bottleneck hypothesis before another optimization round;
correctness instrumentation and kernel sums alone are not a speedup forecast.
Stop an unproductive route when the remaining budget cannot complete its next
discriminating gate and downstream acceptance, or when the new result refutes
the repair hypothesis. Preserve an implementation-inconclusive verdict when
repair is unfinished; time spent does not become evidence against the paper.
Reuse source-bound unaffected predecessor evidence, but rerun the complete
affected gate after a repair and state why the other evidence remains valid.

Within one bounded admission or whole-result verification, execute each required
full predecessor replay once and pass its consumed result to dependent helpers.
Bind that reuse to exact input/source references and recheck their immutable
identity before final acceptance; changed references invalidate it. Start a fresh
replay for the next invocation. Do not introduce a persistent generic PASS cache,
skip mathematical checks, widen the budget or refit unchanged producer artifacts
to compensate for duplicate helper-level replay. Compare the full call graph's
work with the phase budget before scarce-device admission.

MAIN keeps an executable ready inventory, not an authored-source inventory.
While CURRENT computes, close NEXT's exact launch and successor consumer.
Keep device stages serial under the current authority; disjoint smoke/full jobs
require explicit later authorization and a reviewed summed ledger.
TP4/model/profile/formal paired timing remains exclusive. Measure useful stage
completions per card-hour, launch failures, native compute ownership, terminal
to release/next dispatch latency and idle causes. Queue target is at least one
reviewed executable backup; explicitly report when it is not met. Use real
input/initialization checks, never dummy load, to eliminate avoidable gaps.

## Shared physical pools and reference ownership

When several logical cache views share storage, distinguish exact typed-view
aliases from partially overlapping views and from legitimate different native
writers. Charge and actually create one before-copy per required physical owner;
deduplicating only the budget does not fix duplicated allocations. Keep every
logical layer's source-bound metadata/identity and coverage references. A storage
pointer alone cannot prove identical views or semantic ownership.

A whole-model untouched-state reference must account for ALL legitimate writers
to the pool using their actual source-supported indices or slot mapping. Do not
classify another layer's valid writes as corruption, exempt an entire partly
written row, or drop padding/untouched bytes to make a gate pass. Mixed-dtype
storage also needs typed ownership: bytes holding BF16 FA cache must not be
reinterpreted as live FP32 recurrent state for a finite check. Keep all genuinely
unwritten bytes bitwise and the registered live/retained typed-state checks.

Preserve the original rejected budget and first fault. Persist the fresh actual
memory sample and complete copy/temporary/oracle/reserve ledger before refusing
allocation, so estimates are not later presented as first-fault RSS. Fix a
proved observer/reference defect with independent deployed allocator evidence
and complete real-entry regressions; require a new source/output identity and
the affected NPU/model gate. This is adaptation/reference recovery, not evidence
of a paper limitation or permission to raise the resource/numerical threshold.

## Triton JIT globals and masked low-bit conversions

For a nested Triton kernel, Python factory-local names are not sufficient evidence
that JIT can resolve them: inspect the real function globals and execute with the
installed backend. Bind only the qualified language module, rejecting incompatible
rebinding. In the observed Ascend backend, uint32-to-float lowering failed even
though software integer tests passed. For an already-masked2/4-bit code, an
explicit int32 then float32 conversion preserves values0..3/0..15 exactly; do not
cast the packed word before its unsigned shift. Preserve the original rounding
boundaries and validate the full affected NPU matrix on a new source identity.
This is a version-observed repair, not a universal ban on unsigned conversion.

KIVI evidence: `.agents/workstreams/qwen36-damp-ascend-20261006/KIVI_PACKED3_SIGNED_PASS_20261010.json`.
Two compile failures preceded a20-frame/24-row realNPU pass independently consumed
from original logs/raw bytes. That pass covers controlled eager tensors of actual
read length at most257; capacity33792 is not a long-context test. The next useful
step is actual model integration and real-context output validation, not more
unchanged toy passes or a premature paper/performance success claim.

# Root-cause classification must select the next experiment

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
fixture/import/controller defects. Under the user's current explicit permission,
independent numerical/preparation jobs may use disjoint physical4/5/6/7 under
one MAIN-coordinated ownership and summed CPU/RAM/disk ledger. Preserve foreign
occupation checks; a frozen controller demanding other cards idle cannot be
made concurrency-compatible by verbal permission alone. Freeze/review a new
controller/grouping before launch; never mutate a live source or identity.

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
Check current concurrency text has no stale cross-paper serial-only restriction.
Documentation validation never grants native/model/performance/task acceptance.

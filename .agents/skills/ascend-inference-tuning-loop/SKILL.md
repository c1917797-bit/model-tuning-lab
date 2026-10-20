---
name: ascend-inference-tuning-loop
description: Use for every Ascend NPU inference optimization from hypothesis through baseline, implementation, measurement, decision, rollback, and learning; preserve successful and failed stages as pushed Git history.
---

# Ascend Inference Tuning Loop

## Purpose

Turn tuning into a cumulative flywheel:

```text
orient -> hypothesize -> baseline -> change -> verify -> measure -> decide
   ^                                                           |
   +---------------- record, learn, and select next loop <------+
```

Success, regression, failure, and inconclusive evidence are all useful when
their conditions and decisions are reproducible.

## Four-question execution contract

Before a new launch, after a terminal event, at an authorized periodic resource
audit, and before upgrading any result, read and apply the relevant rules below. Practice source: the user's Oct9
request to make utilization, validity, attribution and smoke-first execution
durable rather than dependent on chat memory.

- Effective card use: [portfolio admission](references/portfolio-preparation-and-serial-admission.md),
  especially CURRENT/NEXT/BACKUP; count executable successors and useful
  evidence, not source deliveries or artificial occupancy.
- Valid success: [the validation DAG and matched controls](references/paper-validation-dag-and-matched-controls.md);
  no stage may borrow a later stage's PASS or another algorithm's evidence.
- Failure and route selection: [causal recovery](references/failure-root-cause-and-next-action.md);
  preserve first fault, classify with confidence, and choose a bounded repair,
  diagnostic, measured-configuration closure or advance within the fixed clock.
- Early feedback: the smoke-first section of causal recovery; preregister
  production-relevant smoke before full gates, without weakening final coverage.

Each stage decision must leave its successor entry, evidence prerequisites,
owner, remaining budget and missing gates in the active workstream. Skill
validation or a policy update is not an algorithm acceptance result.

## Experiment Contract

For mechanism comprehension, hardware mapping, numerical diagnosis or a new
paper adaptation, use the scoped [AI Infra / Ascend knowledge base](../../../docs/knowledge-base/ascend-infra/INDEX.md).
Read only the module needed for the decision. Produce the actual model/path,
mathematical invariants, adaptable seams, competing failure hypotheses and a
discriminating experiment before changing the candidate. Distinguish source
facts, derivations, measured cases and pending hypotheses; knowledge-base tests
are not NPU or model acceptance. Promote reusable evidence-backed cases at
coherent stages, not every polling tick.

Before ranking or resuming papers, apply
[architecture and bottleneck selection](references/architecture-and-bottleneck-selection.md).
Bind the installed hybrid-model stages and actual hardware execution costs;
official code, publication year and previous adaptation effort do not establish
local end-to-end opportunity. Keep unresolved opportunities as bounded diagnostics.

Use one ID such as `exp-YYYYMMDD-short-name`, one `work/*` branch, and one
`.agents/experiments/<id>.yaml` record. Declare before implementation:

- objective and bottleneck hypothesis;
- model, workload, hardware, framework, and source identities;
- one primary variable to change;
- correctness guardrails;
- acceptance, regression, abort, and resource thresholds;
- benchmark commands, repetitions, and artifact destinations;
- rollback and cleanup commands.

## Stage Checkpoints

Commit and immediately push each coherent stage:

1. `planned`: hypothesis, scope, metrics, thresholds, and rollback.
2. `baselined`: current environment and repeated baseline measurements.
3. `attempted`: one bounded implementation or configuration change.
4. `verified`: correctness and target-device checks.
5. `measured`: raw-artifact hashes plus summarized comparable results.
6. `decided`: accepted, rejected, inconclusive, or failed, with reasons.
7. `recovered`: if needed, revert or disable failed code and prove the final
   branch tree is safe while retaining prior commits.

Do not squash, amend, force-push, or delete negative-result history. A failed
attempt may remain as an intermediate workstream commit; it must not remain
active in the final tree merged to `main`.

## Decision Rules

- `accepted`: correctness passes and predeclared performance/resource
  thresholds are met across comparable repetitions.
- `rejected`: measurement is valid but thresholds are not met.
- `inconclusive`: evidence is insufficient or conditions are not comparable.
- `failed`: implementation, runtime, correctness, or safety gate failed.

Never relabel an inconclusive run as a regression or improvement. Select the
next loop from evidence, not from an unrecorded intuition.
Before selecting a successor after any failure, apply
[root-cause classification and next-action recovery](references/failure-root-cause-and-next-action.md).
A proved adaptation defect requires repair and regression, not paper rejection;
unknown causes require discriminating evidence and remain inconclusive.

When the user permits combined techniques, apply the performance target to the
final combination, not automatically to every component. Retain a correctly
verified, repeatable sub-target gain as a component candidate; historical
single-technique promotion thresholds still describe their old experiments.
Preregister a new combination ticket and matched dense/A/B/A+B measurements.
Do not sum speedup percentages. Audit cache ownership, graph keys, lifetime,
allocation and numerical interactions before combining hooks; revalidate the
combined implementation and final task quality, even when A and B passed alone.
No component or combination is accepted without its actual required evidence.

## Ready-before-resource execution rule

Maintainer instruction2026-10-06: prepare the next algorithm migration while
resources are unavailable or the current experiment runs; dispatch a complete
source-reviewed validation matrix promptly after admission, not a placeholder
load. This rule does not guarantee the first real-device attempt will pass.

- Keep a ranked ready queue. Each packet names the algorithm-specific seam,
  immutable dependencies, independent oracle, full numerical/slot/graph matrix,
  matched E2E and task gates, exact commands, new output roots and failure policy.
- Complete all safe device-independent checks first: syntax/import, software
  contracts, no-device compile, defined export/dlopen/schema/Meta, actual receipt
  format compatibility, CLI argument paths and source pins. Do not discover a
  known missing schema field, smoke-only plan admission or batch restriction
  for the first time after reserving scarce cards. Unrun prerequisites remain
  explicitly pending, never fabricated to mark a packet ready.
- Test real CLI/aggregate entry points and the fresh-clone transitive source
  closure, not only helper mocks.
  Use the exact delivered interpreter flags (including -I when specified) in
  fresh-process default-OFF and negative-admission tests. A helper imported
  after the test runner changes sys.path cannot prove standalone CLI imports.
  Before device reservation, execute the real source/admission path in a
  same-image no-device container with exact read-only transitive source and
  immutable-evidence mounts. Host imports alone do not prove container path
  visibility; validate destination coverage and reject writable overlap.
  Old failed/software snapshots are historical
  evidence, not current source manifests; retain them without rewriting pins.
  Distinguish static prerequisites from genuine hardware-dependent imports.
  In this pinned stack a full runner import may query HAL/Triton architecture:
  do not fabricate CPU architecture stubs or call that a paper no-go. Move only
  that evidenced dependency into the first admitted real-device source/ABI
  stage before model allocation, preserving all static/source checks.
  Check required plugin names in their actual platform/general entrypoint groups,
  not one invented group. Reuse SHA-verified valid child results when a parent
  predicate fails; correct only that predicate without relabelling the old exit.
- Before scarce-card reservation, check the actual cross-stage handoffs:
  numerical producer -> model launcher -> paired comparator. A new report
  schema or host absolute Ref needs an explicit consumer and inspected mounts,
  not fabricated legacy PASS. Bind and interpret actual Python/NPU ownership
  separately from a prelaunch waiting PID or tiny canary. Helper-test PASS may
  coexist with a proven model-entrypoint gap; retain that gap as preparation
  pending rather than an algorithm failure or end-to-end readiness.
- Check actual engine/cgroup CPU capacity before create; threads are not CPU
  quota. Admit concurrent jobs against ONE summed RAM/CPU/workspace budget plus
  the unchanged reserve. Separate per-job checks cannot admit their combination.
  Prove no-device CPU fitting avoids device-backend autoload using the supported
  pinned-stack mechanism; an import canary is not actual fitting or NPU evidence.
- MAIN alone admits and launches device jobs. Prove fresh physical mapping,
  actual process/HBM usage, aggregate host-RAM/disk/cgroup limits and source
  identities. Device declarations do not prove occupation; idle accelerators
  do not authorize lowering resource gates or reclaiming protected workloads.
- Respect the latest explicit concurrency authority recorded in the active
  window, not an older serial-only template. MAIN serializes admission and owns
  physical-device leases; that does not require all independent correctness
  stages to execute serially. Disjoint concurrency requires explicit authority,
  compatible reviewed controllers, exact mappings and ONE summed resource
  budget. Preparers never self-admit devices. A frozen four-card matrix is one
  lease; TP4/model/profiling/formal paired timing remains exclusive. Overlapping
  timing is not comparable. An unknown exit or release keeps its lease reserved.
- Parallel agents prepare the next gates/adapters during a running job, with
  frozen live sources and distinct edit scopes. Observe terminal exit, retain
  evidence/release only owned resources, then dispatch the admitted successor
  without waiting for report prose. Preserve proven OFF/calibration artifacts
  when only a missing arm is needed; never repeat expensive valid work blindly.
  Check the actual agent status before replenishing work: a message-only call
  does not restart a completed or errored preparer. Use the execution-triggering
  follow-up, then verify it is running. If capacity prevents continuation, retain
  its existing files and transfer the missing narrow gate to an available owner;
  do not count queued messages or a source delivery as active preparation.
- Separate preparer completion from device dispatch: completing an independent
  preparation node submits artifacts for MAIN review and queueing, not permission
  to launch. Reassign its agent to another independent preparation node without
  waiting for card availability. A dependent repair or downstream gate waits for
  its actual predecessor evidence; MAIN alone dispatches a qualified ready node
  after fresh resource admission and verified release of overlapping leases.
- A real-device failure retains the first raw-before/exception/nullable-after
  and has a scoped implementation diagnosis. No unchanged deterministic retry,
  relaxed threshold, fake padded batch, dummy utilization or paper-wide no-go
  from source/CPU-only evidence. Report idle time with its concrete blocker.
- Review throughput of evidence, not card occupancy alone: track admission and
  terminal times, real per-card compute ownership, ready-queue gaps and the next
  bottleneck toward E2E acceptance. Update short goals against medium/long goals
  and the fixed per-paper/portfolio deadline after every stage.
- Balance correctness shards by estimated oracle/native-call, transfer and CPU
  costs, not just equal case counts. Pre-register complete coverage and each
  source-bound group before launch. A frozen live grouping is not silently
  reordered or restarted to hide tail waiting; use its measured progress to
  design the next packet. Separate lightweight no-device preflight budgets from
  model budgets, while preserving the full model's admission and reserve gates.

## Adaptive phase scheduling

Treat each paper as a dependency DAG, not a card reservation held until the
paper finishes. On a terminal/release event, replenish preparation work and
admit the next ready node without waiting for report prose. A failed node goes
to bounded device-free repair; it does not block another paper's ready node.

Among source- and gate-qualified nodes, prefer the next end-to-end acceptance
edge with the smallest remaining critical path; break ties by deadline slack,
waiting age and bounded phase duration. Pack compatible disjoint correctness
nodes against physical devices and summed RAM/CPU/disk limits plus the unchanged
reserve. Once a four-card comparison is ready, reserve its earliest safe start;
backfill only work whose full budget and cleanup cannot delay that reservation.
Do not duplicate a complete case merely to fill the fourth card.

Improve this policy during the active campaign, not by repeatedly restating it:
use measured stage durations, ready-to-start delay, handoff defects and useful
validation completions. Attribute idle gaps to preparation, admission, resource,
release, controller or unavailable evidence; change the responsible component.
Evaluate the next comparable cycle before claiming an improvement. Missing
continuous telemetry means utilization is unmeasured. Freeze live tickets;
scheduling/controller fixes create new versions and preserve failed evidence.
Keep the workstream's CURRENT/NEXT/BACKUP ledger current at stage transitions;
persist reusable skill changes at coherent milestones, not every polling tick.

Treat idle HBM as a versioned environment observation, not a permanent exact
snapshot or arbitrary lower bound. After a host restart, recheck health, compute
processes, device FD ownership, utilization and the justified memory ceiling;
repair a proved admission false-negative without relaxing numerical gates.
Bind operation continuity to the target, boot/session, source and command.
After an interrupted mutation, inspect actual bytes or owned process state
before resuming; a reused operation number is not proof of the previous run.

## Git and Artifact Rules

- Commit small configuration, code, summaries, commands, and checksums.
  When relocating a patch, rewrite only its file-header paths; never replace
  path prefixes across the patch body. Verify deployed bytes against the
  reviewed source before execution; a successful patch response is not a
  source-identity check. Distinguish transport success from nested action errors.
- Keep datasets, weights, checkpoints, traces, dumps, and large logs outside
  Git; reference immutable hashes and controlled locations.
- Push every stage to the current workstream branch.
- Merge the completed branch non-fast-forward so intermediate learning remains
  reachable from `main`.

## Verification

- The experiment record advances monotonically through named stages.
- Every result points to the exact code and environment commits.
- All outcomes include a reason and next-loop recommendation.
- Failed active changes are recovered before integration.
- Local branch equals its upstream after every stage checkpoint.
- After changing code mounted into a reusable container, prove the imported
  module realpath and source identity in every relevant process. Restarting a
  container is insufficient when startup copies into a persistent directory:
  use a fresh container or a non-nesting replacement such as `cp -aT`, then
  re-record module paths and hashes before spending an NPU validation run.

For a multi-paper queue with parallel preparers, apply
[portfolio preparation and serialized admission](references/portfolio-preparation-and-serial-admission.md).
It distinguishes executable readiness from source screens and prevents a
single active paper from consuming every preparation slot.

Before scheduling a prepared paper or comparing its speedup, apply
[the paper validation DAG and matched dense controls](references/paper-validation-dag-and-matched-controls.md).
It defines actual predecessor/consumer edges, data-dependent capture branches,
the only-paper-delta OFF/ON contract, and scoped failure/recovery paths.
An authored packet, canary or software PASS does not satisfy later gates.

For packed recurrent-state ports, also apply the evidence-backed
[DAMP migration gates](references/damp-migration-gates.md): native tokenizer
and plugin registration, static versus device-dependent preflight, untouched
slot preservation, and prepack-versus-quantization failure attribution.

For deferred-state GDN failures or copy-only observation kernels, read
[KVBuffer numerical diagnostics](references/kvbuffer-numerical-diagnostics.md):
native ABI versus FP32 proxies, production anchors, failed-build retention,
actual receipt consumers, card attribution, and ordinary/HugeTLB memory ledgers.

For RSS observer first-identity/exit races or child reports that change during cleanup,
read [controller observation and quiescent results](references/controller-observation-and-quiescent-results.md).
Keep controller failure distinct from algorithm failure; freeze Refs after writers stop.
The same reference covers thread-list lifetime fences and short-lived admission
evidence. For relocated selector/oracle regression contracts, use the ranking
reference below before any new native admission; preserve original failures.

For almost-tied token support, mixed-dtype packed-view persistence, or an
unjustified CPU template, read [ranking and packed snapshots](references/ranking-and-packed-snapshots.md).
Keep the failed run intact; a diagnostic hypothesis is not a revised acceptance gate.

## Live E2E admission and evidence ladder

Use this section whenever a source bundle is repaired, an authorization window
is renewed, or a full-model Ascend run is started after a failed gate.

1. Bind the exact current authorization identity (batch ID, start/cutoff,
   resource scope) to the successor source, controller/worker gates, command
   records, and a fresh unique output root. Refresh every manifest/readset and
   inverse-edit ledger affected by the change. A valid hash/readset audit is
   necessary but does not prove that every nested runtime gate was updated.
2. Keep old batches immutable. Never reuse a prior output path or overwrite a
   terminal receipt. A retry gets a new source root and a new output root.
3. Run the same-image software suite before device admission. Fix source,
   contract, or provenance mismatches at their owning layer; do not weaken
   numerical assertions or edit tests merely to force a green suite. Update a
   test only when the intended invariant genuinely changed, and retain
   historical algorithm/reference checks.
4. Treat these as distinct gates, in order: source audit; same-image software
   preflight; physical-device admission; native model load; real HTTP/request
   smoke; numerical and state correctness; task quality; matched performance
   and resource measurements. A pass at one level cannot be promoted to a
   later level.
5. For Ascend proof, combine a fresh npu-smi snapshot with the exact container
   device mappings, container/process state, and per-rank receipts. A software
   report with Devices=[] is explicitly device-free and is not NPU evidence.
   Host-side NPU telemetry or container existence alone is not enough.
6. Interpret model-load receipts narrowly. A receipt that identifies the
   unmodified native MTP class, says BOLE=false, and forward_modified=false
   proves that the native loader ran; it does not prove the paper adaptation
   is active, numerically correct, or accepted. Require the registered
   algorithm-specific consumer and real request/numerical gates.
7. Before retrying a long operation after a control-plane timeout, poll the
   original operation and inspect the exact host/container process and output
   milestones. A retryable AWMCP transport timeout is not proof the remote
   process failed. Never launch a duplicate while the original owned server,
   worker, or cleanup is still active.
8. If a client fails on an ancillary command or admission utility, preserve its
   terminal receipt and stderr, identify which process issued the command, and
   classify the failure at that boundary. Do not call it a model numerical
   failure without a model response; do not call it a successful smoke without
   the actual HTTP result.

Verification for this ladder: record the source/output refs and hashes, exact
authorization batch, target peer, container image digest, CANN/framework
versions, physical device mapping, per-rank receipts, client terminal result,
and cleanup receipt. Keep model readiness, algorithm qualification, task
quality, and performance as separate fields; leave each unobserved gate
pending rather than inferring it from a neighbouring pass.


## BOLE/GDN: saved-input recovery and bounded service qualification

For precision-boundary diagnosis, saved-consumer recovery, hook installation
order, dynamic backend provenance, or short-service evidence, read
[saved-input diagnosis and bounded BOLE qualification](references/bole-saved-input-and-service-qualification.md).
It retains the earlier failed entry and the later component/service successes
with their different source identities. Neither history nor a short-request
PASS replaces the missing production-control, long-output, task and formal
performance gates. Use the latest explicit task contract for new experiments.

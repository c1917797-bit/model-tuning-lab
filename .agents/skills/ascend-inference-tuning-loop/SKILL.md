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

## Experiment Contract

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
- MAIN alone admits and launches device jobs. Prove fresh physical mapping,
  actual process/HBM usage, aggregate host-RAM/disk/cgroup limits and source
  identities. Device declarations do not prove occupation; idle accelerators
  do not authorize lowering resource gates or reclaiming protected workloads.
- Independent correctness-only jobs may use disjoint authorized cards in
  parallel when project safety contracts allow; all TP4 model/calibration and
  formal performance/profiling measurements remain exclusive. Never publish
  timing collected with overlapping experiments as a comparable speedup.
- Parallel agents prepare the next gates/adapters during a running job, with
  frozen live sources and distinct edit scopes. Observe terminal exit, retain
  evidence/release only owned resources, then dispatch the admitted successor
  without waiting for report prose. Preserve proven OFF/calibration artifacts
  when only a missing arm is needed; never repeat expensive valid work blindly.
- A real-device failure retains the first raw-before/exception/nullable-after
  and has a scoped implementation diagnosis. No unchanged deterministic retry,
  relaxed threshold, fake padded batch, dummy utilization or paper-wide no-go
  from source/CPU-only evidence. Report idle time with its concrete blocker.
- Review throughput of evidence, not card occupancy alone: track admission and
  terminal times, real per-card compute ownership, ready-queue gaps and the next
  bottleneck toward E2E acceptance. Update short goals against medium/long goals
  and the fixed per-paper/portfolio deadline after every stage.

## Git and Artifact Rules

- Commit small configuration, code, summaries, commands, and checksums.
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

For packed recurrent-state ports, also apply the evidence-backed
[DAMP migration gates](references/damp-migration-gates.md): native tokenizer
and plugin registration, static versus device-dependent preflight, untouched
slot preservation, and prepack-versus-quantization failure attribution.

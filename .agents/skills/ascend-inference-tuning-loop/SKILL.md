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

## Opportunity and mechanism admission

Before implementation, quantify why the proposed seam can close a meaningful
part of the declared target gap:

- use exclusive or non-overlapped wall time when available; summed durations
  from overlapping streams are only hotspot-ranking evidence;
- record the affected call count, shapes, execution phase, and the fraction of
  service work the candidate can actually cover;
- estimate an optimistic E2E bound. If perfect removal of the measured cost
  cannot reach the next milestone, reject or redirect the candidate unless it
  unlocks a named, separately testable downstream benefit;
- state whether the change is a diagnostic or a treatment. A diagnostic may
  accept or reject a hypothesis, but its timing is not an optimization result.

Verify the mechanism against the exact pinned image and live import path before
editing. A historical checkout, similarly named class, test stub, or old source
map is not proof of the runtime object used by the service.

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

## Closed routes and successor experiments

For every rejected or failed route, record the exact code/configuration hash,
first observed failure phase, logs or markers that localize it, and cleanup
result. Do not rerun unchanged bytes after a deterministic failure.

A successor must change a material hypothesis or implementation and add a
bounded test that targets the recorded failure phase. Fixing a visible defect
does not establish root cause until the failure phase or measured outcome
changes. Keep the old route closed when a fix leaves the original stall,
timeout, correctness failure, or performance result unchanged.

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
- Every admitted candidate has a recorded E2E opportunity bound and real
  runtime-path proof.
- All outcomes include a reason and next-loop recommendation.
- Rejected and failed routes identify the exact bytes and evidence required for
  any materially different successor.
- Failed active changes are recovered before integration.
- Local branch equals its upstream after every stage checkpoint.

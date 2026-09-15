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

## State-cache algorithm piercing gate

For algorithms that claim gains by reducing recurrent or prefix state:

- First prove the plugin reaches the real checkpoint save/restore path on every
  TP rank and expected layer; an API success or model-level hook is not enough.
- Separate a numerical canary from a performance implementation. A canary that
  masks a dense state proves semantics/reachability but cannot claim memory,
  capacity, TTFT, or throughput gains.
- Measure physical allocation and page geometry. Framework page balancing or
  alignment can erase theoretical state savings.
- Run an explicit plugin-disabled control with identical model, devices,
  cache mode, eager/graph mode, prompt tokens, cache-hit tokens, and decoding
  settings.
- Treat first-request latency as warm-up evidence only. Use repeated
  steady-state cache reuse for performance decisions.
- A canary that is slower is still useful if it closes the execution-path
  uncertainty; record it as a negative performance result and move to the
  missing physical representation rather than tuning the canary.
- Treat every state family sharing scheduler indices as one transaction. For
  GDN this means temporal and convolution state must use the same active-slot
  remap, prefix block copy, validity propagation, and invalidation boundary;
  changing only the pruned tensor can silently combine states from different
  requests.
- Keep persistent checkpoint storage separate from fixed-address dense active
  workspaces when the native operator ABI is dense. Prove restore, compute,
  checkpoint, prefix-copy, abort, and invalidation lifecycles before changing
  framework page accounting or claiming physical savings.
- When state geometry is derived from TP-sharded weights, synchronize the
  per-layer geometry before vLLM cache-spec collection. Rank-local indices may
  differ, but every worker must advertise the same page shape for a layer.
  Prefer a layerwise collective MAX count and pad each rank with its next most
  important local states; a global maximum across all layers destroys useful
  heterogeneity. Treat cross-worker cache-spec merge as a hard runtime gate and
  cover it before another service launch.
- In hybrid attention/Mamba models, equal TP geometry is necessary but not
  sufficient. Per-layer compact Mamba pages can still fail vLLM's global
  page-divisibility gate. Do not pad every compact layer back to the dense
  maximum and call that physical reduction. In Mamba align mode, represent
  attention plus heterogeneous Mamba layers as one token-lifecycle group whose
  aggregate page is the sum of exact inner pages, and fail closed for cache
  families whose lifecycle equivalence has not been proved.
- Preserve the model-provided inner-layer order when synthesizing an aggregate
  hybrid cache group. Some runners dispatch group-wide block-table and slot
  mapping behavior from the first inner spec; sorting attention before Mamba
  can silently change execution semantics even when page accounting remains
  numerically correct. Lock order preservation with a regression test and a
  same-config plugin-disabled service control.
- Recheck accelerator ownership and free memory at worker initialization, not
  only immediately before launching a container. Another container can claim
  devices in the startup gap. Attribute every conflicting PID through its
  cgroup/container identity, never stop an unowned workload, and classify a
  resource-collision run as inconclusive rather than an algorithm failure.

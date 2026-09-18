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

- Use a one-variable correctness ladder before restoring compression:
  plugin-disabled dense control, all-state native control, all-state bridge
  control, lifecycle-branch coverage, physical-row/metadata binding, and only
  then the pruned candidate. Give every rung a new immutable artifact root and
  close it with an explicit decision; do not change pruning and lifecycle
  mechanics in the same diagnostic.
- Derive the expected layer and state-family inventory from the exact pinned
  checkpoint configuration, then cross-check it against the generated
  selector/plan manifest and live worker activation. Treat architecture counts
  quoted by a paper or a related checkpoint as context only. Fail before an
  accelerator launch when these inventories disagree, and retain the
  checkpoint and manifest hashes with the decision.
- Split launch admission into deterministic and volatile phases. Validate the
  pinned checkpoint, selector/plan, source identities, ordered inventories, and
  output-root policy first without touching the accelerator. Then re-sample
  device ownership, memory, ports, and foreign containers immediately before
  launch. A volatile resource rejection may prove software readiness only; it
  is not target-device activation, numerical, performance, or quality
  evidence.
- Make trace coverage a Cartesian-product gate, not a collection of independent
  membership checks. For every required TP rank, state family/index, and
  representative layer, require one uniquely keyed copy, before-native, and
  after-native event; compare those key sets exactly and reject duplicate-key
  collapse. Seeing every rank, state, and layer somewhere can still omit a
  required combination.
- Treat scheduler flags, branch counters, cache-hit deltas, state-copy events,
  and HTTP success as reachability evidence only. They do not override a failed
  exact repeated-replay canary. Performance and E2E quality remain prohibited
  until the all-state path meets the declared token- or logit-equality contract
  across repeated cache-hit resumes.
- When state moves from one physical row to another, prove the native operator
  consumes and updates the destination row: hash the complete representative
  rows before copy, after copy, immediately before native execution, and after
  execution; require the source row to remain unchanged and the destination row
  to change on every TP rank. Sampled elements, pointer stability, or a copy
  count alone cannot prove row identity.
- Keep graph-captured metadata buffers at stable addresses while changing their
  values outside replay. If an all-state control still diverges, classify it as
  an integration-correctness failure and localize the next operator boundary;
  do not tune retention, benchmark the candidate, or reject the paper.
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
- Do not accept a compact cache-spec or reported page size as proof of physical
  allocation savings. After the framework allocator binds the real tensors,
  fail closed unless their exact storage bytes equal compact page bytes times
  the allocated block count; record both actual and expected values before any
  performance claim.
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
- Audit worker cache configuration and the scheduler's derived cache
  configuration as separate runtime objects. A scheduler reducer may replace a
  heterogeneous aggregate with one representative inner spec: manager
  selection can remain correct while recurrent-state split/zeroing flags are
  silently lost. Preserve manager type and lifecycle flags as independent
  invariants. When a consumer imports the reducer by value, patch the defining
  module first; patch an already-loaded alias only after proving object
  identity, defer when the consumer is not loaded, and fail closed on a
  detached alias.
- Preserve the model-provided storage/layer order when synthesizing an
  aggregate hybrid cache group, but never treat that order as a valid
  group-wide execution-dispatch contract. Some runners infer block-table and
  slot-mapping behavior from the first inner spec under a same-type assumption;
  a mixed attention/Mamba aggregate violates that assumption whether attention
  or Mamba comes first. Adapt runner dispatch explicitly: derive attention slot
  mapping from an `AttentionSpec`, filter Mamba copy/invalidation to the
  Mamba members, and leave authoritative cache order unchanged. Lock all three
  invariants with regression tests and require target-device graph-capture
  evidence before treating the adapter as correct.
- Instrument the actual first inner spec and the derived dispatch before
  changing hybrid-group order. If the live group already selects attention and
  the same graph/operator failure persists, close the first-spec hypothesis;
  do not keep permuting dictionaries. Audit every remaining consumer of the
  synthetic outer spec because a same-type wrapper around mixed inner specs can
  violate assumptions beyond the initial dispatch branch.
- Treat recurrent-state virtualization as a graph-boundary design problem, not
  only a storage-layout problem. A plugin that allocates new index tensors or
  swaps module cache/metadata objects inside every forward may pass eager
  numerical tests yet be invalid for ACL graph replay. Keep scheduler-owned
  compact storage authoritative, bind the native operator once to fixed-address
  dense active workspaces, prepare global-to-local state indices before the
  captured model call, and checkpoint after replay. Lock tensor pointers and
  object identity with regression tests before spending another multi-NPU run.
- When a historical control has an empty result directory, inspect any retained
  stopped container before rerunning expensive accelerator work. Recover and
  hash only evidence the container can actually prove: image, command, mounts,
  device mapping, graph-capture completion, readiness, replay, and HTTP status.
  A server-side HTTP 200 log does not prove the client response body; withdraw
  exact-output claims unless the response artifact itself is retained.
- Recheck accelerator ownership and free memory at worker initialization, not
  only immediately before launching a container. Another container can claim
  devices in the startup gap. Attribute every conflicting PID through its
  cgroup/container identity, never stop an unowned workload, and classify a
  resource-collision run as inconclusive rather than an algorithm failure.
- Keep the ownership evidence layers separate: a live container device mapping
  is a reservation/overlap signal, a device-side PID proves active execution,
  and HBM measures allocation. Under an exclusive-use contract, any foreign
  overlapping mapping is a launch blocker even when no NPU PID is present; do
  not describe that idle mapping as active compute, and do not weaken the gate
  merely to consume apparently free memory.
- Hardware-free validation may continue while an accelerator lane is occupied
  only when the validation container is non-privileged, maps no accelerator
  devices, uses read-only source/input mounts, and does not contend for the
  owned service port. Record it as pinned-software evidence only; it cannot
  satisfy target-device activation, numerical, performance, or quality gates.
- Do not implement the container-claim gate from HostConfig.Devices alone.
  Privileged Ascend containers can expose no explicit Docker device mappings
  while selecting host-physical devices through ASCEND_RT_VISIBLE_DEVICES.
  For non-privileged containers, explicit PathOnHost mappings are physical
  authority even when devices are renumbered inside; for privileged containers,
  conservatively union explicit mappings with valid visible-device claims.
  Cover both forms and their mixed case with parser regression tests.
- If the operator explicitly authorizes a narrow experiment to coexist with
  idle foreign declarations, record that exception in the owning workstream
  rather than weakening the repository default. Keep device-side processes,
  HBM, port, and immutable-output checks as hard blockers, and repeat the live
  resource check immediately before container launch after preparation work.

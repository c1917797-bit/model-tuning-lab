---
name: ascend-inference-tuning-loop
description: Use for every Ascend NPU inference optimization from hypothesis through baseline, implementation, measurement, decision, rollback, and learning; preserve successful and failed stages as pushed Git history.
---

# Ascend Inference Tuning Loop

## Purpose

Turn tuning into a cumulative flywheel:

~~~text
goal chain -> orient real path -> hypothesize -> baseline -> change
    ^            -> verify by layer -> measure -> decide -> learn |
    +-------------------------------------------------------------+
~~~

Success, regression, failure, and inconclusive evidence are all useful when
their conditions and decisions are reproducible.

## Experiment Contract

Use one ID such as `exp-YYYYMMDD-short-name`, one `work/*` branch, and one
`.agents/experiments/<id>.yaml` record. Declare before implementation:

- objective and bottleneck hypothesis;
- the fixed long-term acceptance gap, medium-term candidate decision, and why
  this short experiment can change it;
- model, workload, hardware, framework, and source identities;
- the expected execution path and how the actual loaded source, library,
  operator, or graph path will be proved;
- one primary variable to change;
- correctness guardrails;
- acceptance, regression, abort, and resource thresholds;
- benchmark commands, repetitions, and artifact destinations;
- rollback and cleanup commands.

## Ordered evidence ladder

Use the cheapest sufficient gate, but never skip upward:

1. **Orientation and identity**: prove devices, container, source revisions,
   runtime path, and actually loaded implementations.
2. **Local/ABI semantics**: shape, layout, bounds, storage, dispatch, and
   reference behavior. This admits target-runtime testing only.
3. **Target-NPU numerical behavior**: representative edge shapes, multi-step
   mutable state, graph replay when relevant, finite outputs, and predeclared
   equality or error tolerances.
4. **Integrated service path**: prove that the real framework/cache/scheduler
   path uses the candidate; an isolated operator probe is insufficient.
5. **Paired end-to-end screen**: candidate versus a contemporaneous dense or
   unmodified control with the same common optimizations.
6. **Repeated performance acceptance**: fixed protocol, raw artifacts,
   dispersion, throughput and latency decomposition.
7. **Task-quality and portability acceptance**: the same admitted candidate,
   final quality protocol, and environment-specific paired baselines.

Each stage records its evidence_level and claim_ceiling. Kernel-time sums,
energy proxies, CPU tests, ABI probes, and operator microbenchmarks are useful
diagnostics but are not end-to-end speedup. No-NaN/Inf is not sufficient
numerical correctness for stateful operators. Pure storage transformations may
require bitwise parity; arithmetic/fusion changes require justified tolerances
and multi-step state comparison.

Portability starts at design time: separate algorithm semantics from physical
alignment, padding, tiling, chip, compiler, and runtime dispatch assumptions.
Record the saved and added compute, memory, communication, and data movement,
plus conditions where benefit disappears. Later cross-environment measurements
verify that contract; they do not replace it.

## Stage Checkpoints

Commit and immediately push each coherent stage:

1. `planned`: hypothesis, scope, metrics, thresholds, and rollback.
2. `baselined`: current environment and repeated baseline measurements.
3. `attempted`: one bounded implementation or configuration change.
4. `verified`: correctness and target-device checks.
5. `measured`: raw-artifact hashes plus summarized comparable results.
6. decided: accepted, rejected, inconclusive, failed, or invalid, with reasons
   and the exact scope of the claim.
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
- invalid: the executed path, source identity, comparison, or measurement
  protocol was disproved or non-comparable. Preserve the finding, but do not
  use it as positive or negative evidence about the algorithm.

Never relabel an inconclusive run as a regression or improvement. Select the
next loop from evidence, not from an unrecorded intuition.

A rejection eliminates only the tested configuration unless the experiment was
predeclared and powered to support a broader claim. A low-layer success promotes
only to the next gate. General optimizations must be applied equally to the
paired control; otherwise the delta cannot be attributed to the candidate.
When a former conclusion is disproved, mark it superseded and retain both the
historical record and correction.

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
- Actual runtime identity is proved before interpreting operator behavior.
- Evidence level and claim ceiling match; lower-layer checks are not reported
  as end-to-end, quality, or portability acceptance.
- Invalid results are preserved but excluded from algorithm trend claims.
- Failed active changes are recovered before integration.
- Local branch equals its upstream after every stage checkpoint.

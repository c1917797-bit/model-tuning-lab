# Paper-algorithm piercing lessons

Read this reference when an Ascend tuning loop implements or adapts an
algorithm from a paper. Keep machine-specific commands, dimensions, thresholds,
and artifact paths in the workstream record rather than in this reference.

## Evidence ladder

Treat these as separate gates; evidence at one level does not prove a later
level:

1. **Method parity:** enumerate every paper stage that causally supports speed
   or quality and label it exact, adapted, omitted, or substituted. State
   whether the result is paper-exact, a faithful port, or a derivative.
2. **Runtime identity and activation:** prove the live imported source, version,
   worker dispatch, operator path, and all-rank activation. A flag, import log,
   CPU probe, or similarly named reference implementation is insufficient.
3. **Backend validity:** verify shapes, layouts, alignment, storage offsets,
   graph capture/replay, multi-step state, finite values, and guards on the
   target NPU. Backend-invalid runs are not algorithm evidence.
4. **Physical effect:** prove the intended bytes, cache admission, traffic, or
   compute actually changed. A dense masked or zero-filled representation may
   prove semantics while providing no capacity benefit.
5. **Service performance:** compare the workload the mechanism is meant to
   improve. Cache algorithms require real hit/fill/replay traffic; no-cache
   decode throughput is not their main verdict.
6. **End-task quality:** apply the user-declared E2E task gate. A single tensor,
   token prefix, numerical tolerance, or absence of NaN/Inf cannot substitute
   for GSM8K, LongBench, or the declared task metric.
7. **Portability:** isolate architecture-dependent adapters, derive shapes and
   topology from runtime metadata, fail closed on unknown versions/layouts, and
   test representative boundaries. One environment proves only that frozen
   scope, not universal benefit.

Only time performance after all earlier gates needed by the claim pass. Keep
profiling disabled during clean A/B measurement.

## Successful patterns

- **HYPIC:** success followed a frozen same-denominator A/B with one treatment
  switch, explicit cache-capacity arithmetic, real cache-hit traffic, hot-path
  activation evidence, separate performance and quality semantics, resumable
  per-unit artifacts, and independent hash/count/index audit. The reusable
  lesson is the causal chain, not its absolute gain on one model or topology.
- **DRRQR:** useful progress came from pinning the real Ascend GDN path,
  validating prefill and decode separately, preserving negative results, and
  comparing candidate and dense under the same common optimizations. An aligned
  supported reduced dimension produced a credible but sub-target throughput
  gain; this justified targeted integration work but not adoption.
- **DASC:** the dense-storage numerical canary proved all-rank state-restore
  activation and identical continuations. It correctly served as semantic and
  source-seam evidence even though it regressed latency. Later physical-cache
  attempts advanced one framework boundary at a time: first TP-rank shape
  agreement, then heterogeneous page representation. These are valid mechanism
  advances, not performance or quality results.

## Failure patterns and the rule each adds

- **Paper stage substituted silently:** DRRQR's energy selector was not the
  paper's StrongRRQR selector, its calibration data differed, and the paper's
  training-based recovery was omitted under a no-training constraint. Require
  a method-parity ledger and a feasibility check before expensive NPU work.
- **Backend defect mistaken for algorithm behavior:** non-aligned DRRQR state
  widths crossed padded rows incorrectly in the native recurrent-state path.
  Invalidate those runs; do not infer a pruning-rate trend or relax the guard.
- **Narrow correctness overclaimed:** token-prefix equality, finite tensors, or
  a single operator comparison does not establish E2E quality. Preserve the
  numerical gate, then run the declared task-quality gate independently.
- **Diagnostic timing promoted to E2E gain:** summed kernel durations can
  overlap and cannot be converted directly into throughput. Use them to rank
  hotspots; use service A/B runs for adoption decisions.
- **Semantic prototype mistaken for physical optimization:** DASC zero-filled
  omitted heads inside dense storage and therefore changed restore semantics
  without reducing cache bytes. Reject it as a performance route after it has
  supplied the intended semantic evidence; the successor must change the
  physical representation.
- **Distributed local choice broke a global contract:** independently selected
  DASC head counts yielded different per-layer shapes across TP ranks. Separate
  local indices from globally agreed storage geometry and prove the collective
  agreement before cache allocation.
- **Framework abstraction rejected valid heterogeneity:** heterogeneous Mamba
  pages entered a global page-divisibility path. Fix the exact cache-spec seam,
  retain real inner sizes, and fail closed on unsupported cache types instead
  of padding everything to the dense maximum.
- **Contaminated resources produced invalid evidence:** unexpected users on an
  owned NPU lane make a run incomparable even if it completes. Archive it as an
  invalid attempt, preserve ownership evidence, and rerun only after the full
  lane is demonstrably free; never stop another workload.
- **Unrelated optimization replaced the objective:** MTP or another generally
  useful speedup does not answer whether DRRQR or DASC lands successfully.
  Admit it only as an explicitly separate experiment, not as a successor that
  hides an unproven paper mechanism.

## Successor and stopping rules

Choose the next loop at the earliest broken causal link. A successor is
admissible only when it changes that link materially and adds a bounded test
that would distinguish the new hypothesis from the closed route.

Stop or pivot the current paper route when any of these becomes true:

- user constraints omit a necessary result-bearing paper stage and no faithful
  alternative has a credible quality/performance path;
- a valid upper bound cannot reach the declared E2E milestone;
- repeated comparable service measurements miss the threshold after the
  affected hotspot or physical resource has been verified;
- E2E quality crosses the rejection boundary and the allowed adaptation space
  has no evidence-backed recovery route;
- the next proposal only retunes unchanged bytes after a deterministic failure.

A stopped implementation does not automatically reject the paper. Classify the
decision separately at primitive, operator, service, frozen-workload, and
generalization scope, and record the most valuable next scientific question.

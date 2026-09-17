---
name: ascend-canary-implementation
description: Use to implement the first minimal, one-variable Ascend inference change from a paper-derived hypothesis before scaling to full benchmarks or broad source edits.
---

# Ascend Canary Implementation

## Purpose

Make the smallest safe implementation that can falsify or support a
Paper-to-Ascend hypothesis. A canary is not a final optimization; it is the
first controlled proof that the mechanism can run correctly on the intended
Ascend path.

## Workflow

1. Require a passed or explicitly pending `paper-ingestion`,
   `ascend-architecture-fit`, and `ascend-source-map` note.
2. Work on one `work/*` branch and one experiment record. Commit/push the
   planned state before protected source changes.
3. From inside the pinned serving image, resolve and record the imported module,
   source file, class or function, package version, and source/patch hash used
   by the live service. Do not infer this path from a historical host checkout.
4. Change one primary variable only. Prefer config or existing runtime hooks
   before custom source changes.
5. Run a small deterministic workload first. Prove load, request success,
   output validity, and the intended physical NPU/process execution.
   Treat an idle-device sample as observation, not reservation. Put the final
   occupancy check inside the same controller that performs the launch, after
   any cooperative resource lock and immediately before the first mutation.
   A repository lock coordinates only workflows that honor it; it cannot
   exclude an unrelated container or operator.
6. Emit bounded activation evidence from every relevant worker, rank, or engine
   process. Run the same canary with the mechanism disabled and prove the marker
   disappears while the request still succeeds.
   A restored configuration property is precondition evidence only: when the
   hypothesis depends on a scheduler split, cache zeroing, state copy, or
   restore branch, emit bounded evidence from that branch and validate its
   material inputs/outputs. Do not infer branch execution from a true flag.
   If an early warmup or short request may reach the branch without exercising
   the material condition, record both the first invocation and the first
   materially changed/nonempty invocation. A first-call-only marker can hide
   the later request that the canary is meant to prove.
7. Compare against a tiny baseline under the same environment fingerprint before
   any larger benchmark.
8. If correctness fails, classify the stage as `failed` and recover active code.
9. If correctness passes but performance is unclear, route to profiler or formal
   benchmark rather than expanding the change blindly.
10. Record the canary result, limitations, artifact paths/hashes, and next step.
    Generate the diagnostic verdict even when the primary numerical guard
    fails, without masking that original failure. If verdict or cleanup files
    are written after the base controller creates its artifact manifest,
    regenerate the manifest while excluding the manifest itself.

## Acceptance to scale

Only scale to repeated benchmark when:

- the target mechanism is actually enabled;
- the exact live runtime object and candidate bytes are identified;
- every relevant process emits activation evidence and the disabled control
  does not;
- correctness guardrails pass;
- target NPU execution is proven in the same session;
- the launch controller rechecks live target-device occupancy immediately
  before mutation and records whether the experiment actually crossed its
  start boundary;
- after service readiness, every target-device PID is re-attributed to the
  owned container before the numerical request is sent;
- rollback is known;
- the next benchmark protocol is frozen.

## Boundaries

- Do not combine multiple paper ideas in one canary.
- Do not treat import success or a marker from only the launcher as proof that
  tensor-parallel workers or the engine core executed the change.
- Do not treat a lifecycle/configuration flag as proof that its consuming
  branch executed; require branch-local evidence plus output correctness.
- Do not assume a clean prelaunch sample reserves the devices. Recheck ownership
  after the service has created its workers and fail closed on a missing target
  worker or any foreign target-device PID.
- If a foreign workload appears after an idle preflight but before the owned
  experiment crosses its recorded start boundary, classify the outcome as
  `not_run/resource_race`, not as a candidate or algorithm failure. Preserve
  the exact competing PIDs and container attribution, require the immutable
  result root to remain absent, and allow a later fresh admission attempt only
  with a new control-plane idempotency key. Do not reuse a completed key whose
  cached result is the admission failure.
- Do not use canary success as a performance claim.
- Do not leave failed active code in the final branch tree, even though the
  failed commit/evidence should remain reachable in history.

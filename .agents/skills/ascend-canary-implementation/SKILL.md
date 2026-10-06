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
6. Emit bounded activation evidence from every relevant worker, rank, or engine
   process. Run the same canary with the mechanism disabled and prove the marker
   disappears while the request still succeeds.
7. Compare against a tiny baseline under the same environment fingerprint before
   any larger benchmark.
8. If correctness fails, classify the stage as `failed` and recover active code.
9. If correctness passes but performance is unclear, route to profiler or formal
   benchmark rather than expanding the change blindly.
10. Record the canary result, limitations, artifact paths/hashes, and next step.
11. When a local runtime change survives the canary, use
    `runtime-monkeypatch-delivery` to package it as a removable candidate
    before formal service benchmarking or PR preparation.

## Acceptance to scale

Only scale to repeated benchmark when:

- the target mechanism is actually enabled;
- the exact live runtime object and candidate bytes are identified;
- every relevant process emits activation evidence and the disabled control
  does not;
- correctness guardrails pass;
- target NPU execution is proven in the same session;
- rollback is known;
- the next benchmark protocol is frozen.

## Boundaries

- Do not combine multiple paper ideas in one canary.
- Do not treat import success or a marker from only the launcher as proof that
  tensor-parallel workers or the engine core executed the change.
- Do not use canary success as a performance claim.
- Do not leave failed active code in the final branch tree, even though the
  failed commit/evidence should remain reachable in history.

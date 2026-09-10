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
3. Change one primary variable only. Prefer config or existing runtime hooks
   before custom source changes.
4. Run a small deterministic workload first. Prove load, request success,
   output validity, and the intended physical NPU/process execution.
   For structured dimension or state pruning, replay at least one aligned
   width below and above the current candidate on the same real captured
   trajectories before investing in heterogeneous runtime support. Require a
   monotonic aggregate fidelity curve and retain layer/rank/sequence window
   gates; a passing local curve admits broader sensitivity capture only, not
   endpoint performance or task accuracy. Before implementing a heterogeneous
   budget, solve the complete constrained allocation over every admitted layer:
   the lower-cost width must itself satisfy all local regression gates, and the
   selected map must meet the aggregate gain at the declared total cost. A
   monotonic lower/current/higher curve can still yield no feasible mixed plan
   when every lower-cost layer violates a local gate.
5. Compare against a tiny baseline under the same environment fingerprint before
   any larger benchmark.
6. If correctness fails, classify the stage as `failed` and recover active code.
7. If correctness passes but performance is unclear, route to profiler or formal
   benchmark rather than expanding the change blindly.
8. Record the canary result, limitations, artifact paths/hashes, and next step.

## Acceptance to scale

Only scale to repeated benchmark when:

- the target mechanism is actually enabled;
- correctness guardrails pass;
- target NPU execution is proven in the same session;
- rollback is known;
- the next benchmark protocol is frozen.

## Boundaries

- Do not combine multiple paper ideas in one canary.
- Do not use canary success as a performance claim.
- Do not leave failed active code in the final branch tree, even though the
  failed commit/evidence should remain reachable in history.

# R19 quality-controller gate retrospective — 2026-10-10

This is a read-only attribution of an experiment-harness failure mode, not a
change to the frozen r19 protocol, source, raw root, or quality decision.

## Evidence

- The frozen repaired-source LongBench c32/max-2048 pair completed 127 samples
  and 381 scored responses per arm. The independent paired audit SHA256 is
  `40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b`.
  It verified matched identity, scorer replay, continuous physical NPU0–3
  isolation, and exact owned release. All-request quality was 227/381 control
  versus 219/381 HYPIC-only, `REJECT_OR_QUALIFY`.
- The candidate controller exited 1 *after* completing the rows. In the
  frozen `hotpath_quality_full.py`, its final condition raises
  `candidate scored boundary/hot coverage incomplete` when aggregate
  `verified_hot_requests < scored_rows`. The audit joined 134/381 candidate
  scored requests to four-worker hot events; all 381 had explicit-boundary
  events. Thus this controller exit records a mechanism-coverage shortfall,
  not missing quality rows or a failed resource cleanup.
- `paper-to-ascend-reproduction/SKILL.md` and
  `ascend-model-quality-evaluation/references/quality-test-contract.md`
  require two separate lenses: score every predeclared request for deployment
  quality, and report request-level hot coverage for mechanism attribution.
  Universal per-request proof is required only for a universal hot-path claim.
  The controller's unconditional final raise conflated these lenses. The
  independent auditor correctly retained both the adverse all-request score
  and the failed universal-coverage claim.

## Prospective correction and regression gate

Do not edit or rerun the hash-pinned r19 controller or overwrite its roots.
For a new experiment, version the controller and freeze its hash before use.
After complete scored rows, record boundary coverage and per-request
four-worker hot coverage as distinct fields. A shortfall must fail only the
predeclared mechanism-attribution gate; it must not erase a complete,
independently auditable all-request quality comparison. Test the successor
offline with complete scored rows but partial hot events: expect a terminal
quality receipt, a failed universal-hot receipt, and no adoption-pass claim.
Also test missing rows, identity drift, foreign physical NPU process, and
incomplete exact-owned release as true evidence-invalidating failures.

This is a harness/Skill-execution lesson, not proof that HYPIC is quality-safe
or that the cache churn caused the eight-response net loss. The r19 frozen
negative decision and 134/381 mechanism boundary remain unchanged. No
repaired-source performance benefit or full Skill-chain acceptance follows.

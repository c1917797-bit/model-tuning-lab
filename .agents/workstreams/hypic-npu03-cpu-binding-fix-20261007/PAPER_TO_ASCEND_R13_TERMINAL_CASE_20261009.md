# Paper-to-Ascend HYPIC case — r13 terminal addendum

2026-10-09 UTC. This addendum supersedes the *pending-r13* statements in
`PAPER_TO_ASCEND_REAL_TASK_CASE_20261008.md`; it does not change that
historical report or any immutable experiment root.

## Replay and identity

The exact main Paper-to-Ascend Skill under review is commit
`ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`. The branch-local
`paper-to-ascend-reproduction` Skill changed since its earlier case:
current blob `167d4555bc1f8ffa650d3e8f846a197538ce4a59` separates valid
all-request deployment effects from incomplete conditional hot-path
attribution. `verify_paper_to_ascend_reproduction_case.py` pins and
replays that exact version and the raw terminal audits.

The historical c16/1024 result, natural-EOS clean2 quality, r12 c8 stress,
and r13 c8/cache10 runs are separate identities. Do not pool their scores
or compare cross-identity baselines as one treatment effect.

## Current matched r13 result

- A same-identity 0.85/cache10 no-cache control and HYPIC-only treatment
  completed the explicit-boundary LongBench-v2 127 × 3, max-2048,
  natural-EOS quality ruler on physical NPU0–3. The independent dual audit
  SHA256 is
  `f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b`.
- All-request quality is 230/381 → 219/381, −2.8871 percentage points,
  `REJECT_OR_QUALIFY`. Strict four-worker hot proof covers 368/381, so
  universal mechanism attribution `FAIL`. The 13 cold requests do not
  explain the hot-cohort quality decrease.
- All six matched 40-request fixed-1024 performance phases independently
  audit valid: median weighted TPOT 74.727578 → 58.643006 ms
  (−21.5243%), and all 120 candidate scored performance requests have
  four-worker hot proof. Audit SHA256
  `d8f710f6ccd79ad79a31a36926963eac650761c921924d08b4fb0d2a1a206062`.
  This is a bounded performance success, not a quality pass.
- r14's separate 3-sample c1 diagnostic cannot reclassify the r13 full
  population. Its two arms were each 3/9 correct and candidate hot proof
  was 9/9; concurrency, campaign size/order and cache history were not
  isolated as causes.

## Skill verdict and next gate

The experiment has a terminal, evidence-valid *mixed* result. The
Paper-to-Ascend case remains `partial-evidence`: the applicability
and method-parity review was retrospective; this is a derivative C1/C2
implementation, not paper-exact, upstream exact Git revision and C3
multi-replica path are unproven; the default GSM8K/c32 quality ruler and
short deterministic canary are not covered by r13. Neither six-phase
speed nor the smaller r14 diagnostic can satisfy those missing gates or
justify adoption.

Do not rerun r13/r14 or re-request a matching 0.85 pair; those units are
complete and immutable. First replay
`verify_paper_to_ascend_case.py` and
`verify_paper_to_ascend_reproduction_case.py`, then review the branch
Skill corrections against exact main and validate the *remaining*
method-parity, default-ruler, and integration gates as separate work.
Any new causal device experiment needs its own prospective identity and
matched control. No NPU4–7 or foreign workload is in scope.

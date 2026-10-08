# Main Skill validation goals (active from 2026-10-08)

North star: establish which archived `main` Skills work in real, reproducible
tasks. A structurally valid Skill is not a behaviorally verified Skill. This
branch's HYPIC run is one case, not the entire validation campaign.

## Run-time drift check (2026-10-08)

The long goal is still real-task validation of all 29 main Skills, not a
favorable HYPIC score. The medium HYPIC Skill-chain milestone still needs a
full in-path quality decision and matching performance identity. The cache10
127-sample candidate was invalidated by shared-lane interference after only
1/127 samples; its prior 9-sample/27-row stress remains valid for that
narrower gate. A fresh cache10r1 candidate was also invalidated at 0/127
by a `cannbench_ds` process on physical NPU3. Its prompt guard abort and
exact owned release passed the execution-control repair gate. After a bounded
quiet-lane check, cache10r2 candidate operation `exec-00000000000013ec`
started on physical NPU0-3; at 2026-10-08 13:48 UTC it was live with 20/127
samples persisted. This is progress, not a quality verdict. Keep the exact
operation alive; do not restart or reuse a partial root. If its independent
audit passes and the lane is available, run only the matched 0.85/cache10
control arm. The audited 0.9 no-cache baseline is historical reference, not
that control. A fresh matched performance comparison must likewise use the
0.85/cache10 identity and the prospective ruler in
`HOTPATH_CACHE10_MATCHED_PERFORMANCE_PLAN.md`. Keep per-request worker-hot
attribution open until evidence can join workers to scored request IDs.

## Short term — current HYPIC in-path quality gate

- Frozen context: physical chicaihong01 NPU0-3 only; NPU4-7 and unrelated
  containers untouched. Existing three-repeat C1/C2 performance result and
  clean2 off-path quality evidence remain separate.
- This ruler's 127-sample candidate is active on a single operation handle;
  complete it and independently audit it before starting the matching control.
- Run the 3-sample explicit-boundary pilot, then the new matched 127-sample,
  three-repeat, 2048-max-output LongBench ruler described in
  `HOTPATH_FULL_QUALITY_PLAN.md`.
- Exit gate: independent row/hash/scorer/activation/isolation/release audit,
  declared score classification, and exact permitted/forbidden claims. No
  automatic "pass" from a completed controller or one favorable sample.

## Medium term — validate and repair the HYPIC Skill chain

- Map each actual stage to the relevant `main` Skills, especially host
  maintenance, environment orientation, Paper-to-Ascend reproduction,
  benchmark evidence, model-quality evaluation, runtime delivery, and
  reporting.
- For each Skill record the exercised instruction, evidence, outcome,
  counterexample, and whether a reusable rule needs an update. Re-run focused
  checks after changes. Preserve rejected and incomplete routes.
- Promote only repeated/generalizable lessons to `main`, after branch review
  and validation; keep machine-specific paths, PIDs and one-off incidents in
  this workstream.

## Long term — all archived `main` Skills

- Maintain an inventory of every `main` Skill with status `verified`,
  `partial`, or `not-run`, plus a linked real task, acceptance test, raw
  evidence hash, environment scope, date, and known failure boundary.
- Cover untested Skills with independent representative tasks and repeatable
  regression checks, rather than extrapolating from the HYPIC case. A Skill
  moves to `verified` only after its stated behavioral gates pass.
- Publish a reviewed, versioned main-branch validation ledger and keep it
  current as host/runtime/model versions change. The goal is trustworthy
  Skill capability, not a favorable count.

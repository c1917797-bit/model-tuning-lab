# Main Skill validation goals (active from 2026-10-08)

North star: establish which archived `main` Skills work in real, reproducible
tasks. A structurally valid Skill is not a behaviorally verified Skill. This
branch's HYPIC run is one case, not the entire validation campaign.

## Short term — current HYPIC in-path quality gate

- Frozen context: physical chicaihong01 NPU0-3 only; NPU4-7 and unrelated
  containers untouched. Existing three-repeat C1/C2 performance result and
  clean2 off-path quality evidence remain separate.
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

# Workstream Handoff — DRRQR paper parity lessons

Updated: 2026-09-11

## Objective

Convert the DRRQR migration experience into reusable Maintainer Skill Tree
rules. This is a repository-only maintenance task and owns no NPU, container,
port, model, or runtime resource.

## Evidence basis

- The implemented energy selector was not paper-exact StrongRRQR.
- The delivered calibration corpus differed from the paper's corpus.
- The paper workflow uses a training-based quality-recovery stage, while the
  user task forbids retraining and requires no accuracy decline.
- The exact supported Dk64 path produced a credible same-stack throughput gain
  below the frozen target, while quality regressed materially.
- Dk104/Dk88 results were invalidated by an Ascend recurrent-state copy-out
  layout defect and therefore are not algorithm evidence.
- HYPIC succeeded only after its causal mechanism, full runtime path, capacity
  arithmetic, and hot-path activation were ported and verified.

## Planned change

Add an implementation-before-experiment gate that requires a method parity
ledger: enumerate every paper stage that causally supports speed or quality,
identify exact, adapted, omitted, and substituted stages, prove that the user's
constraints leave a feasible success path, and keep paper-exact reproduction
separate from a derivative implementation.

## Implemented checkpoint

- `paper-to-ascend` now requires a stage-by-stage method parity ledger.
- Paper-exact, faithful-port, and derivative identities are distinct.
- User restrictions are checked against every result-bearing paper stage before
  accelerator implementation.
- Backend-invalid execution paths are separated from mathematical algorithm
  evidence.
- A transformation case encodes the DRRQR failure pattern as a reusable
  regression check.

## 2026-09-11 selection and baseline follow-up

User requested ingestion of the subsequent paper-selection and TP4 reporting
experience. The existing clean maintenance branch is reused; no new hardware
experiment or worktree is required.

- `paper-ingestion`: source/publication identity, redistribution permission,
  GPU-to-Ascend contribution intent, and upstream implementation-state checks.
- `ascend-source-map`: exact head grouping/state contract and separation of
  runtime-library repairs from kernel-performance evidence.
- `ascend-benchmark-evidence`: historical/fresh/development baselines,
  new-shape versus warmed TTFT, screening versus complete matrices, and EOS
  length/occupancy effects.
- `paper-to-ascend`: removed stale MTP-first task advice in favor of the owning
  task's current constraints.
- Case evidence is linked from the skills in
  `.agents/skills/paper-ingestion/references/selection-baseline-lessons.md`.
  Kachua remains an unvalidated migration candidate; no Ascend success claimed.

Follow-up validation: `git diff --check` passed; `bash scripts/validate-mst.sh`
passed (26 skills). All four T16 raw-file SHA256 values were independently
recomputed and matched the case record. No performance experiment was rerun;
no NPU, container, model, host framework, or base image was modified. Existing
validation below refers to the earlier parity checkpoint.

## Integration handoff

The implementation is complete. Review the exact branch diff and integrate it
through the serialized maintainer path; do not merge branch-local DRRQR runtime
changes with this shared-skill checkpoint.

## Validation

- `./scripts/validate-mst.sh`: PASS, 26 skills.
- `git diff --check`: PASS.
- Workstream task JSON parse: PASS.
- Transformation-case YAML parse and four-lesson assertion: PASS.
- Semantic presence checks for method-chain completeness, constraint
  feasibility, and algorithm identity: PASS.

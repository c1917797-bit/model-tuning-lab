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

## Resume

Read `.agents/skills/paper-to-ascend/SKILL.md`, update its registry metadata,
add a small transformation case, run the declared validation commands, commit,
and push each coherent checkpoint.

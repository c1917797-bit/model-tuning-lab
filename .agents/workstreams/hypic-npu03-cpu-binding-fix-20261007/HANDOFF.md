# HYPIC NPU0-3 CPU-binding repair — current workstream handoff

## 0. Status

- Updated: 2026-10-08 15:41 UTC. Branch: work/hypic-npu03-cpu-binding-fix-20261007.
- Earlier branch checkpoints were pushed through 622d68a. The validated
  maintainer-handoff Skill case commit b097067 is local-only because Git
  HTTPS authentication disappeared during its push; do not claim it is remote.
  Integrated main has not accepted this campaign.
- HYPIC full paired 2048-token quality, matched performance and Skill-wide
  acceptance remain incomplete. cache10r3 is environment/isolation invalid,
  not an HYPIC algorithm or quality verdict.
- Main has 29 Skills; long-term per-Skill cases on this branch: 2 bounded
  verified, 2 partial, 25 missing. V11/P14/N4 is a separate campaign matrix.
- Full historical checkpoints are retained in HANDOFF_HISTORY.md.

## 1. North Star

Validate the main Skill tree on real tasks with repeatable evidence. HYPIC
needs a fresh same-identity physical NPU0–3 baseline/treatment pair,
explicit-boundary hot-path proof, full 2048-token quality, matched
performance, isolation and independent audits before a final conclusion.

## 2. Current Focus

Short term: original full single-service HYPIC quality then performance on
physical NPU0–3 only. Medium term: map HYPIC outcomes to relevant Skills
and focused regressions. Long term: exact-main per-Skill real-task cases.
Optional cache10split is an unapproved revised protocol: do not run it.

## 3. Recent Progress

- User clarified that foreign container device mapping alone is not use.
  The branch controller now gates on actual NPU0–3 processes and port 8223
  and continuously fails closed on foreign processes while scoring.
- cache10r3 started with idle 0–3; after service readiness, cannbench_ds
  actually used physical NPU3. The guard aborted at 0/127 completed
  samples, released the exact owned service and port, and preserved
  HOTPATH_CACHE10R3_RESOURCE_CONFLICT.md with raw receipt hashes.
- User clarified that idle physical NPU0–3 are sufficient to start; do not
  wait merely because another container has mapped devices. A fresh
  original-protocol cache10r4 candidate arm started under AWMCP operation
  exec-00000000000014c4 after all 127 sample identities, source fingerprints,
  actual NPU processes and port 8223 passed preflight. It remains in flight;
  its continuous guard will reject real foreign use, not passive mappings.
- The Git checkpoint and maintainer-handoff Skills have bounded verified
  real-task cases locally; host-maintenance and onboarding have partial cases. See
  MAIN_SKILL_ACCEPTANCE_GAP_AUDIT_20261008.md and skill-cases/.

## 4. Current Action

Monitor the running cache10r4 operation and exact raw root; do not launch
another controller while it lives. An idle-at-launch snapshot does not
guarantee uninterrupted isolation, so classify any real foreign PID as
environment-invalid through the guard. Target-host Git HTTPS authentication
remains absent; do not repeat local commits merely because push failed.

## 5. Next Actions

1. After host Git authentication is restored, inspect the exact branch
   HEAD and remote ref, then push existing local commits once to the named
   workstream branch and verify upstream equality. Do not amend, reset,
   force-push, or embed credentials in Git files or command output.
2. For any device action, freshly resolve chicaihong01/ma through AWMCP,
   load host-development, prove the direct peer, and inspect physical
   NPU0–3 PIDs and port 8223. Mapping alone does not block this task;
   real foreign PIDs do.
3. Poll cache10r4 exec-00000000000014c4 and
   /cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r4-full-hypic.
   Do not reuse cache10r2/cache10r3 or silently switch to cache10split.
4. Complete HYPIC 127×3 scored quality and independent guard/release
   audit, then same-identity no-cache arm and pair audit. Only after
   quality gates pass, run matched performance.
5. For each main Skill, retain exact main blob, real task, evidence hash,
   boundary and replayable regression; leave unsupported cases partial/N.

## 6. Validation Commands

From this branch worktree:

```sh
./scripts/validate-mst.sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_cases.py
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p 'test_*.py'
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_git_checkpoint_case.py
git diff --check
```

These are offline/structural gates, not live HYPIC acceptance.

## 7. Do Not Do

- Do not use NPU4–7 or stop/modify foreign containers.
- Do not confuse passive mappings with use or ignore real NPU PIDs.
- Do not resume invalid roots, mix their rows into a clean pair, or call
  0/127 samples an algorithm failure.
- Do not extrapolate the bounded Git case to all 29 Skills or edit the
  integrated global .agents/HANDOFF.md from this work branch.
- Do not claim the pending local commit was pushed; do not print secrets
  or install an unreviewed credential helper to force it.
- Keep credentials, weights, datasets and raw profiles out of Git.

## 8. Recovery / Resume Commands

Read AGENTS.md, global .agents/HANDOFF.md, this file, task.json,
HANDOFF_HISTORY.md and narrow Skills. Inspect current branch and physical
resources before any new launch:

```sh
git status --short --branch
git log -8 --decorate --oneline
git rev-parse HEAD '@{upstream}'
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_cases.py
npu-smi info
ss -lntp
```

Once safe Git authentication is restored, push the existing HEAD with
`git push origin HEAD:work/hypic-npu03-cpu-binding-fix-20261007` and
check the live remote ref. This is pending, not completed.

cache10r3 controller exec-000000000000147b is terminal exit 1. Its raw root:
/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r3-full-hypic.

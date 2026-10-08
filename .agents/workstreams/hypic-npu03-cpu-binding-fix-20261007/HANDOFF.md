# HYPIC NPU0-3 CPU-binding repair — current workstream handoff

## 0. Status

- Updated: 2026-10-08 15:20 UTC. Branch: work/hypic-npu03-cpu-binding-fix-20261007.
- Branch checkpoints are pushed; integrated main has not accepted this campaign.
- HYPIC full paired 2048-token quality, matched performance and Skill-wide
  acceptance remain incomplete. cache10r3 is environment/isolation invalid,
  not an HYPIC algorithm or quality verdict.
- Main has 29 Skills; long-term per-Skill cases on this branch: 1 bounded
  verified, 2 partial, 26 missing. V11/P14/N4 is a separate campaign matrix.
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
- The Git checkpoint Skill has one bounded verified real-task case;
  host-maintenance and onboarding have partial cases. See
  MAIN_SKILL_ACCEPTANCE_GAP_AUDIT_20261008.md and skill-cases/.

## 4. Current Action

Continue non-NPU Skill acceptance while awaiting an uninterrupted NPU0–3
window. cannbench_ds remains running and intermittently executes real
kernels; an idle snapshot is not a full-run lease. User coordination was
requested. Do not restart terminal cache10r3 or reuse its root.

## 5. Next Actions

1. For any device action, freshly resolve chicaihong01/ma through AWMCP,
   load host-development, prove the direct peer, and inspect physical
   NPU0–3 PIDs and port 8223. Mapping alone does not block this task;
   real foreign PIDs do.
2. In a sustained clean window, declare a new unique original-protocol
   HYPIC campaign/root. Do not reuse cache10r2 or cache10r3 and do not
   silently switch to cache10split.
3. Complete HYPIC 127×3 scored quality and independent guard/release
   audit, then same-identity no-cache arm and pair audit. Only after
   quality gates pass, run matched performance.
4. For each main Skill, retain exact main blob, real task, evidence hash,
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
- Keep credentials, weights, datasets and raw profiles out of Git.

## 8. Recovery / Resume Commands

Read AGENTS.md, global .agents/HANDOFF.md, this file, task.json,
HANDOFF_HISTORY.md and narrow Skills. Inspect current branch and physical
resources before any new launch:

```sh
git status --short --branch
git log -8 --decorate --oneline
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_cases.py
npu-smi info
ss -lntp
```

cache10r3 controller exec-000000000000147b is terminal exit 1. Its raw root:
/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r3-full-hypic.

# HYPIC NPU0-3 CPU-binding repair — current workstream handoff

## 0. Status

- Updated: 2026-10-08 16:08 UTC. Branch: work/hypic-npu03-cpu-binding-fix-20261007.
- The branch is pushed and verified through 1fec73f; `exec-00000000000014cf`
  confirmed live remote, upstream and clean local HEAD equality after the
  target-host Git HTTPS authentication recovered. Integrated main has not
  accepted this campaign.
- HYPIC full paired 2048-token quality, matched performance and Skill-wide
  acceptance remain incomplete. cache10r3, cache10r4 and cache10r5 are
  environment/isolation invalid, not HYPIC algorithm or quality verdicts.
- Main has 29 Skills; long-term per-Skill cases on this branch: 2 bounded
  verified, 3 partial, 24 missing. V11/P14/N4 is a separate campaign matrix.
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
  actual NPU processes and port 8223 passed preflight. Its guard found an
  actual foreign NPU0 PID before any scored sample; it exited 1, recorded
  0/127, released its exact owned service and port, and retained
  HOTPATH_CACHE10R4_RESOURCE_CONFLICT.md with raw hashes.
- The Git checkpoint and maintainer-handoff Skills have bounded verified
  real-task cases locally; host-maintenance and onboarding have partial cases. See
  MAIN_SKILL_ACCEPTANCE_GAP_AUDIT_20261008.md and skill-cases/.
- During cache10r4 service loading, a read-only host snapshot at 15:44 UTC
  caught transient foreign `cannbench_ds` NPU0/1 PIDs. The arm's continuous
  scoring guard starts after service readiness; preserve this startup
  overlap as a caveat and rely on the later guard/evidence for the score
  decision. No foreign container was modified.
- The startup guard repair is in HOTPATH_STARTUP_GUARD_REPAIR.md and was
  pushed at 5e3b774 after 34 offline tests. cache10r5 live operation
  exec-00000000000014ee proved that its new pre-health guard catches
  `cannbench_ds` on physical NPU2 and releases only the exact owned
  container within about 135 seconds, at 0/127 scored samples. See
  HOTPATH_CACHE10R5_STARTUP_GUARD_RESULT.md and immutable hashes.
- A fifth provenance-checked Skill case now records the bounded
  `ascend-npu-environment-orientation` behavior as partial, not verified;
  see NPU_ENVIRONMENT_ORIENTATION_ACCEPTANCE_20261008.md and the gap audit.

## 4. Current Action

cache10r5 is terminal and environment-invalid. At 16:01 UTC, physical
NPU1 again had actual foreign processes; do not launch another full arm
during real use. A momentary idle snapshot is not an uninterrupted lease.
Continue other Skill acceptance until NPU0–3 use is sustainably clear;
passive Docker mappings alone remain irrelevant. The branch was
synchronized at 5e3b774 before this status update; check again before
claiming new changes are remote.

## 5. Next Actions

1. Preserve the successful push and live equality receipt for 1fec73f.
   Validate, then push each later coherent checkpoint to the named
   workstream branch; never amend, reset, force-push, or expose credentials.
2. For any device action, freshly resolve chicaihong01/ma through AWMCP,
   load host-development, prove the direct peer, and inspect physical
   NPU0–3 PIDs and port 8223. Mapping alone does not block this task;
   real foreign PIDs do.
3. Audit cache10r5's immutable root and terminal exec-00000000000014ee
   against HOTPATH_CACHE10R5_STARTUP_GUARD_RESULT.md. Do not reuse
   cache10r2/cache10r3/cache10r4/cache10r5 or silently switch to cache10split.
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

The pending commits were pushed through 1fec73f. After any later commit,
push the current HEAD with
`git push origin HEAD:work/hypic-npu03-cpu-binding-fix-20261007` and
check the live remote ref before claiming it is synchronized.

cache10r3 controller exec-000000000000147b, cache10r4 controller
exec-00000000000014c4, and cache10r5 controller exec-00000000000014ee
are terminal exit 1, all environment-invalid. Their immutable raw roots are
respectively
/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r3-full-hypic
and
/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r4-full-hypic
and
/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r5-full-hypic.

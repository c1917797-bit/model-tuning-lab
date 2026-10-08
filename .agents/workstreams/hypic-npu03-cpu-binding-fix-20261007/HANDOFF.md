# HYPIC NPU0-3 CPU-binding repair — current workstream handoff

## 0. Status

- Updated: 2026-10-08 16:14 UTC. Branch: work/hypic-npu03-cpu-binding-fix-20261007.
- The last independently verified live remote HEAD was deab436. The later
  r6 identity commit a55cc1d is local-only as of this update: two bounded
  Git pushes timed out, and a live remote read still showed deab436. Do
  not claim r6 code was pushed. Do not repeat the commit or force-push.
- Integrated main has not accepted this campaign.
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
- cache10r3/r4 began on idle physical0–3, then real foreign processes
  intruded before scoring. Both aborted at 0/127 and released exact owned
  services; see their separate RESOURCE_CONFLICT reports and raw hashes.
- The Git checkpoint and maintainer-handoff Skills have bounded verified
  real-task cases locally; host-maintenance and onboarding have partial cases. See
  MAIN_SKILL_ACCEPTANCE_GAP_AUDIT_20261008.md and skill-cases/.
- The startup guard repair is in HOTPATH_STARTUP_GUARD_REPAIR.md and was
  pushed at 5e3b774 after 34 offline tests. cache10r5 live operation
  exec-00000000000014ee proved that its new pre-health guard catches
  `cannbench_ds` on physical NPU2 and releases only the exact owned
  container within about 135 seconds, at 0/127 scored samples. See
  HOTPATH_CACHE10R5_STARTUP_GUARD_RESULT.md and immutable hashes.
- A fifth provenance-checked Skill case now records the bounded
  `ascend-npu-environment-orientation` behavior as partial, not verified;
  see NPU_ENVIRONMENT_ORIENTATION_ACCEPTANCE_20261008.md and the gap audit.
- A unique original-protocol cache10r6 identity was preflighted: 127
  samples, physical0–3, 0.85 utilization, 3584 MiB/10 segments. AWMCP
  operation exec-000000000000150a is a *single* pending controller: it
  samples actual NPU0–3/port every 30 seconds, requires 10 consecutive
  clean checks, then launches exactly one candidate arm. If no such window
  occurs within two hours, it exits without creating a root. It ignores
  passive Docker mappings and does not use NPU4–7. Poll this operation;
  never launch a parallel r6 controller.

## 4. Current Action

cache10r5 is terminal and environment-invalid. The single r6 watcher
exec-000000000000150a is live; do not start a duplicate. Continue other
Skill acceptance while it waits for actual NPU0–3 idleness. Passive
Docker mappings alone remain irrelevant. Push the pending local r6
checkpoint when target-host Git HTTPS becomes responsive, then verify
remote/upstream equality.

## 5. Next Actions

1. Retry only the pending push when Git HTTPS responds, then verify live
   equality; never amend, reset, force-push, or expose credentials.
2. For any device action, freshly resolve chicaihong01/ma through AWMCP,
   load host-development, prove the direct peer, and inspect physical
   NPU0–3 PIDs and port 8223. Mapping alone does not block this task;
   real foreign PIDs do.
3. Poll r6 watcher exec-000000000000150a before any device action. If
   terminal, inspect whether it created
   /cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r6-full-hypic.
   Audit cache10r5 separately against HOTPATH_CACHE10R5_STARTUP_GUARD_RESULT.md.
   Do not reuse cache10r2/cache10r3/cache10r4/cache10r5 or silently switch
   to cache10split.
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

After a validated commit, push the current HEAD with
`git push origin HEAD:work/hypic-npu03-cpu-binding-fix-20261007` and
check the live remote ref before claiming it is synchronized.

cache10r3/r4/r5 terminal operations and immutable raw roots are recorded
in their conflict/result reports; none is a valid baseline/treatment arm.

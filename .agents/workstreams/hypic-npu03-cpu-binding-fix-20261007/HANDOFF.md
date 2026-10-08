# HYPIC NPU0-3 CPU-binding repair — current workstream handoff

## 0. Status

- Updated: 2026-10-08 16:39 UTC. Branch: work/hypic-npu03-cpu-binding-fix-20261007.
- The r6 code and watcher handoff are pushed through 1a3a518. Operation
  exec-0000000000001514 verified clean local HEAD, upstream and live remote
  equality. Plain HTTPS briefly timed out/errored; a per-command HTTP/1.1
  push succeeded without changing persistent Git settings.
- Integrated main has not accepted this campaign.
- HYPIC full paired 2048-token quality, matched performance and Skill-wide
  acceptance remain incomplete. cache10r3 through cache10r7 are
  environment/isolation invalid, not HYPIC algorithm or quality verdicts.
- Main has 29 Skills; long-term per-Skill cases on this branch: 2 bounded
  verified, 4 partial, 23 missing. V11/P14/N4 is a separate campaign matrix.
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
- cache10r6 launched after ten actual-idle checks, ignoring passive
  mappings. Startup guard caught foreign PID 1426552 on physical NPU2
  at 16:21:22 UTC, stopped at 0/127 and released only owned resources;
  see HOTPATH_CACHE10R6_RESOURCE_CONFLICT.md and raw SHA-256 receipts.
- The user explicitly confirmed actual physical NPU0–3 idleness permits
  running regardless of others' passive mappings. After a clean live probe,
  a new unique cache10r7 attempt was launched. Its controller operation is
  exec-0000000000001523, root
  /cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r7-full-hypic.
  The first r7 launch was rejected by its allowlist before root creation;
  both campaign and artifact mapping were repaired, then 35 offline tests
  passed. The second launch caught a real foreign PID 1482057 on physical
  NPU3 during startup at 16:28:11 UTC. It stopped at 0/127 and removed
  only its owned container; see HOTPATH_CACHE10R7_RESOURCE_CONFLICT.md.
- The real r6/r7 practice was ingested via the existing branch-local
  host-maintenance guard, a registry trigger, and a structured eval with
  raw-artifact replay. The sixth Skill case covers `mst-experience-ingestion`
  as partial: main still lacks that continuous guard. See
  hypic-shared-npu-reentry-ingestion.yaml and verify_experience_ingestion_case.py.

## 4. Current Action

cache10r6/r7 are terminal and environment-invalid; no quality controller is
live. Both started after actual NPU0–3 idleness, but a real foreign process
entered during startup. Do not blindly reattempt under the same shared
scheduling conditions. Continue non-device Skill acceptance and obtain a
durable exclusive NPU0–3 window before a new unique full arm. Passive Docker
mappings alone remain irrelevant. The branch remote was independently
verified at 06279f67865b59aede6edcdea0b78da21429e720 before this
handoff update; recheck latest HEAD and remote on resume.

## 5. Next Actions

1. For later validated changes, push the named branch and verify live
   equality; never amend, reset, force-push, or expose credentials.
2. For any device action, freshly resolve chicaihong01/ma through AWMCP,
   load host-development, prove the direct peer, and inspect physical
   NPU0–3 PIDs and port 8223. Mapping alone does not block this task;
   real foreign PIDs do.
3. Inspect cache10r7 terminal op exec-0000000000001523 and its immutable
   root under `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/` if needed.
   Audit cache10r5/r6/r7 separately against their result reports.
   Do not reuse cache10r2/cache10r3/cache10r4/cache10r5/cache10r6/cache10r7 or silently switch
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
- Do not claim later local commits are remote without a live read; do not
  print secrets or install an unreviewed credential helper.
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

cache10r3/r4/r5/r6/r7 terminal operations and immutable raw roots are recorded
in their conflict/result reports; none is a valid baseline/treatment arm.

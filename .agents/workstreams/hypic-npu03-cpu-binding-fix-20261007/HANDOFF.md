# HYPIC NPU0-3 CPU-binding repair — current workstream handoff

## 0. Status

- Updated: 2026-10-08 17:14 UTC. Branch: work/hypic-npu03-cpu-binding-fix-20261007.
- The r6 code and watcher handoff are pushed through 1a3a518. Operation
  exec-0000000000001514 verified clean local HEAD, upstream and live remote
  equality. Plain HTTPS briefly timed out/errored; a per-command HTTP/1.1
  push succeeded without changing persistent Git settings.
- Integrated main has not accepted this campaign.
- HYPIC full paired 2048-token quality, matched performance and Skill-wide
  acceptance remain incomplete. cache10r3 through cache10r8 are
  environment/isolation invalid, not HYPIC algorithm or quality verdicts.
- Main has 29 Skills; long-term per-Skill cases on this branch: 2 bounded
  verified, 5 partial, 22 missing. V11/P14/N4 is a separate campaign matrix.
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
- The seventh case caught `mst-practice-iteration-planning`'s main YAML
  schema mismatch; the branch Skill repair and bounded HYPIC plan pass.
  Main remains partial; see PRACTICE_ITERATION_SCHEMA_ACCEPTANCE_20261008.md.
- cache10r6 launched after ten actual-idle checks, ignoring passive
  mappings. Startup guard caught foreign PID 1426552 on physical NPU2
  at 16:21:22 UTC, stopped at 0/127 and released only owned resources;
  see HOTPATH_CACHE10R6_RESOURCE_CONFLICT.md and raw SHA-256 receipts.
- cache10r7 reached 0/127 after a real foreign NPU3 PID entered during startup;
  its owned service was released. See HOTPATH_CACHE10R7_RESOURCE_CONFLICT.md
  for the immutable operation, root, allowlist repair and raw hashes.
- The user chose opportunistic actual-idle attempts over requiring an exclusive
  reservation. cache10r8 launched on actual-idle physical NPU0–3, then its
  startup guard caught a real foreign `cannbench_ds` PID 1762714 on physical
  NPU3 at 16:54:46 UTC. It stopped before health at 0/127 and released only
  its owned container/port. See HOTPATH_CACHE10R8_RESOURCE_CONFLICT.md.
- The real r6/r7 practice was ingested via the existing branch-local
  host-maintenance guard, a registry trigger, and a structured eval with
  raw-artifact replay. The sixth Skill case covers `mst-experience-ingestion`
  as partial: main still lacks that continuous guard. See
  hypic-shared-npu-reentry-ingestion.yaml and verify_experience_ingestion_case.py.

## 4. Current Action

cache10r9 full HYPIC controller `exec-000000000000158e` is **live** on physical
NPU0–3 in the unique root `quality-context-41984-hotpath-cache10r9-full-hypic`.
Service became healthy at 17:06:55 UTC; the first scored sentinel passed its
four-worker hot-path gate at 17:09:43. It is processing the remaining 126
samples. Poll this exact operation and root; never launch a duplicate while it
runs. cache10r8 is terminal and isolation-invalid. The r9 preparation branch
commit `54c092b210a8c3791496a124b8439deba26a6369` was live-remote verified.
On collision, preserve evidence and only retry a fresh root when actual 0–3
and port 8223 are idle; passive mappings do not veto and foreign jobs stay.

## 5. Next Actions

1. For later validated changes, push the named branch and verify live
   equality; never amend, reset, force-push, or expose credentials.
2. For any device action, freshly resolve chicaihong01/ma through AWMCP,
   load host-development, prove the direct peer, and inspect physical
   NPU0–3 PIDs and port 8223. Mapping alone does not block this task;
   real foreign PIDs do.
3. Inspect cache10r8 terminal op exec-000000000000157a and its immutable
   root under `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/` if needed.
   Audit cache10r5/r6/r7 separately against their result reports.
   Do not reuse cache10r2/cache10r3/cache10r4/cache10r5/cache10r6/cache10r7/cache10r8 or silently switch
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

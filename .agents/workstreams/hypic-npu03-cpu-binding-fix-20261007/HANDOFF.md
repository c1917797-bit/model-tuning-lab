# HYPIC NPU0-3 CPU-binding repair — current workstream handoff

## 0. Status

- Updated: 2026-10-08 19:02 UTC. Branch: work/hypic-npu03-cpu-binding-fix-20261007.
- Live remote workstream tip was 0d00bab at last read. Local 4073829 and
  later work are NOT pushed: HTTPS lacks noninteractive credentials and SSH
  timed out. Await user-provisioned auth; do not expose credentials.
- Integrated main has not accepted this campaign.
- HYPIC full paired 2048-token quality, matched performance and Skill-wide
  acceptance remain incomplete. cache10r3 through cache10r8 are
  environment/isolation invalid, not HYPIC algorithm or quality verdicts.
- Main has 29 Skills; long-term per-Skill cases on this branch: 2 bounded
  verified, 7 partial, 20 missing. V11/P14/N4 is a separate campaign matrix.
- Full historical checkpoints are retained in HANDOFF_HISTORY.md.
- r9 is terminal FAILED at 93/127 after a worker-local GDN material miss.
  See HOTPATH_CACHE10R9_EVICTION_RACE_ROOT_CAUSE.md; no quality verdict.
- r10 full HYPIC is running as operation exec-00000000000016af at the root
  in task.json. At 19:01 UTC, 28 samples were complete; 81/84 scored
  requests had four-worker proof. Sample 6 rep 3 and sample 18 reps 2–3
  fell back natively.
  See HOTPATH_CACHE10R10_PARTIAL_REQUEST_COVERAGE.md; no final verdict.
- Quality and benchmark Skill cases eight/nine remain partial; see their
  request-coverage and baseline-reuse acceptance reports.

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
- The startup guard repair passed 34 offline tests and caught the
  r5 foreign NPU2 process before scoring; see
  HOTPATH_STARTUP_GUARD_REPAIR.md and HOTPATH_CACHE10R5_STARTUP_GUARD_RESULT.md.
- The seventh case caught `mst-practice-iteration-planning`'s main YAML
  schema mismatch; the branch Skill repair and bounded HYPIC plan pass.
  Main remains partial; see PRACTICE_ITERATION_SCHEMA_ACCEPTANCE_20261008.md.
- r6/r7 both stopped before scoring on real foreign NPU2/NPU3
  processes and released only owned resources. See their separate
  RESOURCE_CONFLICT reports for PIDs, roots and hashes.
- The user chose actual-idle attempts. r8 caught foreign
  `cannbench_ds` on physical NPU3 before scoring and released only
  owned resources; see HOTPATH_CACHE10R8_RESOURCE_CONFLICT.md.
- The real r6/r7 practice was ingested via the existing branch-local
  host-maintenance guard, a registry trigger, and a structured eval with
  raw-artifact replay. The sixth Skill case covers `mst-experience-ingestion`
  as partial: main still lacks that continuous guard. See
  hypic-shared-npu-reentry-ingestion.yaml and verify_experience_ingestion_case.py.

## 4. Current Action

r10 operation `exec-00000000000016af` is the sole active controller.
Do not restart or mix another root. Its pinned clean plugin commit
`4429e35177979c874bf053ab29789e4773f39b22` has the pending-eviction
gate and per-request worker events. The strict verifier now joins host PIDs
to container PID namespace using a validated sidecar. r10 has this map
under `hypic-only/worker-namespace-map.json`; future launches write it
automatically. At 18:46 UTC, 12/12 completed scored requests passed the
four-worker audit. 46 offline tests and nine provenance checks pass, but
full device acceptance remains pending. One scored r10 request lacks proof;
see the partial-coverage report. Preserve r9 raw root; its 93/127
GDN miss is not a quality verdict. Old 0.9 baseline is not pairable with 0.85.

## 5. Next Actions

1. Preserve local commits while GitHub auth is unavailable. After user
   provisioning, push named branch and verify live equality; no force.
2. For any device action, freshly resolve chicaihong01/ma through AWMCP,
   load host-development, prove the direct peer, and inspect physical
   NPU0–3 PIDs and port 8223. Mapping alone does not block this task;
   real foreign PIDs do.
3. Poll only r10 operation exec-00000000000016af and its progress file.
   Preserve prior roots and audit r9 against its failure report.
   Do not reuse cache10r2/cache10r3/cache10r4/cache10r5/cache10r6/cache10r7/cache10r8 or silently switch
   to cache10split.
4. Continue r10; audit eviction gate, all request-level four-worker
   coverage, 127×3 quality, and isolation. Pair with new 0.85 no-cache
   arm only if valid; then run matched performance.
5. For each main Skill, retain exact main blob, real task, evidence hash,
   boundary and replayable regression; leave unsupported cases partial/N.

## 6. Validation Commands

From this branch worktree:

```sh
./scripts/validate-mst.sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_cases.py
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p 'test_*.py'
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_git_checkpoint_case.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/diagnose_partial_hotpath_coverage.py /cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r10-full-hypic
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

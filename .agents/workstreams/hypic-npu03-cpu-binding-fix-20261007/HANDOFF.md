# HYPIC NPU0-3 CPU-binding repair — current workstream handoff

## 0. Status

- Updated: 2026-10-08 18:00 UTC. Branch: work/hypic-npu03-cpu-binding-fix-20261007.
- The r6 code and watcher handoff are pushed through 1a3a518. Operation
  exec-0000000000001514 verified clean local HEAD, upstream and live remote
  equality. Plain HTTPS briefly timed out/errored; a per-command HTTP/1.1
  push succeeded without changing persistent Git settings.
- Integrated main has not accepted this campaign.
- HYPIC full paired 2048-token quality, matched performance and Skill-wide
  acceptance remain incomplete. cache10r3 through cache10r8 are
  environment/isolation invalid, not HYPIC algorithm or quality verdicts.
- Main has 29 Skills; long-term per-Skill cases on this branch: 2 bounded
  verified, 7 partial, 20 missing. V11/P14/N4 is a separate campaign matrix.
- Full historical checkpoints are retained in HANDOFF_HISTORY.md.
- Live r9 request-level traceability is not yet proven despite aggregate
  hot-path activity; see HOTPATH_CACHE10R9_REQUEST_TRACEABILITY_AUDIT.md.
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

cache10r9 full HYPIC controller `exec-000000000000158e` is **live** on physical
NPU0–3 in the unique root `quality-context-41984-hotpath-cache10r9-full-hypic`.
Service became healthy at 17:06:55 UTC; the first scored sentinel passed its
four-worker hot-path gate at 17:09:43. Poll this exact operation/root and
never launch a duplicate while it runs.
At the 17:36 read-only checkpoint, 38/127 sample files existed and their
114 scored IDs each matched a boundary event. Worker hot-path and hybrid
repair events lacked request IDs, so per-scored-request hot-path coverage
remains unverified under the quality Skill. Preserve r9 unchanged and do
not interpret a green aggregate controller result as this stricter gate.
The old completed no-cache arm used GPU utilization 0.9 versus r9's 0.85:
HOTPATH_CACHE10R9_BASELINE_REUSE_AUDIT.md proves it is not reusable. After a
valid candidate, run only the fresh r9 0.85 no-cache arm on an actually idle
lane. cache10r8 is isolation-invalid; on collision preserve evidence, touch
only owned resources, and retry a new root only when physical 0–3 are idle.
Passive mappings do not veto; foreign workloads stay untouched.

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
4. Complete r9's 127×3 scored rows and independent guard/release audit.
   Audit request-level work-performing coverage separately from boundary
   admission and aggregate repair counts. If it remains unverified, repair
   telemetry only after r9 releases its service and use a fresh candidate
   identity/root; pair only with a matching no-cache arm. Only after all
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

# HYPIC NPU0-3 CPU-binding repair — current workstream handoff

## 0. Status

- Updated: 2026-10-09. Branch: work/hypic-npu03-cpu-binding-fix-20261007.
- Remote workstream tip last observed as 0d00bab; local work through 17aa9fc
  and later is NOT pushed: HTTPS lacks noninteractive credentials and SSH
  timed out. Await user-provisioned auth; do not expose credentials.
- Integrated main has not accepted this campaign.
- HYPIC r13 full paired 2048-token quality is valid but REJECT_OR_QUALIFY;
  strict hot coverage FAIL. Matched performance and Skill-wide acceptance
  remain incomplete. cache10r3 through cache10r8 are
  environment/isolation invalid, not HYPIC algorithm or quality verdicts.
- Main has 29 Skills; long-term per-Skill cases on this branch: 2 bounded
  verified, 21 partial, 6 missing. V11/P14/N4 is a separate campaign matrix.
- Full historical checkpoints are retained in HANDOFF_HISTORY.md.
- r9 is terminal FAILED at 93/127 after a worker-local GDN material miss.
  See HOTPATH_CACHE10R9_EVICTION_RACE_ROOT_CAUSE.md; no quality verdict.
- r10 ended at 20:04 UTC, exit 1: all 127 samples and 381 responses persisted,
  but only 366/381 scored requests had four-worker proof; 15 failed the
  strict activation gate. Exact owned service released, 1,077 clean guard
  probes. See HOTPATH_CACHE10R10_TERMINAL_AUDIT.md; no paired verdict.
- r11 targeted c8 stress ended at 20:49 UTC, exit 1: all 19 samples and 57
  responses persisted, but only 53/57 scored requests had four-worker proof.
  Gaps were 77:2, 79:2, 79:3 and 85:2. Its 283 guard probes were clean;
  exact owned service and port released. See
  HOTPATH_CACHE10R11_TERMINAL_AUDIT.md; no paired verdict.
- Plugin source c12060c repairs a scheduler-directory rebuild defect seen
  in the 79:2-to-79:3 eviction chain. Red/green focused regression, 13
  focused tests, compile and single-instance source/topology audits passed.
  r12 ran this source on NPU0–3 but strict hot coverage failed. Broad
  test_pure.py collection is blocked by host Python 3.9 lacking pairwise.
- r12 stress: 19/19 samples, 57/57 responses, 52/57 four-worker proof;
  279 clean guard probes and exact release. r11's 79:2/79:3 gaps are hot
  here, but five others missed; HOTPATH_CACHE10R12_TERMINAL_AUDIT.md has no paired verdict.
- Architecture fit, ingestion, quality, benchmark, tuning, optimization, reporting, source-map and canary cases remain partial. r13 paired quality is negative; C3 remains open. See HOTPATH_CACHE10R13_TERMINAL_QUALITY_AUDIT.md.
- The inference-tuning-loop case replays six raw performance runs and three
  candidate contracts/cleanup receipts; bounded CPU-binding-off TPOT median
  fell 81.12%, but full HYPIC and 2048-token quality remain open.

## 1. North Star

Validate the main Skill tree on real tasks with repeatable evidence. HYPIC
needs a fresh same-identity physical NPU0–3 baseline/treatment pair,
explicit-boundary hot-path proof, full 2048-token quality, matched
performance, isolation and independent audits before a final conclusion.

## 2. Current Focus

Short term: original full single-service HYPIC quality then performance on
physical NPU0–3 only. Medium term: map HYPIC outcomes to relevant Skills
and focused regressions. Long term: exact-main per-Skill real-task cases.
Prospective cache10r13 full 127x3 pair freezes dual deployed/strict conclusions;
cache10split remains unapproved and must not run.

## 3. Recent Progress

- User clarified that foreign container device mapping alone is not use.
  The branch controller now gates on actual NPU0–3 processes and port 8223
  and continuously fails closed on foreign processes while scoring.
- Earlier r3–r8 foreign-process conflicts, startup-guard fixes and exact
  releases are indexed in HANDOFF_HISTORY.md and separate raw-hash reports;
  none is an algorithm verdict.
- Git checkpoint and maintainer-handoff have bounded verified cases; host,
  onboarding and tool-adapter boundary have partial real-task cases. See
  MAIN_SKILL_ACCEPTANCE_GAP_AUDIT_20261008.md and skill-cases/.
- The seventh case caught `mst-practice-iteration-planning`'s main YAML
  schema mismatch; the branch Skill repair and bounded HYPIC plan pass.
  Main remains partial; see PRACTICE_ITERATION_SCHEMA_ACCEPTANCE_20261008.md.
- The user chose actual-idle attempts; passive mapping alone does not block
  use, while real foreign NPU processes do.
- Loop-framework case caught and repaired stale task.json active_attempt=null;
  its exact-main long-term status remains partial pending fresh-agent replay.

## 4. Current Action

r13 baseline and candidate each passed full 127x3/source/isolation/release
audit. Frozen dual report `f66b976` says 230/381 to 219/381 (-2.887 pp),
deployed quality REJECT_OR_QUALIFY; strict 368/381 hot FAIL. All 13 cold
requests show material ready then evicted before partial-prefill rejection.
Hot-cohort quality also declined descriptively; cause remains unisolated.
See HOTPATH_CACHE10R13_TERMINAL_QUALITY_AUDIT.md. No-cache/screen passed its
40-row/42-ID/source/isolation/release audit; expired handle is not a rerun
signal (HOTPATH_CACHE10PERF_SCREEN_BASELINE_AUDIT.md). HYPIC-only/screen
controller `exec-0000000000001c22` is running; poll, never restart.
Do not post-hoc pass either root, use NPU4–7, or modify foreign containers.

## 5. Next Actions

1. Preserve r10–r13 negatives; poll performance hypic-only/screen, independently
   audit terminal receipts, then run remaining frozen phases serially.
2. Preserve local commits while GitHub auth is unavailable. After user
   provisioning, push named branch and verify live equality; no force.
3. For any device action, freshly resolve chicaihong01/ma through AWMCP,
   load host-development, prove the direct peer, and inspect physical
   NPU0–3 PIDs and port 8223. Mapping alone does not block this task;
   real foreign PIDs do.
4. Preserve r9–r12 terminal roots; never relabel their strict failures,
   pair them with a control, reuse r2–r8 roots, or switch to cache10split.
5. Follow HOTPATH_CACHE10R13_MATCHED_PERFORMANCE_PLAN.md; six phases separately
   audit deployed effect and strict per-request proof, plus isolation/release.
6. For each main Skill, retain exact main blob, real task, evidence hash,
   boundary and replayable regression; leave unsupported cases partial/N.

## 6. Validation Commands

From this branch worktree:

```sh
./scripts/validate-mst.sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_cases.py
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p 'test_*.py'
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_git_checkpoint_case.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_inference_tuning_loop_case.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/audit_cache10r11_stress.py
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

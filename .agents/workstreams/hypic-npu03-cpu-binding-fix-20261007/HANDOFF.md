# HYPIC NPU0–3 — current handoff

## 0. Status

As of2026-10-13: device campaign terminal; broad Skill-validation goal incomplete.
Branch work/hypic-npu03-cpu-binding-fix-20261007; runtime source4429e35.
Six-phase same-source performance is complete, not a quality pass.
Current task.active_attempt=null; no performance controller remains active.
Execution in-progress / integration not-ready. No main/remote synchronization.
29 cases:9 bounded verified,20 partial,0 missing. No all-Skill success claim.
App heartbeat hypic is absent; do not recreate it for the finished supplement.

## 1. North Star

Long: real requirement-scoped acceptance and replayable evidence for all29
exact-main Skills, with authorized reviewed main/remote integration.
Medium: retain HYPIC successes/failures, repair demonstrated workflow defects,
and regress those repairs without manufacturing historical evidence.
Short: preserve complete max2048 paired quality and same-source performance/
isolation evidence on physical0–3; no repeated runs of completed roots.

## 2. Current Focus

Offline exact-main obligation review and handoff/state repair only.
Use task.json.current_source_performance_checkpoint as current campaign state;
older named attempt/milestone entries are historical,not live instructions.
The original full single-service quality attempts and retry history are retained
in HANDOFF_HISTORY.md and HANDOFF_SNAPSHOT_20261013_0802.md.
Snapshot SHA256 a79dfa7aa634a1f69575c24d56fb0dc03efeecc9a15ef1dee07cfa1d336311cd.
Global .agents/HANDOFF.md describes integrated history,not this unmerged result.

## 3. Recent Progress

- r19 LongBench-v2:227/381→219/381,−2.0997pp; REJECT_OR_QUALIFY.
  GSM8K off-path3838/3957→3840/3957 does not prove HYPIC hot-path quality.
- current4429 performance:6/6 valid,240 scored responses,120/120 candidate
  four-worker hot proof,1006 clean isolation samples; all exact services released.
  Median TPOT−22.0163%,TTFT P95−49.6429%,throughput+31.7543%.
  Performance output1024; existing natural-EOS quality cap2048; do not mix them.
- Native enabled and disabled canaries both failed semantic guard; exact
  resources released. Uninstalled control was not started. No adoption.
- Report checkpoint232299f2; five stale case-route repairs checkpointe28acb4f.
  Six routing regressions and five statistics regressions passed;9/20 unchanged.
- Current handoff audit0306 exposed a1417-line diary and stale active GSM8K.
  Raw terminal proof0308: GSM8K released2026-10-10T17:11:41UTC,3 units complete.
  Its former active entry is retained under retired_active_attempt_20261013.
  See LOOP_HANDOFF_REPAIR_20261013.md; after the live-test digest repair,
  0312 passed15 focused checks, historical replays,29 provenance and29 structure checks.

## 4. Current Action

Current/historical handoff repair is committed874ec388. Report review031a
found missing round-level TPOT P95/duration; repaired from existing raw data.
031c passed six-phase raw replay and7 report tests; report repair commitea5e16b2.
0329 reviewed all7 retained profiler phases and6 negative-control tests.
See HYPIC_PROFILER_HISTORY_REVIEW_20261013.md: r3 was omitted from the old
failure table; Prefill executed-controller bytes remain unavailable. Do not
repeat this completed inventory/search. No Skill promotion; review only
genuinely remaining exact-main obligations against existing evidence.
Preserve negative verdicts,exact raw hashes and the two pre-existing untracked
observer-v3 drafts; do not stage or activate them.
Do not reinterpret the successful performance supplement as a deployment gate.
Loop-framework full acceptance still lacks fresh-agent orient/validate/push
evidence; local docs/tests alone cannot prove that behavior.

## 5. Next Actions

1. Run the read-only current-state and case-provenance commands below.
2. Review remaining exact-main Skill obligations against existing evidence.
   Historical missing identity/chronology/retry data remains unavailable;
   do not rerun completed HYPIC merely to improve acceptance counts.
3. Record only demonstrated fixes and task-scoped acceptance. Preserve9/20
   unless the original Skill requirements are actually proven.
4. Remote authentication remains unresolved. Do not repeat unchanged failed
   pushes or claim main integration. Push only when authentication changes
   and existing authorization applies; then independently verify equality.
5. Fixed experiment deadline2026-10-13T08:47:14Z is unchanged. No new device
   stages are scheduled or authorized by this handoff.

## 6. Validation Commands

Run from /cache/cch/model-tuning-lab-hypic-e2e-20261006:
```bash
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p 'test_handoff_current.py'
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_completed_campaign_routes.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_cases.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_current_source_performance_report.py
bash scripts/validate-mst.sh
git diff --check
```
From this workstream, read-only summarize_current_source_performance.py replays
all six raw audits. Do not repeat its exclusive audit-all writer.
Historical snapshot verifiers verify_handoff_case.py and
verify_loop_framework_case.py remain separate from current-state tests.

## 7. Do Not Do

- No unapproved experiment,old-root reuse,threshold change or source mixing.
- No physical NPU4–7; no stopping/modifying foreign jobs. A mapping alone does
  not prove occupancy; actual physical processes govern any future admission.
- No additional quality,observer,GDN,profiling or performance run here.
- No invented historical metadata,losslessness,quality pass,full29-Skill
  acceptance or upstream equality. No credential or large raw data in Git.
- No growing this current page into a diary. Archive old checkpoints separately.

## 8. Recovery / Resume Commands

Read AGENTS.md,global handoff,this page,task.json and the selected narrow Skills.
Relevant reports:
- HYPIC_CURRENT_SOURCE_PERFORMANCE_FINAL_20261013.md
- HYPIC_R19_FINAL_QUALITY_REPORT_20261012.md
- HYPIC_R19_QUESTION_LEVEL_INTERPRETATION_20261013.md
- HYPIC_NATIVE_RECOVERY_DISABLED_FAILURE_20261012.md
- SKILL_ACCEPTANCE_SCOPE_REVIEW_20261012.md (dated historical scope review)

Aggregate /cache/cch/hypic-npu03-cpu-binding-fix-20261007/current4429-performance-20261013-audit.json
SHA25667ba6cf14fc9bed993acbdf421eb438f22d56957f3e56baad170a4bb871e53fe.
Remote work must freshly resolve chicaihong01/ma,load host-development and
prove force_direct target identity. Credentials only in connector fields.
No active service needs stopping. If future state conflicts with this page,
inspect exact live ownership and raw terminal receipts before any action.

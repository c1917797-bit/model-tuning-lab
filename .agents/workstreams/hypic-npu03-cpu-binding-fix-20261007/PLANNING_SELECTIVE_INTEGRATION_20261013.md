# Planning-schema selective integration candidate — 2026-10-13

Status: OFFLINE PREFLIGHT ONLY. Not integration-ready,not main-synchronized,
and not evidence of restored GitHub authentication.

The user asked to validate subsequent Skills without further HYPIC accuracy
work. This candidate advances one already-validated maintainer fix toward
authorized main integration without carrying the experiment branch's runtime
changes,failed paths,large history or task-specific records into main.

## Exact candidate

- Target parent: ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2 (cached/pinned main).
- Validated source: 4a95c87b8bf6a59557ad0e45c42e7b0616593caa.
- Sole changed path: .agents/skills/mst-practice-iteration-planning/SKILL.md.
- Before blob: 171e1f401b18dc6aaa4d38a2c3b6b260fca46123.
- After blob: 9be62a7adfec954b2b08d8d3d30e496e676d9ac8.
- Unified diff SHA256: c675e747fa70695e733f413ca877860383a089fb0543b2a719047095cf63383a.
- Bundle: integration/planning-schema/manifest.json and planning-schema.diff.json.

The diff is preserved inside a JSON string so its required blank context-line
spaces are not stripped as prose trailing whitespace. Decoded bytes must match
git diff --full-index TARGET SOURCE -- SOLE_PATH exactly. No hand-edited or
additional patch is accepted.

The source commit also changes two workstream files. Do not cherry-pick that
whole commit or merge this long-running experiment branch as a shortcut.
Only the allowlisted Skill diff belongs to this candidate.

## Existing behavioral evidence

PRACTICE_ITERATION_SCHEMA_ACCEPTANCE_20261008.md records the real main example
failure and the branch schema repair. COMPLETED_ITERATION_REVIEW_20261013.md
adds the real completed-plan lifecycle and seven regressions.
These completed checks are reused; no HYPIC run or unchanged plan test was
repeated to generate a new acceptance claim.

## New preflight evidence

chicaihong01/mc exec-000000000000007a exit0:
- Seven admission controls pass: exact candidate,target drift,extra path,
  wrong source,wrong blob,patch injection and readiness overclaim.
- Read-only git apply --check --whitespace=error-all passes on the retained
  clean exact-main copy /cache/cch/mst-main-onboarding-20261013-f8113561.
- Before/after HEAD,status and Skill blob are identical.
- Reported integration_ready=false,main_changed=false,remote_authenticated=false.

The execution receipt is PLANNING_INTEGRATION_PREFLIGHT_RECEIPT_20261013.json.
This proves applicability to the pinned parent,NOT validation of a future
changed main,completion of an actual merge,or remote reachability.

## Resume after authentication is restored

1. Freshly resolve chicaihong01 route and read current host/workstream policy.
2. Fetch authenticated origin state and prove the target primary is clean and
   synchronized. If target OID differs,invalidate/review this candidate; do not
   override the drift guard or assume the old preflight transfers.
3. Create/resume an authorized named integration workstream and publish its
   remote start checkpoint before product/shared-truth edits.
4. Apply only the reviewed allowlisted diff,carry its evidence and run the
   original validator plus planning example regression on the prospective tree.
5. Push the validated workstream; bind source and exact target parent,resolve
   claims,and serialize integration. Prepare target-owned merged state in that
   merge tree and validate the full tree before commit.
6. Push normally and independently prove remote equality and source provenance.
   Only then report that prepared merged state as remotely verified and advance
   acceptance; do not append an unvalidated state commit to the integration.

Current production GitHub authentication remains unresolved; no repeated failed
push was attempted and no primary ref was changed.
Counts remain12 bounded verified/17 partial. Planning main remains partial.
The broader goal stays incomplete.

Read-only replay from the task repository:

```bash
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/preflight_planning_integration.py --target /cache/cch/mst-main-onboarding-20261013-f8113561
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p test_planning_integration.py
```

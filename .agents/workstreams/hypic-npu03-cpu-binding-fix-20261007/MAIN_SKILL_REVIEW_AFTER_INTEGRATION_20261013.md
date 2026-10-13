# Exact-main Skill review after selective integration — 2026-10-13

## Result and boundary
Published main: 23ec33d7d692bb77d17fb5b81aabacf57adad5c7.
Parent: ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2.
Selected remote source: 06365feb165898a86305296dc007b40ec4e09461.
Six repair files were integrated; no whole HYPIC branch merge occurred.

The planning example defect is closed on exact main. Bounded acceptance covers
one completed selective-repair iteration: stated goal, actual changed file,
validated checkpoint, executable checks, classified lesson destination, and
the documented YAML example. Three controls accept the generated valid plan
and reject old schema/missing checkpoint. A fresh local, no-hardlinks clone
of the published main passed these checks. This is not a fresh GitHub clone
or a new NPU result.

## Evidence
- mc0104: final-tree validation, no-ff commit, normal push and remote equality.
- mc0106: fresh main clone, selected-source checks, 3 planning controls,
  2 direct CLI controls, 9 runtime CPU tests, 29 structural entries.
- mc010f: independent live remote main/source-ref equality.
- mc0117: independent source/merge/receipt audit, replay in the retained clean
  clone, 6 auditor controls (1 valid and 5 invalid), same CPU tests.
- MAIN_REPAIR_REPLAY_RECEIPT_20261013.json retains actual tool output.
- verify_integrated_main_repairs.py checks commit parents, six source blobs/
  modes, completed-plan checkpoint ancestry/content and fail-closed receipts.
- snapshots/planning-case-before-main-23ec33d7.json preserves the earlier
  partial case. Historical observed fields are not rewritten.

## Case reconciliation
28 Skill entrypoint blobs and the registry are unchanged. Only the planning
entrypoint changed. Runtime template/validator assets changed separately and
are explicitly revalidated, not inferred from its unchanged SKILL.md.
All 29 reviewed-current-main references advance to the inspected main.
Only planning is promoted: 12 to 13 bounded verified; 17 to 16 partial.
Existing bounded evidence is reused, not described as newly executed device work.
monkeypatch remains partial: CPU/default-off/fail-fast checks do not establish
real-service disable/uninstall/restart acceptance.

Pre-update case tests failed closed on main drift (23 errors and one hash-test
mismatch caused by the earlier main-drift guard). Older aggregate assertions
also still expected 7/22 and partial onboarding/paper-ingestion despite already
recorded 12/17. Tests now preserve current bounded cases and include an explicit
unreviewed-main rejection control. No provenance/hash guard was removed.
The old planning verifier pins the actual historical main instead of expecting
a newly repaired main to remain broken.

Final metadata gate mc011c passed: 29 case-provenance checks, 25 case tests,
5 current-handoff tests, 6 receipt controls, historical planning replay,
5 completed-campaign route checks, 29 structural entries and diff checks.

## Remaining work
The 16 partial cases retain their own requirement gaps; see skill-cases/*.json.
No HYPIC quality verdict changes, no device retry, no all-Skill acceptance.
The original work branch remains not-ready for whole-branch integration.
Retain the remote repair branch; reclaim its unused local worktree only after
fresh usage/claim checks. No worktree cleanup is claimed by this report.

## Replay
From the original HYPIC worktree:
```sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_integrated_main_repairs.py --replay
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p test_integrated_main_repairs.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_cases.py
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p test_verify_skill_cases.py
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p test_handoff_current.py
```
Use TMPDIR=/cache/cch. No device packages or installations are required.

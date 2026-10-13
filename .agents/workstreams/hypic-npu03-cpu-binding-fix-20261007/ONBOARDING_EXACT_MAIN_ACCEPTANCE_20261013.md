# Onboarding Report — exact-main acceptance2026-10-13

- Repository: /cache/cch/mst-main-onboarding-20261013-f8113561
- Skills:29 registry IDs,29 directories,29 SKILL.md entrypoints; no orphan.
- Agents:0 agents/*/work/backlog.yaml directories.
- Active tasks:0 non-done tasks across that legacy backlog pattern ONLY.
  Ten .agents/workstreams/*/task.json records also exist; this is NOT zero live
  tasks and those historical records are not a fresh host-occupancy inventory.
- Validation: PASS in the exact-main copy; six inventory regression tests PASS.
- Last significant change: ead80810 merge: integrate verified README refresh.
- Structural changes since last session: first session in this isolated copy;
  no prior-session structural diff is claimed.

## Scope and evidence

The human redirected work to remaining Skill validation and explicitly stopped
further HYPIC quality work. This creates a real need to re-orient into the exact
main snapshot before validating further Skills. Plan d7b17384 admitted the
isolated checkout before it was created. Clone operation003b on freshly resolved
chicaihong01/mc completed exit0. Snapshot workflow003d and independent inventory/
focused negative-control replay003e also completed exit0, host Euler.

Pinned main: ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2.
Onboarding Skill blob:a1eb74cee760653f63181f8e4e775a7cf29ee75c.
Registry blob:2611864bbcf719d57920aae03ff9eb85521526b4.
Both actual checkout file blobs were checked, not inferred from filenames.
The clean detached checkout is retained; its shared Git objects depend on the
source checkout. This was a LOCAL clone, not a GitHub authentication or latest
remote-main test. No runtime, source image, model, container or NPU was changed.

## Required workflow actually performed

1. Read the copy's AGENTS.md and maintainer role/canonical sources.
2. Read the entire registry and smallest-relevant-set selection rule.
3. Enumerate all Skill directories; check unique IDs, exact paths, entrypoints
   and orphan/missing cases with an independent inventory function.
4. Check repository docs/adapters: CLAUDE.md and AGENTS.md exist;
   docs/ARCHITECTURE.md absent. Absence is reported, not fabricated.
5. Inspect agents/*/work/backlog.yaml: none. Explicitly identify10 alternative
   workstream task records so the scoped zero is not a live-task conclusion.
6. Run the unchanged exact-main scripts/validate-mst.sh: PASS29.
7. Emit this structured report with count, identity, result and change scope.

Six tests cover valid input, duplicate ID, missing directory, orphan directory,
missing SKILL.md and wrong path. A future nonempty backlog makes the frozen
snapshot replay stop for schema review rather than silently reporting zero.

## Commands and replay

Actual clone (already completed; do not overwrite/recreate the existing copy):
git clone --shared --no-checkout -- /cache/cch/model-tuning-lab-hypic-e2e-20261006 /cache/cch/mst-main-onboarding-20261013-f8113561
git -C /cache/cch/mst-main-onboarding-20261013-f8113561 checkout --detach ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2

Read-only replay from the maintenance repository:
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_onboarding_snapshot.py /cache/cch/mst-main-onboarding-20261013-f8113561
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p test_onboarding_snapshot.py

Actual raw replay records the selected docs and all10 alternative task paths.
The script repeats hash-bound identity checks and runs the original validator;
the tests do not substitute for that real checkout execution.

## Decision and reusable experience

Bounded acceptance for mst-repo-onboarding at the exact pinned main is
supported by this new task. It does not retroactively restore the missing
2026-10-08 GitHub clone/transcript, prove remote authentication, accept all
Skill behaviors, or integrate branch changes into main.

Experience-ingestion destination: verification case and replay script
(classification5). Trigger: resuming work or changing repository snapshots.
Different action: retain a clean exact-commit acceptance copy and input hashes,
and label backlog counts by their storage format. Verification: actual
unchanged main validator plus independent missing/orphan/duplicate controls.
No reusable Skill text or registry behavior was changed in this iteration.

Remaining: other Skills' own functional obligations and authorized integration.
HYPIC quality outcome is not an onboarding prerequisite.

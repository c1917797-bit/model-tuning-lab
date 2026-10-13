# Current-loop handoff and active-state repair — 2026-10-13

Scope: maintain the real HYPIC task's current state after completed quality and
same-source performance. This is not a replacement easy task, a new experiment,
a full loop-Skill acceptance or historical gate repair.
Exact-main loop Skill blob32ae84455395011aa83308e3cc05759aa2206441;
main revisionead80810b7019bdc9ae410ebe883fc5dfbd8f0c2. Branch-only
three-horizon guidance is not retrospectively credited to this main blob.

## Observed defects and checks

0306 ran the existing current-handoff regression before editing: both tests
failed. HANDOFF.md had1417 splitlines (1418 entries including final empty line);
the active_attempt still described running GSM8K rather than current terminal
state. The earlier successful structure/provenance checks had not exercised
this live handoff test. Passing those checks did not establish current-state
coherence. Historical acceptance snapshots remain separately valid.

0308 read the exact candidate arm-result and service-stop and verified the
paired GSM8K audit digest. The candidate completed3 units and released its
exact container,workers and port2026-10-10T17:11:41.241053+00:00.
Arm SHA3814b62c948bdc275cc3ef221678191c1160b97dbe2f7907c545f89f108dfa9b;
paired SHA496f1dfacb3c3a8dd03f8ee07368fb142b432498c0ee5dbb5722e1d4f85fd187.
This was metadata repair, not a live process cancellation.

Repair:
- Move the complete previous handoff content to
  HANDOFF_SNAPSHOT_20261013_0802.md, byte-identical SHA256
  a79dfa7aa634a1f69575c24d56fb0dc03efeecc9a15ef1dee07cfa1d336311cd.
  Existing HANDOFF_HISTORY.md and Git history remain untouched.
- Replace current handoff with a page under160 lines and required ordered sections0–8.
- Clear stale active_attempt; retain its original object and terminal authority
  under retired_active_attempt_20261013. Broad execution remains in-progress,
  integration not-ready; physical4–7 remains forbidden.
- Preserve historical ledger assertions in test_handoff_current.py and update
  current-state assertions to six completed performance phases,source/quality
  boundary,no controller,raw terminal release and exact archive preservation.

0309 passed15 focused tests, historical handoff and loop snapshot replays and
current route checks. Its subsequent provenance check correctly failed because
mst-parallel-workstreams still pinned the previous live test digest.030b found
only that drift; update the live-test evidence digest, not frozen old snapshots.
Current test SHA8654b583ac542036ccc11b0139d0c8ca74b891b00dfe1a6f21b8359de2d047fb.
No quality verdict or Skill acceptance changes.

## Exact-main loop validation obligations

| Obligation | Evidence / status |
|---|---|
| Maintainer structure and registry match | Existing29 structure/provenance replay; recheck after repair |
| Required handoff sections | Current page under160 lines,ordered0–8;focused test |
| Current pass criteria | task.json and immutable quality/performance plans;negative quality retained |
| Architecture/topology orientation and drift prevention | Host routing/physical ownership skills and campaign receipts; prior drift checks are bounded,not universal topology coverage |
| Fresh agent orients,selects,validates and commits/pushes without hidden context | Not proved; this same-session repair is not a fresh-agent trial; authentication unresolved |
| Independent checker rejects bad result | Frozen raw audits and observed0306 current-state failures; no claim of new independent human/agent review |
| Explicit bounded next entry or stop | Offline obligation review only;device campaign closed;no old-root restart |
| Git checkpoint/push | Local checkpoint after checks;remote push not proved and must not be claimed |

The exact-main non-drift contract permits an explicit checkpoint blocker.
It does not make unavailable Git authentication count as a successful push.
No fresh agent is silently simulated by reusing the current agent's knowledge.
Maintain mst-loop-engineering-framework at partial-evidence. The previously
bounded verified handoff case stays scoped to its original snapshot.

## Durable lesson and replay

Experience destination5: verification case. Trigger: a long-running task changes
from active measurement to terminal evidence but distributed state still says
running. Next action: reconcile current pointer against immutable terminal
receipts,archive history byte-for-byte,and run the live handoff test as well as
structural/provenance tests. Do not fabricate missing historical fields or
increase the160-line size limit to make a diary pass.

From the workstream run:
```bash
python3 -B -m unittest test_handoff_current.py test_completed_campaign_routes.py test_summarize_current_source_performance.py
python3 -B verify_handoff_case.py
python3 -B verify_loop_framework_case.py
python3 -B verify_completed_campaign_routes.py
python3 -B verify_skill_cases.py
```
From the repository run bash scripts/validate-mst.sh and git diff --check.
No device action,source change,foreign-task mutation,case promotion or main
integration is included. Remaining20 partial cases retain their requirements.

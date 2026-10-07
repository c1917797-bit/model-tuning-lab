# H8 v6 actual controller failure — 2026-10-07 23:28Z

## Outcome and scope

MAIN operation exec-000000000000109c ended exit1 after 1323.047 seconds.
This is a controller-observation failure, not a proved H8 numerical failure,
paper-wide no-go, E2E result or task-quality result. The original full matrix
still requires 11520 steps; mixed64/model/service remain blocked by that missing
numerical prerequisite. Default OFF and all numerical thresholds are unchanged.

- Source manifest cbe3902c540f0851590336d1b3fa72a83cee06955b801a7e89b030f01b8ec0dc.
- RESULT /cache/cch/qwen36-paper-preparation-20261007/recurrent/MAIN-h8-full-runtime-v6-20261007-001/RESULT.json:
  4bbfb7f7eb931bf37b7a42eac24bd495570dc9f3c1a90efa9b7bea60ab2a9af1.
- Whole original H8_V6_FULL_ORIGINAL_TERMINAL_20261007.json:
  aaa41d47bdf65c3c2b7dd20dc5f59c0afb7ac452f28c2c05279c9e2333e9f630.
- Primary: actual whole-controller RSS sample unreadable.
  Retained measurement error: ProcessLookupError(3, 'No such process').
- 41023 RSS samples; sampled aggregate peak226048KiB (~220.75MiB),
  budget524288KiB; resource_violation=false. This is not an observed RSS
  budget overrun and does not prove every unsampled instant was below budget.
- Old controller catches FileNotFoundError for departed descendants but not
  ProcessLookupError. Exact syscall/PID for this original error was not
  recorded; process-exit race is a hypothesis to test, not an established cause.

## Quiescent partial reports, not completion authority

Independent read10c4 after exact stop found 2189 checked steps, zero failed
steps and 12 complete cases: each of B16/15/14/13 eager160 and graph trials0/1
160. Graph trial2 checked50/64/92/63 respectively. Reports remain status
running; no smaller-batch or lifecycle completion. Max observed output metric
0.0029940119760479044 and max per-head state L2 2.5892022770307797e-7.
These are numerical diagnostics, not token/task precision percentages.

All four RESULT child Refs were captured while children could still update.
Their hashes therefore drifted during cleanup. Actual independent consumer
10c2 failed1/19.428s with Ref bytes drift at consume.py156. Preserve this failure
and old RESULT unmodified; do not regenerate its Ref values or claim consumer
PASS. Stable partial current hashes are recorded by independent10c4 original.
The original source-stage/partial warm prerequisites remain scoped successes.

## Release and memory protection

Independent readonly10c5 exit0/1.330s validated each actual inspect against
its original OWNED record: four exact CIDs stopped/retained/Pid0/noExec/noOOM.
Fresh raw SMI showed no NPU processes; physical4–7 AICore0 and HBM2861–2866MiB.
No external container was stopped and no0–3 mutation occurred.

The previously authorized hugepage release remains exactly32GiB/SPENT:
NUMA0 1GiB pages nr/free439/439, not another release. NUMA3 full474GiB retained,
free450GiB. OVS PID27118/start11471 is unchanged, HugetlbPages25165824KiB.
Fresh MemAvailable116843576KiB (~111.43GiB) fluctuates with other workloads;
only the original58→90GiB immediate delta is attributable to the release.

## Next narrowly supported changes

Recurrent preparer builds a new v7 root, never mutating frozenv6:
prove confirmed descendant departure versus live unreadable/PID-reuse errors
using real short-lived processes, preserve live failure and512MiB/256MiB VAS
limits, then exact-own cleanup/reap before stable failed report/journal/raw
Refs. Mathematics,11520 coverage, guards and thresholds must be byte-pinned
unchanged. MAIN reviews/tests before any new NPU dispatch; no unchanged retry.

SparQ strict006 and W4native002 prepare concurrently for the serial NPU lane.
H8 thin model bridge is still source preparation. MAIN extracted exact
same-image stopped-owned block_table.py with Docker cp stdout tar (10c1 exit0),
14149B SHA b79a46abf8feb0e2ad9e9de64b55e6fc6d3597eadbd903993cbf4e3e74f1f324,
and delivered source plus complete original operation to model-v2 preparer.
Actual Ascend allocator is _reshape_kv_cache_tensors, not a guessed inherited
implementation; no old H16 wrapper is relabelled as H8 integration.

KV cutoff2026-10-08T08:29:54Z and portfolio2026-10-09T11:17:31Z unchanged.
Still no accepted non-HYPIC matched E2E+task candidate. Goal remains active.

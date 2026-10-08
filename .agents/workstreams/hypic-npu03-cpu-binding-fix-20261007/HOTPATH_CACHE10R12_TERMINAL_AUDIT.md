# r12 terminal audit: new eviction-directory source, strict activation negative

- Target: chicaihong01 physical NPU0–3 only; no NPU4–7 use. Controller
  `exec-00000000000018b4` ran 2026-10-08 21:19:31–21:44:19 UTC and
  terminated exit 1 at the predeclared strict activation gate.
- Frozen controller source: model-tuning-lab `64bfa3c`; clean read-only
  HYPIC plugin `c12060cd47e7575ead059983d7a8bb4704165c98`; image
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
  Model index, evaluator and dataset match the frozen r11 identities.
  Full selector and launch contract: HOTPATH_CACHE10R12_STRESS_PLAN.md.
- External immutable root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r12-stress-hypic`.
  19/19 sample indexes 75–91, 107, 111; two one-token observations and
  three max-2048 natural-EOS scored responses per sample; 57/57 unique
  scored responses, exact payload/response hashes and frozen scorer replay.
- Independent auditor: `HYPIC_STRESS_AUDIT_CAMPAIGN=cache10r12 python3 -B
  audit_cache10r11_stress.py`, exit 2 solely for five scored requests
  without four-worker post-repair proof. 52/57 passed. Missing:
  77:1, 77:3, 81:3, 85:2, 88:2. All had unique explicit-boundary joins.
  Request-local logs show plan-unavailable/non-reusable-prefix fallbacks;
  the precise eviction chain for each is not independently proven. Do not
  relabel these five as hot.
- The r11 missing 79:2 and 79:3 are four-worker hot in r12 (API request
  IDs `chatcmpl-9bb20124e3051118` and
  `chatcmpl-90527148dfae5e63`; each has four
  `worker_hot_request_verified` events with 14,760 skipped prefix tokens).
  This is consistent with the scheduler-directory repair but does not prove
  that the repaired branch was exercised: concurrent arrival/eviction order
  also changed. Overall coverage was 53/57 in r11 and 52/57 in r12; do not
  call this a net activation improvement.
- Diagnostic-subset scores: 22/57 correct in r12, versus 27/57 in r11;
  finish reasons r12 stop 44 / length 13, versus r11 stop 45 / length 12.
  By frozen sample/repetition ID, seven answers flipped correct→wrong and
  two wrong→correct; 0/57 full response hashes match across r11/r12.
  In contrast, 38/38 one-token observations match across sources and
  19/19 observation pairs match within each arm. This proves only the
  short deterministic canary. The long outputs already vary within arm:
  among 57 within-arm scored-output pairs, exact SHA agrees 0 times in
  r11 and once in r12. Per-repetition correct counts are 8/9/10 in r11
  and 6/9/7 in r12. Hence the 0/57 cross-source long-output match is
  not by itself evidence of a source regression; source and scheduling
  effects still require a paired quality investigation.
  No same-identity no-cache control or full LongBench/GSM8K paired suite
  exists for this source, so these are not quality or performance verdicts.
  Replay these bounded comparisons with
  `python3 -B compare_cache10r11r12_stress.py` after both independent
  raw auditors; it is not a substitute for a no-cache control.
- Physical worker PID map was 0→387999, 1→388000, 2→388001, 3→388002.
  The 279 guard samples recorded zero foreign PIDs/probe errors. Exact owned
  container `7d083aa3a09669b7cdefddab626a3fb551ee1b025f738e5058759c321ff1063f`
  was removed; the terminal receipt proves port and owned PIDs released.
  Independent post-run `npu-smi`, `ss`, and `docker ps -a --filter id=…`
  also found no NPU0–3 process, port listener or owned container.

## Raw SHA256

| Artifact | SHA256 |
| --- | --- |
| contract.json | `606fd8f5fa9af6a843afb7942712982a3c903abae8007a322bcdf50a7966ce65` |
| arm-result.json | `5248ccba641ac6132e366f74c711ae7e9b96b69e4f466c40e45cacb3c85749b5` |
| hypic-evidence.jsonl | `4a07d50497f730dcd8d3dadd9840ae3f9b47a5e48dbdf4cb96c02a2908adff60` |
| ordered sample manifest | `62d2056f28a492d3e296e748d93aaf7806a8d18b81f081523f4e531987dd1695` |
| lane-guard.json | `da309b4ff0d23cabd198606d2855dbc5949c34013426bfbccb54af1d2872b9dd` |
| service-stop.json | `fc3682c4e0a1c766827e5c486b3a317b67055d7690dd8b3f5533c8ce3b6cee57` |

## Decision and next gate

This is a bounded negative all-hot stress result and a valid NPU canary of
the new source, not a HYPIC paper, quality, performance, or delivery
acceptance. The scheduler-directory defect has a red/green CPU regression;
the NPU run shows the corrected source executes, but the specific causal
repair is not isolated and bounded cache still yields cold fallbacks.
Do not repeat unchanged r12. Before a full matched 0.85 control/candidate
pair, prospectively choose whether the claim is deployed effect with
request-level hot/cold stratification or 100% hot activation; retain the
original c8/2048/127 payload ruler and run only on actually idle physical
NPU0–3.

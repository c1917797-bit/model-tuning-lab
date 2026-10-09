# HYPIC r13 acceptance-gate retrospective

Date: 2026-10-09. This note separates protocol facts from acceptance language;
it does not alter any immutable result or reinterpret a negative score.

## Finding

Yes: this campaign added stricter mechanism-attribution gates than the
historical successful runs used. In particular, the current performance plan
requires per-request scheduler-boundary plus four-worker receipts, and its
strict C1/C2 claim requires 120/120 candidate requests hot across three
candidate rounds. Those are useful for proving that every measured request
used the intended mechanism, but they are not the same as the all-request
deployed result. Previously I spoke about the strict gate as though it were a
single HYPIC pass/fail verdict. That was too coarse and could wrongly turn
partial mechanism coverage into “the algorithm failed.” The report must keep
deployed effect, strict mechanism coverage, and implementation/quality
evidence separate.

The gates were not the cause of the r13 quality regression. The frozen,
independently audited full pair itself scored 230/381 (60.3675%) for no-cache
and 219/381 (57.4803%) for HYPIC-only, a decrease of 2.8871 percentage points.
That all-request score is valid regardless of whether a request has four-worker
proof. Thus the current exact configuration remains REJECT_OR_QUALIFY on
quality even after correcting the overly broad interpretation of the hot-path
gate.

## Which “previous success” is comparable

- The user-supplied HYPIC v0.8.5 reference records Qwen3.5-27B/TP2,
  no-prefix-cache versus HYPIC-only, 32,768 input, 1,024 output, 40 requests
  at concurrency 16. It reports LongBench-v2 54.33% to 55.38% (+1.05 pp) and
  GSM8K 98.67% to 98.50% (-0.17 pp). This is useful prior experience, but its
  model, hardware/runtime, and manually supplied evidence differ; its
  absolute metrics cannot be pooled with r13.
- The completed local Qwen3.6-27B/TP4 NPU0–3 paper run compares PDC+HYPIC to
  PDC-only, not HYPIC-only to no-cache. LongBench treatment mean was +0.5249
  pp inside the measured baseline range; performance gains were modest and
  adoption was rejected because coexistence/C3 requirements were not met.
  This proves a bounded activation/quality experiment, not the current
  no-cache comparison.
- The often-cited 81.12% TPOT reduction on NPU0–3 is the separate
  CPU-binding-off Decode repair with HYPIC disabled. It must not be attributed
  to HYPIC. That attribution boundary should have been made explicit earlier.
- Current r13 is Qwen3.6-27B/TP4, physical NPU0–3, HYPIC-only versus no-cache,
  cache10, explicit 127×3 LongBench-v2 scoring and `max_output_tokens=2048`.
  The 2048 cap was user-requested; it is not an agent-added restriction. A
  cap controls the maximum, not a requirement that every answer reach 2048.
  These different baselines, model versions, and protocols mean the prior
  success cannot overwrite the current negative paired score.

## Gates: necessary versus over-applied

- Same model/image/source/serving flags, matched baseline, dataset hashes,
  and a frozen request/metric denominator are necessary for causal comparison.
- Physical NPU0–3 only, real-process isolation, exact owned cleanup, and
  preserving foreign work are user/environment safety constraints, not
  algorithm hurdles.
- Per-request four-worker proof and 120/120 are strict causal mechanism
  attribution gates. They are appropriate for saying “every scored request
  exercised all four HYPIC workers”; they are too strict if used to erase or
  replace the separate all-request deployed metric. This correction is now
  recorded in the matched-performance plan.
- Fixed 1,024-token performance output and 40-row repeated runs stabilize the
  performance ruler; they are not quality criteria. The quality cap of 2048
  is not a fixed output-length gate.
- A pre-measurement foreign-PID guard failure is environmental invalidity,
  not a HYPIC pass/fail. The phase-6 original attempt remains immutable and
  excluded. One same-protocol retry in a unique root is permitted only after
  a fresh idle check; no scored row or denominator may be selected away.

## Current execution state and next action

The original `hypic-only/repeat3` performance attempt terminated before
service health and benchmark start. Its 22 guard samples observed PID 1579551
on physical NPU3 in foreign container
`efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6`;
its immutable `arm-result.json` has `valid=false` and no metrics. A later
fresh check again found two foreign processes on NPU3. Invocation
`exec-000000000000007c` then stopped at `assert_lane_available` before creating
the retry root, service, or benchmark rows; the retry root remains absent, so
this is not a second measured attempt. The other five performance roots passed
their independent phase audits. Do not stop or modify the foreign task or use
NPU4–7. When a fresh check shows physical NPU0–3 and port 8223 free, run only
the newly enabled `--environmental-retry1` for this exact phase, preserve both
roots, then run the independent six-phase audit.

## Bottom line

Earlier HYPIC evidence supports that the mechanism can activate and has
produced bounded positive/neutral outcomes under other conditions. It does
not prove this r13 comparison. The current r13 deployment quality outcome is
negative; its strict hot-path coverage is also below complete. The remaining
performance phase is not yet a technology failure; it is blocked by real
foreign use of NPU3. Do not call the entire task “successful” based on speed,
or “failed” based only on the stricter per-request gate.

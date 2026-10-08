# HYPIC c8 quality capacity failure and prospective reserve campaign

Decision recorded 2026-10-08 before any reserve-campaign NPU run. The
original 0.9-GPU-utilization quality baseline remains a valid standalone
226/381 control, but it cannot be paired with a candidate that changes the
common serving memory reserve. Preserve the failed treatment root unchanged.

## Observed failure, not an accuracy verdict

- Original candidate operation `exec-00000000000012e3` exited 1 at 09:45:30
  UTC after the sentinel passed four-worker scored hot-path activation. The
  first c8 wave then returned EngineCore HTTP 500 on sample 7; only the
  sentinel's 1 sample/3 scored rows were persisted. No missing row is scored.
- Worker TP2 stack: `material.py:ensure_replay_capacity` refused about
  1.5 MiB temporary GDN replay when only 1016.3 MiB was free against the
  unchanged 1024 MiB safety watermark. The failure is a capacity gate in the
  HYPIC replay path, not an observed external-process collision. Whether
  transient peaks, fragmentation or a longer-run growth issue also
  contribute remains unproven.
- The candidate had 25 clean 10-second physical NPU0-3 guard samples, no
  foreign PID/probe error, and exact container/worker/port/lane release.
  `service-stop.json` SHA256:
  `9c1d7452b29aeb86c83e274253aa67eec9f966abfc2b6c08415b79256467358c`;
  guard SHA256:
  `119fac70a46ca1a8b1b57bc43cf8a6c5f291a2c780b1edcc05da581ade29d644`;
  HYPIC event SHA256:
  `c822ba75383770649332d088c07acd30a172032389f4157953570459b7ea0578`.
  Raw root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-full-hypic`.
- The unchanged service used `--gpu-memory-utilization 0.9`, 10.78 GiB KV
  cache and a reported 616,216-token capacity (14.68x longest-prompt
  concurrency). The failed request was not explained by exhaustion of that
  token capacity; the HYPIC temporary-memory watermark is a separate gate.

## One-variable common-service repair and disproof

Change only the *common* `--gpu-memory-utilization` setting from 0.9 to
0.85 for both new arms. Do not lower the 1024 MiB HYPIC safety watermark,
alter source/weights, reduce c8, shorten the 2048 output cap, skip sample 7,
or touch physical NPU4-7. At 29.49 GiB total device memory this nominally
reserves another 1.47 GiB/card; the logged KV capacity projects to roughly
532k tokens (> 8 x 41,984), but a real service check must confirm it.

1. On a freshly available physical NPU0-3 lane, run a new-root candidate
   `reserve/stress` feasibility gate: sentinel sample 0, then the same first
   c8 wave of samples 1-8 (including failed sample 7), two one-token
   observations and three natural-EOS max-2048 scored requests per sample.
   Require 9/9 samples, 27 scored rows, explicit-boundary/hot coverage for
   all scored requests, four worker-hot PIDs on the sentinel, no foreign or
   unobservable guard interval, and exact release. These 27 rows are a
   capacity preflight, never the final quality denominator.
2. Only if that gate passes, run a **fresh** 127-sample/381-row no-cache
   baseline and then a fresh HYPIC candidate under identical 0.85 common
   serving settings, c8, three repeats, 2048 cap, frozen evaluator/data and
   explicit boundaries. Do not reuse or pool the completed 0.9 baseline.
3. Independently audit row identity, hashes, scorer, one-switch pair seam,
   candidate hot coverage, 10-second guard and exact release. Apply the
   unchanged aggregate nonnegative score and category-cliff ruler. A score
   failure remains a valid rejection/inconclusive result, not a reason to
   change the ruler after seeing scores.
4. Performance evidence at 0.9 remains historical same-lane C1/C2 evidence;
   an end-to-end performance claim for the 0.85 service identity needs its
   own paired repeat check. Full-paper C3 and all-29-Skill validation remain
   separate.

Abort if the stress gate still crosses the watermark, loses scored hot
coverage, intrudes on another process, or fails to release. Preserve its raw
root and diagnose the new first failure; do not silently step down the
watermark, mark incomplete rows correct, or retry in the same root.

## Exact new-root entry points

Run only after fresh AWMCP target/physical-lane ownership checks. Each
controller refuses an existing attempt root and runs one arm at a time.
Use a persistent AWMCP operation handle; do not background a second copy.

```sh
HYPIC_HOTPATH_QUALITY_CAMPAIGN=reserve HYPIC_HOTPATH_QUALITY_ARM=hypic-only HYPIC_HOTPATH_QUALITY_MODE=stress python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_full.py
python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_stress_audit.py
HYPIC_HOTPATH_QUALITY_CAMPAIGN=reserve HYPIC_HOTPATH_QUALITY_ARM=no-cache HYPIC_HOTPATH_QUALITY_MODE=full python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_full.py
HYPIC_HOTPATH_QUALITY_CAMPAIGN=reserve HYPIC_HOTPATH_QUALITY_ARM=hypic-only HYPIC_HOTPATH_QUALITY_MODE=full python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_full.py
HYPIC_HOTPATH_AUDIT_CAMPAIGN=reserve python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_audit.py
```

The full-arm audit requires both released 127/381 roots and writes only the
external `hotpath-quality-reserve-full-audit.json`. The partial auditor can
inspect persisted full-arm rows with
`HYPIC_HOTPATH_AUDIT_CAMPAIGN=reserve` and `--arm no-cache` or
`--arm hypic-only`; a partial pass is never a final score.

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

## First reserve stress attempt: external interference, not capacity evidence

`exec-00000000000012f9` exited 1 at 2026-10-08 10:07:06 UTC. It started the
0.85 HYPIC service, but before the serialized sentinel completed the guard
detected PID 1762147 on physical NPU0 at 10:06:29 UTC. This PID was not one
of the four expected workers [1684018, 1684019, 1684020, 1684021]. The guard
recorded 18 samples, one foreign event and zero probe errors; controller
persisted 0/9 samples and 0/27 scored rows. Exact owned container, worker,
port and NPU release passed. No quality or capacity pass/fail can be inferred
from this interrupted attempt. The transient PID had exited before a process
tree/cgroup lookup, so its owner is unproven. Separately observed active
operator tasks on this shared host explicitly target NPU0/1; this is a
collision risk, not proof of this PID's origin. Do not stop those tasks.

Raw root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-reserve-stress-hypic`.
arm-result SHA256:
`6c71de2f884646cf469d6f55e4561af3fdc028be3acc4b43690030dfc9bf62e7`;
lane-guard SHA256:
`0379426f27fce670bd24a83f1c00e33eee16898584979f67f00028a3888ac82f`;
service-stop SHA256:
`ec0c2a9eaf32e70bfcd3628cb0921113ffec312cff1f21e3b093b9fed178f7fe`.

The same failed attempt nevertheless supplied a bounded startup-capacity
observation: its retained service log (SHA256
`f702b845bffd5dce6e30dec1232b6df52589931cf3a279858899cec427e10587`)
records the actual 0.85 launch, 9.31 GiB available KV memory, a 532,248-token
GPU KV cache, and a logged 12.68x maximum concurrency for a 41,984-token
request. That validates the projected KV allocation and nominal c8 admission,
not the dynamic HYPIC replay reserve under nine completed stress samples.
The sentinel began but no sample completed before the external-PID abort.
The two physical `npu-smi` snapshots at service health show HBM usage on
NPU0-3 of [28536, 28535, 28537, 28536] MiB for the original 0.9 candidate
versus [27036, 27036, 27038, 27036] MiB for the 0.85 attempt. Thus the
observed startup reservation fell by approximately 1,500 MiB per card,
consistent with the one-variable change. Snapshot SHA256 values are
`7cc59a110f64112ccd0a02a15a96416a645d050c85c184f1a1b85797ed243faa`
and `17d1de12d9cdece0efa1c45cc4a40c3c0bbb8cad52e7e699d1f927ad3d67a636`,
respectively. Health-time HBM is not peak c8 free memory or a replay pass.

The only authorized next stress root is `reserve2/stress` below. Before
launch, inspect physical 0-3 use and active job configuration over a quiet
window; an instantaneous empty snapshot is insufficient. Abort on any new
foreign process without deleting its container or retrying the same root.

## Exact new-root entry points

Run only after fresh AWMCP target/physical-lane ownership checks. Each
controller refuses an existing attempt root and runs one arm at a time.
Use a persistent AWMCP operation handle; do not background a second copy.

```sh
HYPIC_HOTPATH_QUALITY_CAMPAIGN=reserve2 HYPIC_HOTPATH_QUALITY_ARM=hypic-only HYPIC_HOTPATH_QUALITY_MODE=stress python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_full.py
HYPIC_HOTPATH_QUALITY_CAMPAIGN=reserve2 python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_stress_audit.py
HYPIC_HOTPATH_QUALITY_CAMPAIGN=reserve HYPIC_HOTPATH_QUALITY_ARM=no-cache HYPIC_HOTPATH_QUALITY_MODE=full python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_full.py
HYPIC_HOTPATH_QUALITY_CAMPAIGN=reserve HYPIC_HOTPATH_QUALITY_ARM=hypic-only HYPIC_HOTPATH_QUALITY_MODE=full python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_full.py
HYPIC_HOTPATH_AUDIT_CAMPAIGN=reserve python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_audit.py
```

The full-arm audit requires both released 127/381 roots and writes only the
external `hotpath-quality-reserve-full-audit.json`. The partial auditor can
inspect persisted full-arm rows with
`HYPIC_HOTPATH_AUDIT_CAMPAIGN=reserve` and `--arm no-cache` or
`--arm hypic-only`; a partial pass is never a final score.

## Hot-path evidence granularity discovered before reserve2

Read-only inspection of the retained pilot-2 and failed full-candidate event
streams on 2026-10-08 found that `explicit_segment_boundary_active` has a
request ID, while `complete_hybrid_repair` and `worker_hot_path` carry only
batch-level counts/PIDs. The current independent auditor joins every scored
request to its explicit-boundary event, proves the serialized sentinel reached
all four workers, and checks aggregate verified-hot counts. Those checks do
not, by themselves, prove that each concurrent scored request individually
completed a hot repair: a warm request could contribute to the aggregate.
Preserve the predeclared per-scored-request hot-coverage requirement as open
until request-correlated runtime evidence or an equivalently discriminating
independent check exists. A completed reserve2 stress or full pair can still
establish capacity, paired scores, isolation and release at their actual
scope; do not relabel aggregate coverage as per-request proof.

# HYPIC c8 material-cache failure and prospective cache10 gate

Decision recorded 2026-10-08 after reserve2 failed and before any cache10 NPU run.
Read HOTPATH_CAPACITY_REPAIR.md for the earlier 0.9 watermark and 0.85
external-interference attempts. None of their partial rows form a quality
denominator.

## What failed

The replacement 0.85 stress operation `exec-000000000000134f` exited 1 at
11:22 UTC after its serialized sentinel passed four-worker scored hot-path
activation. Sample 4 returned EngineCore HTTP 500 during the first c8 wave.
Only 1/9 samples and 3/27 scored rows were persisted. All 27 physical
NPU0-3 guard samples were clean; exact container, worker, port and lane
release passed. The failed root is
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-reserve-stress2-hypic`.

The service log SHA256 is
`6d0a3c7ce668a6cb39fa324bc0adc648017c97c09377e3c1031075735f3b34e9`.
Contract, arm-result, guard and stop SHA256 respectively:
`5d9e61ba67f332f973e2e651b1e2a5269c01d5703df4f5ee641828a91363ff66`,
`f1fa039077b86a49cad77adb53de796bb2f16d4fd5889e014c665f19f8a8c9ac`,
`0eca21afbe8091c6f23585a95f5147ef3456de66ab6160d38f39d772a198151c`,
`f3ba346c470afae0f55a961ad3dab413854c73a9d040af87a337e06289bca349`.

This is not the earlier NPU free-memory watermark error. All four TP workers
raised `HYPIC PI hit lacks GDN (conv,S,T)` at layer 0. A materialization
report records one eviction immediately before the crash. The unchanged
plugin configures four materialized segments and 1536 MiB per worker; a
complete prefix in this wave projects to about 328.6 MiB, and eight distinct
samples are concurrent. Cache-residency/lifecycle is the leading hypothesis.
The event does not identify the evicted hash, so an async scheduler race is
not yet excluded.

## Frozen cache10 disproof

Change the common material-cache capacity to ten segments and 3584 MiB in
both fresh arms. Keep 0.85 GPU utilization, the 1024-MiB NPU watermark,
source/image/model/evaluator/data, c8, three scored repeats, 2048-token
output cap, and physical NPU0-3 unchanged. Ten observed prefix projections
fit under 3584 MiB per worker; host available RAM was 110 GiB before this
decision. The stress preflight has the same nine samples (including 7),
27 scored rows, serialized four-worker sentinel, aggregate hot evidence,
continuous guard, and exact release gate. Per-request hot attribution is a
separate open evidence gap and must not be inferred from aggregate counts.

Use only the new stress root
`quality-context-41984-hotpath-cache10-stress-hypic` after a fresh shared-host
lane check. If it fails, preserve the raw root and diagnose the first error;
do not widen the cache again without a new technical explanation. If it and
the independent stress audit pass, run fresh matched 127-sample/381-row
baseline and HYPIC roots named
`quality-context-41984-hotpath-cache10-full-baseline` and
`quality-context-41984-hotpath-cache10-full-hypic`. Do not reuse either
the 0.9 baseline or incomplete 0.85 arms. Re-run paired performance for the
new service identity before claiming its latency gain.

```sh
HYPIC_HOTPATH_QUALITY_CAMPAIGN=cache10 HYPIC_HOTPATH_QUALITY_ARM=hypic-only HYPIC_HOTPATH_QUALITY_MODE=stress python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_full.py
HYPIC_HOTPATH_QUALITY_CAMPAIGN=cache10 python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_stress_audit.py
HYPIC_HOTPATH_QUALITY_CAMPAIGN=cache10 HYPIC_HOTPATH_QUALITY_ARM=no-cache HYPIC_HOTPATH_QUALITY_MODE=full python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_full.py
HYPIC_HOTPATH_QUALITY_CAMPAIGN=cache10 HYPIC_HOTPATH_QUALITY_ARM=hypic-only HYPIC_HOTPATH_QUALITY_MODE=full python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_full.py
HYPIC_HOTPATH_AUDIT_CAMPAIGN=cache10 python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/hotpath_quality_audit.py
```

## First cache10 stress result (2026-10-08 11:51 UTC)

Operation `exec-000000000000136c` exited 0 on physical NPU0-3: the
serialized sentinel and all nine declared samples completed, yielding 27
scored rows at c8/three repeats/2048-token cap. The service was released.
Independent audit `exec-0000000000001375` exited 0 with `stress_pass=true`,
9/9 samples, 27/27 rows, 58 clean lane-guard samples, and exact release.
Contract SHA256 is
`3fc03c4df091c030eddb1121c2f12052ac1e49caf71721680b1130654805f7a1`;
arm-result SHA256 is
`38cd5d5437a3f60a3a5151f6c347b10623572f64e0e16a7c8a4e993bc1fb3798`.
This passes the predeclared concurrency/capacity stress gate and disproves
reproduction of the earlier c8 crash under this changed capacity. It does
not by itself identify which evicted segment caused the old failure, prove
per-request worker-hot attribution, or establish full 127-sample quality.
Next run only the missing full candidate and determine whether the previous
0.9 control is sufficiently comparable for a descriptive reference or a
fresh matched 0.85 control is required for a formal paired verdict.

## First full candidate invalidated by lane interference (2026-10-08)

Operation `exec-000000000000137a` started from source commit `a4d05be` on
physical NPU0-3. The sentinel completed, but only 1/127 samples and 3/381
scored rows were persisted. The guard made 199 observations, recorded 31
foreign-process observations (12 distinct PIDs on physical NPU1 or NPU3),
with no probe errors. The first foreign observation was at 12:07:41 UTC.
This invalidates isolation and any quality comparison; it does not diagnose
the HYPIC cache or score. Exact owned container/worker/port release passed
at 12:38 UTC after stopping only the owned service. Preserve raw root
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10-full-hypic`.
Contract, arm-result, lane-guard and service-stop SHA256 respectively:
`9106bfb4a27e6dbd85d88fde76f126a1a9807a889d600e212cb6f9c4705e74c3`,
`aea7b09e7f87a63ecd7612b8ea1840f72026288380265c445f3850a4f667771c`,
`7fec65e7007e03c12620fc453e3dfe13aceaba9aa8fee228f4a4c7547dc17956`,
`3a3a94b70f97d84be01728cb6c8483f977446d20db83c1dcbdf749be5f62720d`.

The guard observed the conflict but the controller checked it only when a
whole sample returned; long in-flight requests delayed termination by over
30 minutes. The prospective repair polls the guard during requests, cancels
queued work and stops only an identity-verified owned container to unblock
the active requests. This is an execution-control repair, not a frozen
algorithm/quality-ruler change. Verify it offline and use a new evidence root
only after a fresh lane check; do not claim full quality from the earlier
stress pass or this invalid arm.

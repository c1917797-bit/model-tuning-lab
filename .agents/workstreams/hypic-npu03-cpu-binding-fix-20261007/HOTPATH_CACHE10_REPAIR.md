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

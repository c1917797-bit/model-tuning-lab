# HYPIC phase-6 retry9 terminal audit

Retry9 was the frozen `hypic-only/repeat3` performance phase on physical
NPU0–3, launched asynchronously as operation
`exec-0000000000000211` after an immediate idle preflight. The controller
terminated before service health because its continuous lane guard observed
foreign PID `4049211` on physical NPU2 at `2026-10-09T11:24:13.109216Z`.
Cgroup attribution at detection identified container
`efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6`
(`cannbench_ds`). The human owner is not established.

The guard captured 12 samples with no probe errors. There were zero scored
requests, no service-health receipt, and no performance result. The controller
removed only its exact retry9-owned container
`bf94db287a41e4d6aa1e23c66cd150f266f920ad2220064fd98911cfeed01ec6`; the
foreign container was untouched. Post-cleanup, physical NPU0–3 had no
reported process and port 8223 was free.

A later snapshot at `2026-10-09T11:25:22Z` observed PIDs `4065160` and
`4052420` on physical NPU1. Both exited before their `/proc` cgroup could be
read, so their container/human owner is unknown. These further establish
intermittent external lane use, not a HYPIC outcome.

The immutable root is
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry9`.

Evidence SHA-256:

- Contract: `908da8facd35743aa86ea3c0109c1f61f2a7b94a0c2027e4d402e4e634dbbe69`
- Arm result: `78c0e7ac42b7318da4fec5594be535797ec0cfa8d5ab292d594401c761faa928`
- Guard: `b6c91535d7949a33fd5b116c839ddfa0662399f030c987cd9b10945391501153`
- Pre-health release: `1dc86a50bc3097f136a1989a448f8a53dbefe6f86d922062175a8e0178046654`

Do not modify foreign work or loosen the isolation guard. Resume this same
frozen phase after the user coordinates or a fresh actual-idle preflight
passes. The r13 quality rejection remains unchanged.

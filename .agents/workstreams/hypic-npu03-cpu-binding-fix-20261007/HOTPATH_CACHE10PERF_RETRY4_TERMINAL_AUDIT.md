# HYPIC phase-6 retry4 terminal audit

- Date: 2026-10-09 UTC; target: `chicaihong01/ma`, physical NPU0–3 only.
- Immutable raw root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry4`.
- Frozen treatment: final `hypic-only/repeat3`, c16, input 32768/output cap 1024, 40 measured requests, two warmups, TP4, source `c12060cd47e7575ead059983d7a8bb4704165c98`, official image `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`; no metric, denominator, threshold, or workload change.
- Contract SHA256: `ea583f6e41ed38f76766def75d2592c1812e2220338115c89677211b6e3f22e9`.
- Arm result SHA256: `5a93ce9402e9ae20c6370cae16f32c1674e57867bd477b33241f7190cd6bc88d`.
- Performance artifact SHA256: `323ced3b25c2e0ac1bfaed2f69e3dbfe369a9617f0d0d6488b9fe5fb2a4e13a5`.
- Benchmark command SHA256: `f0b54998e4077f3c7a56f90ffad629279d91ff74cd3d411e975a547cbbd2e8ae`.
- Continuous guard SHA256: `0551cda9bcdf0a9394a55ed777241610b75a0e89924fd2df26c818b9bb177480`.
- Exact service-stop/release SHA256: `0d8c3b4bf4be2d3761df618e66fdc4edc3f291f58ef4d64f2748dd5a1b8bfec3`.
- Source attestation SHA256: `6a1bd87df57ee2665f578a80291fd388232ef6cd1a5fa975295382474baba2a2`.
- HYPIC event evidence SHA256: `1bac011528b752a4d8a804caca20c9725c933827e68b857e5e0220dc39a70155`.
- Guard: 120 samples, zero probe errors; foreign PID 3079008 from container `efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6` appeared twice on physical NPU1 at 09:50:47 and 09:50:51 UTC. This container is `cannbench_ds`; no human launcher is inferred.
- Partial benchmark artifact: 40 rows were materialized; 16 requests returned `ok`, 24 were refused after guard-triggered service shutdown. Only 15 successful rows contain 1024 output tokens; one response was incomplete. The run is contaminated and invalid for performance comparison; do not calculate or publish its metrics or use its 16 responses in the six-phase audit.
- Exact owned service container `7039de53a1eaad5721207a28bba5ee65abaff5969f90e8ee91fe2a8b8e932d7b` was removed. The stop receipt records service health reached, owned NPUs released, and port 8223 released. A post-cleanup snapshot at 09:53:47 UTC showed no processes on NPU0–7, port 8223 free, and no retry4 controller/service process.
- Classification: environmental mid-run isolation failure, not HYPIC performance evidence. The frozen r13 quality decision remains `REJECT_OR_QUALIFY` (230/381 to 219/381, -2.887 pp); strict hot coverage remains `FAIL` (368/381). The six-phase performance audit remains incomplete because phase 6 has no valid candidate replicate.
- Budget: retry4 was the one user-authorized additional recovery root. No retry5 is authorized. Preserve all raw artifacts and do not stop or modify foreign workloads.

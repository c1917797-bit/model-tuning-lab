# HYPIC NPU0–3 Decode communication root-cause diagnostic

Branch: `work/hypic-npu03-comm-root-20261007`. Parent evidence branch commit: `a8f1123`.

The old 4–7 and current 0–3 HYPIC absolute effects are similar; only the current lane has a large common Decode floor. This successor diagnoses that floor, not a new HYPIC candidate or a revised acceptance gate.

Current stage: diagnostic measured, underlying source-level trigger inconclusive. Physical NPU0–3 only; NPU4–7 forbidden. Do not touch the pre-existing `agentgpu-910b4-qwen35-4b-v0` sleep container. Canonical checkout is dirty with unrelated DAMP/KVBuffer work; this independent clone is the diagnostic checkout.

Raw source: `/cache/cch/hypic-qwen36-e2e-2048-20261006/profiles`. The previous formal 40-request benchmark remains frozen. Read-only trace shows about sixteen 22 ms AllReduce events per Decode step on three exported ranks, plus many roughly 10 us calls. A diagnostic 4-request/128-output capture is not formal service timing. Rank 2 Decode export is incomplete. No physical cause or optimization is yet proven.

Plan and abort criteria: `.agents/experiments/exp-20261007-hypic-npu03-comm-root.yaml`.

Findings: `REPORT.md`. Four-rank standalone HCCL and minimal NPUGraph AIV probes were fast and their exact-name `--rm` containers were recovered. The old raw rank-2 SQLite database, despite missing CSV export, localized the first observed divergence to a roughly 22.4 ms MEM_WAIT_VALUE between reshape_and_cache and FusedInferAttentionScore; ranks 0/1/3 pass the analogous wait in about 1–2 us and are then charged about 22.7 ms in AllReduce while rank 2 arrives late and finishes its AllReduce in about 0.009 ms. Notification producer is unknown. Do not attribute this to physical HCCS, HYPIC, a faulty NPU2, or a specific source line without a service-scoped intervention that changes the measured latency.

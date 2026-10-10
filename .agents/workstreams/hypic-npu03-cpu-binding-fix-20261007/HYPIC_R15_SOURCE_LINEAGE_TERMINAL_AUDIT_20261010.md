# r15 source-lineage E2E diagnostic — terminal

2026-10-10 UTC. The preregistered HYPIC-on original/current source comparison completed on physical NPU0–3. It is a **selected eight-sample diagnostic**, not a full quality verdict or a revision of r13.

Both controllers exited 0: original `exec-000000000000002b`, current `exec-000000000000003a`. Each persisted 8/8 LongBench-v2 samples and 24/24 max-2048 c8 scored responses. The independent auditor `audit_r15_source_lineage.py` exited 0 after checking paired request hashes, recomputed scores, exact live source attestations, four physical worker PIDs, 175/170 clean continuous isolation samples, and exact owned container/NPU/8223 release. Immutable raw paired audit: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hypic-r15-source-lineage-audit.json`, SHA256 `2a2ed7f97696183eb39b1bdfe97e28015d1265b5d0074ccde41e472b232226cf`. Arm-result SHA256 original `9d348e9fc6c948a3f0f0157ec5caa2b36da7e9bf08cebbe5924c8b17aead7dbd`, current `1b734082e0b2400d4dba3222fd8da9c1bdf8daa3d93516cf936a324a56f393f1`.

| Source | Correct / 24 | Length finishes | Activation evidence |
| --- | ---: | ---: | --- |
| Original `3ad0967` | 13 | 1 | 24 aggregate verified hot repairs; no per-request worker telemetry |
| Current `c12060c` | 10 | 2 | 24 aggregate repairs; separate read-only request-ID join proves 24/24 four-worker hot |

Per-index original→current correct counts: 55 `0→0`, 6 `3→2`, 30 `3→2`, 40 `0→1`, 49 `2→1`, 26 `1→1`, 50 `1→0`, 48 `3→3`. Directional rescue is mixed, not universal: one preselected regressed case improves on current code, and the original source itself varies against r13's same-index results. The post-hoc-selected subset, sequential service order and natural long-output variability prohibit a population estimate or unique causal-line attribution. The result strengthens a *source-sensitivity hypothesis*, nothing more.

The frozen r13 full quality result remains 230/381→219/381 (`REJECT_OR_QUALIFY`); its separate six-phase performance remains valid. The next decision-changing test is the newly preregistered **full** max-2048/c8 no-cache versus HYPIC-only pair with the original source in both arms (r16). It requires a fresh matching no-cache baseline because r13 mounted the changed source. Its only serving switch is HYPIC enablement. Do not pool r15 selected rows with r13 or r16, or claim that r15 proves HYPIC adoption.

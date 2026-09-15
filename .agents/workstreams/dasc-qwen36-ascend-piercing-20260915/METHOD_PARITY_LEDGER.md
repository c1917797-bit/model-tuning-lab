# DASC Method Parity Ledger

| Paper stage | Causal role in paper result | Target status | Current parity label | Evidence needed |
|---|---|---|---|---|
| Static retention horizon from weights | Selects long-horizon GDN heads without calibration prompts | Implemented and materialized on four TP workers in the v9 physical-cache attempt | faithful formula locally; full paper parity still open | Runtime plan uses local `A_log`, `dt_bias`, representative `a=-0.3`, and epsilon `1e-3`. Retention counts are heterogeneous per layer and aligned across TP ranks. |
| Head-wise GDN selection | Defines compressed temporal state units for Qwen-GDN | Implemented for complete local temporal heads | faithful granularity locally | Unit tests cover retained-head packing/expansion; v9 physical-page evidence covers four worker pids. End-to-end service semantics remain gated by v12. |
| Ragged temporal checkpoint layout | Converts selection into memory capacity gain | Plugin-owned heterogeneous physical pages implemented and bound in v9 | Ascend derivative, runtime reached | v9 emitted 12 `physical_cache_bound` rows over four worker pids with compact pages 408576-605184 bytes versus 1588224 dense bytes and 160 admitted blocks. The service did not complete because of the now-fixed hybrid group ordering bug. |
| Dense state checkpoint baseline | Denominator retaining complete mixed-precision recurrent checkpoint | Dense control v10 completed graph capture and exact short response | startup denominator available; formal benchmark pending | Freeze the same image, model, HBM budget, prefix caching, workload, and three-run ruler before timing. |
| DASC-NR load policy | Zero-fill omitted local units with no extra model compute | Dense-storage numerical canary verified on physical NPU4-7 | numerical reachability only; performance rejected | 192 restore events covered 48 GDN layers x 4 workers, output matched control, and the cache-reuse request regressed 5.095%; retain as negative evidence, not a performance candidate. |
| DASC-WR load policy | Refresh omitted units using bounded suffix replay | Related Tail-Replay code exists but not integrated | later derivative unless exact | Requires suffix replay source, boundary data, and live cache write path. |
| TP-balanced placement | Avoids one rank limiting checkpoint capacity | Cross-rank geometry alignment implemented; paper-style payload rebalance is not | derivative alignment only | v9 has four `tp_geometry_aligned` events. Do not claim paper-equivalent TP balancing without proving placement and per-rank limiting capacity. |
| Fixed-HBM cache-fill/replay benchmark | Converts smaller checkpoints into fewer misses and lower TTFT | Not run | pending | Controlled fill/replay workload on physical NPU4-7 with cache telemetry. |
| End-task quality | Ensures compressed checkpoint does not break reasoning | Exact-output numerical canary passed; formal task quality not run | local adapted gate | v12 requires deterministic shared-prefix reuse. A later baseline/candidate quality run must exercise the cache-hit path, not merely unique no-hit prompts. |

## Algorithm Identity

The current identity remains `DASC-GDN Ascend derivative`. The local formula,
GDN head granularity, and compact physical representation are implemented, but
the paper's TP-balanced placement and full cache-fill/replay performance and
quality chain are not yet proven. The label may become `faithful-port` only
after those remaining stages are implemented and measured.

## Delivery Boundary

All implementation must live in the plugin/monkeypatch layer and run against the installed Ascend serving stack. Direct upstream edits to vLLM, vLLM-Ascend, CANN, model weights, or base images are out of scope for delivery and may only be used as read-only references.

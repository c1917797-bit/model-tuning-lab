# DASC Method Parity Ledger

| Paper stage | Causal role in paper result | Target status | Current parity label | Evidence needed |
|---|---|---|---|---|
| Static retention horizon from weights | Selects long-horizon GDN heads without calibration prompts | Implemented in the numerical canary; not run on live workers | faithful formula pending NPU proof | Runtime mask uses local `A_log`, `dt_bias`, representative `a=-0.3`, and epsilon `1e-3`; prove TP-local head-axis mapping. |
| Head-wise GDN selection | Defines compressed temporal state units for Qwen-GDN | Plausible | faithful-port if same formula and granularity | Verify local GDN unit corresponds to complete head state in Ascend cache. |
| Ragged temporal checkpoint layout | Converts selection into memory capacity gain | Not yet implemented | pending | Prove store/load path and offsets; compute per-rank bytes including conv state. |
| Dense state checkpoint baseline | Denominator retaining complete mixed-precision recurrent checkpoint | Not frozen | pending | Freeze dense cache path, memory budget, hit telemetry, and baseline TTFT. |
| DASC-NR load policy | Zero-fill omitted local units with no extra model compute | Plugin numerical canary implemented; software syntax/config gates pass; NPU not run | numerical canary only | Intercepts only new/resumed prefix-state copies, preserves dense conv state, copies retained temporal heads, zero-fills omitted heads, and emits per-worker evidence. |
| DASC-WR load policy | Refresh omitted units using bounded suffix replay | Related Tail-Replay code exists but not integrated | later derivative unless exact | Requires suffix replay source, boundary data, and live cache write path. |
| TP-balanced placement | Avoids one rank limiting checkpoint capacity | Not yet implemented | pending | Need TP shard ownership and possible all-to-all or storage-pool design. |
| Fixed-HBM cache-fill/replay benchmark | Converts smaller checkpoints into fewer misses and lower TTFT | Not run | pending | Controlled fill/replay workload on physical NPU4-7 with cache telemetry. |
| End-task quality | Ensures compressed checkpoint does not break reasoning | Not run | local adapted gate | Use local GSM8K/LongBench-style gate after cache-hit path works. |

## Algorithm Identity

Until the full store/load and benchmark chain is reproduced, local work is `DASC-GDN Ascend derivative`. It may become `faithful-port` only if the same horizon formula, GDN head granularity, dense denominator, ragged checkpoint semantics, and cache-hit serving protocol are implemented and measured.

## Delivery Boundary

All implementation must live in the plugin/monkeypatch layer and run against the installed Ascend serving stack. Direct upstream edits to vLLM, vLLM-Ascend, CANN, model weights, or base images are out of scope for delivery and may only be used as read-only references.

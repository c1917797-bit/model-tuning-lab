# EPD-Serve — Ascend piercing report

## Current decision

- Paper: arXiv:2601.11590v1.
- Target: Qwen3.6-27B, vLLM/vLLM-Ascend 0.23.0, CANN 9.1, four physical
  Ascend NPU4-7.
- Delivery boundary: explicit opt-in orchestration/proxy plugin.
- Status: applicability gate in progress; no performance or accuracy claim.

## Initial mapping

| Paper mechanism | Current target evidence | Gate |
| --- | --- | --- |
| Separate multimodal Encode | Checkpoint includes a vision encoder | Frozen workload must actually contain media |
| Separate Prefill and Decode | vLLM-Ascend already supports P/D transfer | Must isolate a distinct EPD contribution |
| Encoder-cache transfer | v0.23 imports vLLM EC-transfer hooks | Must prove Qwen3.6 support and live transfer |
| Layerwise KV transfer | Mooncake layerwise connector exists upstream | Existing capability, not candidate gain |
| Multi-instance scheduling | EPD proxy examples exist upstream | Must fit the same four-card resource envelope |

## Evidence boundary

Paper-level throughput claims come from high-concurrency multimodal workloads.
They do not predict a gain for a text-only fixed-output benchmark. Before using
NPU time, this workstream must prove both an active Encode stage and a feasible
same-four-card deployment. If either is absent, the valid result is a scoped
applicability no-go, not an attempted microbenchmark.

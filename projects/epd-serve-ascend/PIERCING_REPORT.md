# EPD-Serve — Ascend piercing report

## Current decision

- Paper: arXiv:2601.11590v1.
- Target: Qwen3.6-27B, vLLM/vLLM-Ascend 0.23.0, CANN 9.1, four physical
  Ascend NPU4-7.
- Delivery boundary: explicit opt-in orchestration/proxy plugin.
- Status: rejected at the workload applicability gate; no performance or
  accuracy claim.

## Initial mapping

| Paper mechanism | Current target evidence | Gate |
| --- | --- | --- |
| Separate multimodal Encode | Checkpoint includes a vision encoder, but all accepted requests are text-only | Inactive in frozen workload |
| Separate Prefill and Decode | vLLM-Ascend already supports P/D transfer | Existing upstream feature, not EPD increment |
| Encoder-cache transfer | v0.23 imports vLLM EC-transfer hooks | No encoder payload exists in frozen workload |
| Layerwise KV transfer | Mooncake layerwise connector exists upstream | Existing capability, not candidate gain |
| Multi-instance scheduling | EPD proxy examples exist upstream | Must fit the same four-card resource envelope |

## Evidence boundary

Paper-level throughput claims come from high-concurrency multimodal workloads.
They do not predict a gain for a text-only fixed-output benchmark.

## Frozen workload evidence

The existing accepted performance protocol uses raw text completions with input
length 32768, a 16384-token shared prefix, concurrency 16 and fixed 1024-token
output. The final LongBench-v2 and GSM8K evaluations are also text-only. None of
these requests contains an image, video or audio payload.

The model's `vision_config` proves architectural capability, not runtime
activation. With no media payload there is no Encode work to isolate or
prefetch. EPD-specific E-to-P transfer and modality-aware routing therefore
cannot improve the frozen workload.

## Final decision

Reject EPD-Serve for this acceptance protocol before consuming NPU time. Any
remaining P/D disaggregation is already available in vLLM-Ascend v0.23 and is
not the paper's distinct Encode-stage mechanism. Running it under an EPD label
would produce an invalid attribution.

No candidate was implemented, so no E2E performance or task-accuracy result
exists. The decision is scoped: EPD-Serve remains relevant for a separate,
explicitly multimodal high-concurrency benchmark with a same-resource
deployment contract.

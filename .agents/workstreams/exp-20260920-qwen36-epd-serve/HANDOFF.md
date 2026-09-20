# EPD-Serve — Qwen3.6/Ascend piercing

## Status

- Stage: completed / rejected at the workload applicability gate.
- Start: 2026-09-20.
- Hard timebox: 24 hours.
- Queue position: 8. HYPIC remains the previously completed successful template.
- Resource lane if needed: physical NPU4-7 only.

## Paper and target fit

EPD-Serve separates multimodal Encode, Prefill and Decode instances and adds
feature prefetch, hierarchical KV transfer, scheduling and co-location. The
installed checkpoint is a `Qwen3_5ForConditionalGeneration` model with an
explicit vision configuration, so architecture fit is possible.

The pinned vLLM-Ascend v0.23 source already contains EPD examples,
encoder-cache transfer hooks and Mooncake layerwise P/D transfer. These are
upstream capabilities and cannot be counted as new candidate gains.

## Predeclared decision gate

1. Freeze and inspect the exact performance workload. If it has no media input,
   Encode does no work and the paper's distinct EPD mechanism cannot yield the
   claimed benefit.
2. Separate EPD from ordinary P/D disaggregation. Do not relabel an existing PD
   deployment as this paper's Encode-stage contribution.
3. Prove a same-resource E/P/D layout within physical NPU4-7. No extra cards,
   CPU weight offload, quantization or hidden oversubscription.
4. If a distinct candidate remains, deliver orchestration/proxy behavior only
   through an explicit opt-in plugin; do not edit upstream runtimes.
5. Prove live E/P/D instance ownership and actual EC/KV transfer events.
6. Pass exact greedy replay before formal E2E performance.
7. Formal evidence remains 40 requests, concurrency 16, fixed 1024 output
   tokens and three comparable repetitions per arm, followed by paired
   LongBench-v2 and GSM8K.

## Final evidence

- The checkpoint is multimodal-capable, but capability alone is insufficient.
- The frozen performance protocol is raw text completion: input length 32768,
  shared prefix 16384, concurrency 16 and fixed 1024-token output.
- LongBench-v2 and GSM8K are text-only.
- Therefore no request activates visual/audio/video Encode work. Encoder
  isolation, E-to-P feature prefetch and modality-aware routing cannot affect
  the accepted workload.
- vLLM-Ascend v0.23 already contains ordinary P/D transfer, EC-transfer hooks,
  Mooncake layerwise transfer and EPD proxy examples. Re-running ordinary P/D
  would test an existing upstream feature, not this paper's distinct mechanism.
- No NPU service was launched and physical NPU4-7 were not consumed.

## Decision

Reject EPD-Serve for the current frozen Qwen3.6 performance and accuracy
protocol. This is a workload-scoped no-go, not a claim that EPD-Serve lacks
value for real high-concurrency multimodal traffic.

Queue position 9, DASC, already has a preserved deterministic cache-hit replay
failure and is not to be rerun unchanged. Advance to queue position 10, DUET.

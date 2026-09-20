# EPD-Serve — Qwen3.6/Ascend piercing

## Status

- Stage: planned / applicability gate in progress.
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

## Immediate next action

Locate the frozen performance request corpus/command and prove its modality.
In parallel, inspect the v0.23 EPD example's model support and instance memory
layout. Do not launch an NPU service until both gates pass.

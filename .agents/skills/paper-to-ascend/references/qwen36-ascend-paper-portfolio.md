# Qwen3.6-27B Ascend paper portfolio

## Scope and evidence status

This is the dated 2026-09-19 piercing prior for one objective:

- model: Qwen3.6-27B;
- target: Ascend through vLLM-Ascend;
- delivery: independent, opt-in plugin/monkeypatch with thin version adapters;
- performance acceptance: at least 10% end-to-end output-throughput improvement
  versus a matched dense control, with TTFT and TPOT reported separately;
- quality acceptance: no final quality regression under the frozen task
  protocol.

The scores allocate research time. They are not paper-quality rankings, NPU
measurements, or acceptance results. Re-verify each paper, official repository,
upstream support status, runtime seam, and claimed numbers at activation time.

## Weighted rubric

| Dimension | Weight |
| --- | ---: |
| Model/mechanism fit | 25% |
| Ascend-path fit | 20% |
| End-to-end benefit potential | 20% |
| Quality risk | 15% |
| Official implementation maturity | 10% |
| Plugin delivery and portability | 10% |

## Current queue

| Rank | Paper | Mechanism value | Piercing priority | Current decision basis |
| ---: | --- | ---: | ---: | --- |
| 1 | [Fast and Stable Triangular Inversion for Delta-Rule Linear Transformers](https://arxiv.org/abs/2605.21325) | 95 | **95** | Best immediate fit: Qwen3.5/3.6, Huawei NPU evidence, complete official sources, and reported inversion-kernel gain up to 4.3x. |
| 2 | [DeltaLog: Deferred Materialization of Recurrent States](https://arxiv.org/abs/2608.15533) | 91 | **87** | Strongest decode route; aims to preserve model semantics and reports 1.08-1.20x TPOT on Qwen/GDN, directly relevant to fixed 1024-token output. |
| 3 | [When Good Enough Is Optimal](https://arxiv.org/abs/2606.06034) | 84 | **79** | Candidate B for the same inversion campaign: truncated Neumann plus residual correction, reported up to 5x kernel gain and 20% lower decode-layer overhead; Snapdragon NPU evidence and approximation add transfer and quality risk. |
| 4 | [KVBuffer: IO-aware Serving for Linear Attention](https://arxiv.org/abs/2605.19049) | 89 | **76** | High decode potential and reported linear-attention latency reduction up to 45.17%, but requires state-lifecycle, scheduler, and graph-capture changes; reference stack is SGLang/Qwen3-Next. |
| 5 | [HYPIC: Accelerating Hybrid-Attention LLM Serving with Position-Independent Caching](https://arxiv.org/abs/2607.01299) | 92 | **72** | Mature mechanism and prior positive Ascend evidence, but benefit depends on segmented reuse/RAG workload and is limited as a generic dense/PDC increment. |
| 6 | [Sparse Prefix Caching for Hybrid and Recurrent LLM Serving](https://arxiv.org/abs/2605.05219) | 82 | **68** | Exact recovery and low quality risk without recurrent-kernel changes, but benefit depends on real shared-prefix distribution rather than generic decode. |
| 7 | [Scaling State-Space Models on Multiple GPUs with Tensor Parallelism](https://arxiv.org/abs/2602.21144) | 77 | **55** | Strong multi-GPU idea, but NVIDIA Mamba/Falcon-Mamba/Zamba evidence; Qwen3.6 TP4 already has related sharding, so incremental value must be re-proven. |
| 8 | [EPD-Serve: A Flexible Multimodal EPD Disaggregation Inference Serving System On Ascend](https://arxiv.org/abs/2601.11590) | 83 | **47** | Ascend-native and potentially large system gain, but multimodal encode/prefill/decode disaggregation needs multi-instance deployment outside the current single-model plugin boundary. |
| 9 | [DASC: Decay-Aware State Compression for Hybrid Linear-Attention Serving](https://arxiv.org/abs/2608.30386) | 85 | **40** | Mechanism remains interesting, but the current Ascend implementation failed deterministic cache-hit replay. It has no admissible performance or GSM8K result and stays paused. |
| 10 | [DUET: Disaggregated Hybrid Mamba-Transformer LLMs with Prefill and Decode-Specific Packages](https://arxiv.org/abs/2603.15530) | 79 | **28** | Requires custom prefill/decode packages; the available official repository is an architecture simulator rather than a vLLM-Ascend plugin implementation. |

## Sequential execution and turn rules

Only the frontier campaign may consume implementation/NPU budget.

1. **Fast and Stable Triangular Inversion (current frontier).**
   Use the official Ascend sources first. Candidate A is the stable MXR path.
   Treat 2606.06034 as candidate B inside the same bounded operator campaign,
   without inheriting candidate A's identity or evidence. Before substantial
   integration, prove the real Qwen3.6 vLLM-Ascend path and a measured
   triangular-inversion share of about 12% or more. If that bound fails, a
   reported 4.3x local speedup cannot plausibly deliver 10% end to end; stop
   polishing the isolated solve.
2. **DeltaLog (next independent frontier).**
   Activate when the inversion campaign reaches a no-go or terminal result.
   Gate batch/concurrency transfer explicitly because the paper's favorable
   region is reported mainly at batch 64-256.
3. **KVBuffer.**
   Enter only if the first two routes cannot reach the contract and a source
   map proves a plugin-safe state-lifecycle/scheduler/graph seam.
4. **Conditional cache/system routes.**
   HYPIC requires a segmented-reuse/RAG workload. Sparse Prefix Caching requires
   a measured shared-prefix distribution. They are not generic decode claims.
5. **Paused/deferred routes.**
   DASC must first pass deterministic replay. EPD-Serve and DUET require a
   separately authorized system/deployment scope. Scaling SSM TP requires a
   measured gap beyond the existing TP4 implementation.

Do not introduce MTP or speculative decoding as an escape route. A promising
combined path is exact/stable triangular inversion for prefill/chunkwise work
plus DeltaLog for long decode, but each component and the combination need
separate activation, attribution, matched controls, and quality evidence.

## Common admission and acceptance ladder

For every paper:

1. freeze paper/source identities and method-parity ledger;
2. prove Qwen3.6 architecture fit and the real vLLM-Ascend execution seam;
3. measure the affected bottleneck and compute an end-to-end upper bound;
4. implement only in the plugin, disabled by default and fail-closed;
5. pass real Ascend multi-step numerical/state/determinism checks;
6. run target-shape timing only after correctness;
7. run one-switch matched dense service A/B with fixed 1024-token output;
8. expand to three-run performance only when the screen is promising;
9. run final quality with thinking disabled, max_tokens=2048, and normal EOS;
10. accept only at least 10% end-to-end throughput gain with no final quality
    regression; otherwise record a scoped no-go and advance the queue.

General optimizations must be applied equally to the dense control. Kernel
timing, FLOP savings, CPU simulation, energy proxies, or theoretical bounds are
diagnostic evidence only.

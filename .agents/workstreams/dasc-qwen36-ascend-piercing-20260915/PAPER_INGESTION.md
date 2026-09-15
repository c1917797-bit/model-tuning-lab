# DASC Paper Ingestion

## Identity

- Paper: DASC: Decay-Aware State Compression for Hybrid Linear-Attention Serving
- Version: arXiv:2608.30386v1, submitted 2026-08-31
- Source: https://arxiv.org/abs/2608.30386 and https://arxiv.org/html/2608.30386
- Claimed implementation framework: SGLang, not vLLM-Ascend.
- Claimed model families: Kimi-KDA and Qwen-GDN.

## Mechanism

DASC compresses persistent recurrent-state checkpoints for hybrid linear-attention serving. It does not change full-attention KV. It builds a static weight-derived retention-horizon mask, stores only long-horizon state units in a ragged checkpoint layout, and restores a full compute-layout state on cache reuse by loading retained units and zero-filling or suffix-refreshing omitted units.

For Qwen-GDN, the unit is a full GDN head state. For Kimi-KDA, the unit is a key channel within a head. The current Ascend target is Qwen-GDN, so the first local hypothesis is head-wise GDN state checkpoint compression.

## Paper Method Chain

1. Compute static horizon from decay weights using representative input `a=-0.3` and epsilon `1e-3`.
2. Select global units whose horizon is larger than `W_max`; omitted units are local.
3. Store persistent recurrent state checkpoints in ragged layout; convolution state remains part of complete checkpoint accounting.
4. On prefix-cache hit, reconstruct compute-layout state by loading global units and either zero-filling local units (`dasc-nr`) or replaying a bounded suffix and copying refreshed local units (`dasc-wr`).
5. Balance compressed state checkpoint payload across TP ranks; full-attention KV remains unchanged.
6. Evaluate under fixed state-checkpoint HBM budgets where increased checkpoint residency reduces repeated prefill and improves cache-hit TTFT/input throughput.

## First Ascend Hypothesis

The first one-switch hypothesis is: for Qwen3.6 GDN on vLLM-Ascend, a DASC-style head mask can reduce recurrent-state checkpoint bytes while preserving enough cache-hit quality to improve TTFT in a controlled prefix-cache fill/replay workload.

This is not a normal decode-throughput hypothesis. It is a cache-capacity and cache-load hypothesis. A run without prefix reuse cannot validate or reject DASC.

## Required Local Evidence Before NPU Benchmark

- Installed checkpoint has GDN layers and exposes the decay parameters used by DASC.
- GDN state layout and TP sharding are known for conv state and recurrent temporal state.
- vLLM-Ascend cache path can persist and reload recurrent state checkpoints, or the missing path is explicitly implemented in the plugin.
- Dense and DASC arms differ by exactly one compressed-checkpoint switch.
- The workload includes cache fill, cache reuse, cache-hit telemetry, TTFT, and E2E quality.

## Early Risk Assessment

DASC has higher local relevance than Tail-Replay as a cache-system paper because it directly targets recurrent state checkpoint storage. The main risk is that current vLLM-Ascend may not expose the same state-checkpoint store/load abstraction as SGLang; if absent, the first work becomes runtime integration rather than a simple selector port.


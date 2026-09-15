# DASC Qwen3.6 Ascend Piercing Handoff

## Current Status

Workstream opened on 2026-09-15 for arXiv:2608.30386 DASC. No NPU experiment has been launched for this paper yet. Current state is paper ingestion and applicability gating.

## Mainline Goal

Pierce whether DASC can produce a real cache-hit TTFT or throughput gain on Qwen3.6-27B in the chicaihong01 Ascend environment, while keeping E2E quality within the user's gate. Do not judge it with no-cache decode throughput.

## Delivery Constraint

The final runnable implementation must be a plugin-owned monkeypatch that runs on Ascend. Do not modify upstream vLLM, vLLM-Ascend, CANN, model weights, or original images. CPU/offline probes and source inspection are allowed only as gates; they are not a valid final delivery.

## Short-Term Plan

1. Inspect Qwen3.6 GDN weights and vLLM-Ascend state layout.
2. Generate a DASC-GDN head-retention plan for `W_max` values such as 16, 64, 128, and 512.
3. Compute dense vs compressed checkpoint bytes including recurrent temporal state and convolution state.
4. Source-map vLLM-Ascend prefix-cache/state-checkpoint store/load behavior.
5. If the cache path exists, implement DASC-NR canary first; if it does not, implement the smallest plugin-owned state checkpoint path or stop with an integration-gap decision.

## HYPIC Lessons Applied

- Use one denominator and one treatment switch.
- Prove mechanism activation before timing.
- Separate source compatibility, canary correctness, service integration, performance, and quality.
- Keep per-run artifacts resumable and auditable.
- Do not claim the paper result from a partial primitive.

## Current Decision

Open. The paper has credible relevance to Qwen-GDN, but local feasibility depends on state checkpoint store/load support in vLLM-Ascend.

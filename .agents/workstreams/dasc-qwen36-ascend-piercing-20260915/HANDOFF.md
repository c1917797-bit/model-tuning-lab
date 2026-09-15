# DASC Qwen3.6 Ascend Piercing Handoff

## Current Status

Workstream opened on 2026-09-15 for arXiv:2608.30386 DASC. No NPU experiment
has been launched for this paper yet. Paper ingestion, architecture fit, the
state-lifecycle source map, and a first plugin-owned DASC-NR numerical canary
implementation are complete.

The canary lives under `projects/dasc_vllm_ascend`. It is disabled by default,
version/source guarded, and only changes temporal-state copying on a genuine
new/resumed prefix restore. It keeps dense allocation and therefore is not yet
a cache-capacity or performance implementation.

## Mainline Goal

Pierce whether DASC can produce a real cache-hit TTFT or throughput gain on Qwen3.6-27B in the chicaihong01 Ascend environment, while keeping E2E quality within the user's gate. Do not judge it with no-cache decode throughput.

## Delivery Constraint

The final runnable implementation must be a plugin-owned monkeypatch that runs on Ascend. Do not modify upstream vLLM, vLLM-Ascend, CANN, model weights, or original images. CPU/offline probes and source inspection are allowed only as gates; they are not a valid final delivery.

## Short-Term Plan

1. Inspect Qwen3.6 GDN weights and vLLM-Ascend state layout.
2. Generate a DASC-GDN head-retention plan for `W_max` values such as 16, 64, 128, and 512.
3. Compute dense vs compressed checkpoint bytes including recurrent temporal state and convolution state.
4. Source-map vLLM-Ascend prefix-cache/state-checkpoint store/load behavior.
   This is complete: `MambaManager` and `preprocess_mamba` preserve and copy
   aligned convolution and temporal checkpoints by block ID.
5. Review, package, and run the implemented DASC-NR numerical canary with a
   disabled control on physical NPU4-7.
6. After all-rank activation and correctness pass, implement compact temporal
   pages plus dense active-state workspace. Do not mistake the current
   zero-filled dense storage for a capacity optimization.
7. Prove real cache-block admission growth before any service performance claim.

## HYPIC Lessons Applied

- Use one denominator and one treatment switch.
- Prove mechanism activation before timing.
- Separate source compatibility, canary correctness, service integration, performance, and quality.
- Keep per-run artifacts resumable and auditable.
- Do not claim the paper result from a partial primitive.

## Current Decision

Open, with a narrower integration risk. The paper has credible relevance to
Qwen-GDN and the current stack already supports aligned recurrent-state prefix
checkpoints. Local feasibility now depends on whether a plugin monkeypatch can
replace dense block storage with compact retained-head storage plus a dense
active-request workspace while keeping native Ascend GDN kernels unchanged.

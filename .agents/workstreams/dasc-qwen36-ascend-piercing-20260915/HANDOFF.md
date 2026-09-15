# DASC Qwen3.6 Ascend Piercing Handoff

## Current Status

Workstream opened on 2026-09-15 for arXiv:2608.30386 DASC. Paper ingestion,
architecture fit, the state-lifecycle source map, and the first plugin-owned
DASC-NR numerical canary are complete and verified on physical NPU4-7.

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

## Verified NPU canary and decision

The W64 dense-storage canary ran on Qwen3.6-27B with TP4, vLLM/vLLM-Ascend
v0.23.0, eager mode, Mamba align cache, and physical NPU4-7. Two 2,350-token
prompts shared one 1,536-token cache page. All 48 GDN layers fired on all four
TP workers, yielding exactly 192 temporal-restore events. Candidate and
plugin-disabled control returned identical 16-token continuations.

The steady cache-reuse request was 4.213 s for the canary and 4.008 s for the
control, so the dense-storage canary regressed by 5.095%. It is rejected as a
performance candidate but accepted as runtime-path and semantic evidence.
First-request latency is excluded because both runs included cold operator
initialization.

Runtime artifacts:
`/cache/cch/dasc-qwen36-ascend-20260915/`

The next admissible successor must change the physical representation:
compact retained-head checkpoint storage, dense workspace expansion on restore,
and measured post-alignment cache capacity. Repeating or tuning the existing
dense masking route is closed.

# DASC vLLM-Ascend Plugin

This project is the plugin-owned implementation area for the DASC
Qwen-GDN/Ascend piercing workstream.

The first implementation is deliberately a **numerical canary**. On a genuine
Mamba/GDN prefix-cache restore, it keeps the convolution state dense and copies
only weight-selected long-horizon temporal heads into the new running-state
block. Omitted temporal heads are zero-filled (DASC-NR semantics).

It does not yet reduce the physical cache page size. Therefore this version
must not be used to claim cache-capacity, TTFT, throughput, or paper-level
performance gains.

## Opt-in contract

The plugin is disabled by default. The initial canary requires these environment
values: MST_DASC_ENABLE=1, MST_DASC_MODE=nr-numerical,
MST_DASC_W_MAX=64, an absolute MST_DASC_EVIDENCE_PATH, and
VLLM_PLUGINS=dasc_vllm_ascend.

The implementation fails closed on unsupported versions, source identity,
cache mode, state shape, or worker dispatch. Evidence is written outside Git.

## Ascend mechanism canary result (2026-09-15)

On Qwen3.6-27B, TP4, vLLM/vLLM-Ascend v0.23.0, and physical Ascend
NPU4-7, a 2,350-token shared-prefix pair produced one 1,536-token local cache
hit. All four TP workers executed the patched restore path for all 48 GDN
layers (192 `prefix_temporal_restore` events). The candidate and disabled
control produced identical sampled 16-token continuations.

The paired reuse request took 4.213 s with the numerical canary and 4.008 s
with the plugin disabled: the canary was 5.095% slower. This is an expected
negative result for a dense-storage implementation that adds restore masking.
It proves reachability, not performance. The next performance-bearing
milestone is compact retained-head checkpoint storage with dense active
workspace expansion at restore time, followed by capacity and steady-state
A/B measurements.

Raw runtime evidence remains outside Git under
`/cache/cch/dasc-qwen36-ascend-20260915/`.

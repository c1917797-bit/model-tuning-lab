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

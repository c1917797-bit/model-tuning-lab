# Ada-KV to Ascend: cross-rank and storage gate

First-loop start: 2026-09-25 07:05 UTC. Stop or decide this paper's first
formal loop by 2026-09-26 07:05 UTC. This document is a source/ABI gate, **not**
an implemented candidate, NPU result, or performance claim.

## Pinned mechanism and target

The [paper](https://arxiv.org/html/2407.11550) allocates one layer's total
Top-K eviction budget across KV heads by global selection of attention
weights. Its official code is
[`FFY0/AdaKV`](https://github.com/FFY0/AdaKV), observed HEAD
`04497abac4c1a58426f3daf1014578990e225cc5`; pin a local read-only
checkout before any parity result. The author implementation computes
observation-window scores, pools them, means the six query-head scores inside
each GQA group, applies a safeguard allocation, retains selected old tokens
plus the recent window, and uses variable-length flattened storage. The
inspected `AdaptiveSnapKVCluster.update_kv_gqa` asserts batch size one; the
repository README targets Llama/Mistral with FlashAttention/CUDA, not Qwen3.6
continuous batching on Ascend. These are adaptation requirements, not a
paper-wide negative conclusion.

The installed Qwen3.6-27B config has 24 query heads, four KV heads and a
full-attention interval of four. TP4 places one KV head and six query heads
per rank. Therefore rank-local Ada-KV **cannot** adapt among heads: a global
four-head allocation must exchange scores or equivalent budget statistics
across ranks. A per-rank Top-K that always gives each single local KV head its
fixed budget is uniform eviction, not the paper mechanism.

The measured dense decode profile attributes 27.40025% of summed operator
time to attention; this is an investment signal, not a critical-path share or
a 10% E2E proof. The deployed v0.23 cache shape is
`[2, num_blocks, block_size, num_kv_heads, head_size]`, and the native FIA
decode call accepts a block table and effective sequence length. Its existing
`kvcomp_attn` route selects pages using Hamming hashes; that demonstrates a
native selected-table seam, but **does not** implement Ada-KV's score,
cross-rank allocation or physical eviction. A sidecar retaining full BF16 KV
cannot claim cache-memory reduction or a faithful Ada-KV port.

The author's separate [vLLM compression fork](https://github.com/FFY0/adakvcompress)
is useful for studying physical eviction and scheduler ownership, but its
README explicitly lists tensor parallelism, prefix caching, CUDA graphs and
non-FlashAttention backends as unsupported. It is not a drop-in Ascend
implementation. Reuse its lifecycle ideas only where the v0.23 Ascend
worker/cache-manager contracts can be proved compatible.

The official score path uses an observation-window softmax, GQA reduction,
and max pooling; max pooling often creates exact score ties. Its per-head
`sort` followed by global `topk` leaves tie order unspecified. The plugin's
budget probe now applies a stable global ordering (rank/head then token
index) so repeated TP4 allocations have a defined tie policy. This is a
documented determinism adaptation; a tie-free score case should match the
author's allocation exactly, while tied-boundary cases require separate
numerical and task-quality checks. Verify that Ascend supports stable sort
before interpreting the NPU probe.

## Environment evidence, 2026-09-25

The one-shot non-privileged NPU4 canary
`qwen36_adakv_npu4_canary_20260925` exited 1: `torch_npu` reported
`Can't get ascend_hal device count`, then `Invalid device id`. Its Docker
device mapping and read-only driver bind match a previous successful NPU4
container. This reproduces the older pre-release canary symptom but does
**not** by itself identify the cause. Host `npu-smi info` shows no compute
process on physical 4-7 and idle-baseline HBM. The live
`agentgpu-910b4-qwen35-4b-aiv-v1` container has only a `sleep infinity`
process, yet its UDA namespace owns physical 0-7. Because it also maps
protected 0-3, do not stop it without explicit authorization for that exact
container and a fresh owner/process check. Preserve the exited canary logs;
do not rerun an identical failing launch or count this as an Ada-KV NPU
algorithm result.

## First bounded decisions

1. Audit the official score/Top-K/safeguard code at the pinned commit and
   the actual v0.23 worker/cache-manager allocation, graph key, prefix-cache
   identity and FIA update path. Reuse native CANN/FIA and existing source
   where semantics match; generate no new operator without a measured gap.
2. On physical NPU4–7, compare a four-rank global budget calculation against
   the author's single-process four-head reference with GQA mean. Require
   non-uniform head allocations on representative live Q/K, correct global
   budget accounting, finite scores, and stable repeated output. Synthetic
   scores alone are an ABI smoke, not the investment gate.
3. Prove an opt-in compressed-cache lifecycle replacing dense attention KV,
   including mixed batch, prefill/decode, slot recycling, prefix identity and
   NPUGraph replay. A page-aligned approximation must be labeled
   Ada-KV-derived, not the author's token-exact implementation, and validated
   separately.
4. After NPU correctness, run one profiler-off matched service screen against
   the same-stack dense path with 1024 output tokens, 40 requests and
   concurrency 16. Only a promising result advances to three rounds and
   matched LongBench-v2/GSM8K max_tokens=2048 final quality.
5. At the 24-hour gate, preserve precise accepted/rejected/inconclusive/failed
   scope. If the one-day path lacks a real allocator and plausible E2E
   candidate, stop this implementation and select a different measured
   mechanism. Do not call the paper impossible because the author CUDA code
   or current native cache ABI differs.

## NPU resource and synthetic TP4 ABI result, 2026-09-25

Kernel `uda_occupy_dev_by_ns` identified physical NPU4 conflict with
`agentgpu-910b4-qwen35-4b-aiv-v1`, which mapped 0–7 despite running only
`sleep`. After the user authorized stopping that exact container, it was
stopped but **not deleted**; inspect showed `exited`, PID 0. A newly named,
non-privileged single-device NPU4 canary then returned device count 1 and
`Ascend910B4`. This resolves the earlier environment failure, not the
algorithm gate. A separate CANNBench child was terminated only while it
actually occupied NPU5; its broader parent/container and NPU0–3 work were
preserved. A later attempt to stop the parent after NPU5 had cleared was
rejected by safety review and was not retried.

The first TP4 container, `qwen36_adakv_tp_budget_abi_v1_20260925`, did not
enter the probe because `torchrun --standalone` could not resolve its
hostname under `--network none`. It was stopped without deletion; this is a
launcher failure, not an Ada-KV numerical failure. The corrected, uniquely
named `qwen36_adakv_tp_budget_abi_v2_20260925` used an explicit loopback
rendezvous and completed with exit 0. Its device map is host 4–7 to container
0–3; no device 0–3 was mapped. The rank-zero report is
`/cache/cch/qwen36-adakv-ascend-20260925/tp-budget-abi-v2/report.json`
(SHA256 `fb8494f3fa916308c1acc6f1c3b18ab5a821ac54efed13a1ab0bddfe423bc595`).
Synthetic author-style observation scores, TP4 all-gather, stable global
selection and safeguarded per-head budgets matched an independent CPU
reference for batch 1 and 16. All 17 requests had non-uniform raw and
safeguarded head allocations. The unsafeguarded selected count is exactly
1024 per request; safeguarded budgets sometimes total 1023 or 1025 due to
the author's per-head rounding rule. Thus stable sort is supported on this
NPU software stack, but exact physical storage accounting still needs a
documented policy. This **only passes the synthetic distributed ABI gate**:
it does not demonstrate real-model Q/K parity, KV eviction, graph safety,
service throughput, or task quality.

Historical HYPIC remains only the prior segmented-prefix exemplar; it does
not count as this loop's new qualifying technique.

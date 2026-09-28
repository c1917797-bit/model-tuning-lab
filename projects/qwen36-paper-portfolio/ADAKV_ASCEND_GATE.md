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

## Live Q/K/V diagnostic: v1/v2 and source-fidelity correction

The opt-in read-only plugin captured one real 4096-token prefill at Qwen3.6
full-attention layer 3. Four TP workers each saw Q `[4096,6,256]` and K/V
`[4096,1,256]` in BF16, and agreed on a non-uniform global allocation.
The v1 request returned HTTP 200 with four completion tokens. No model
output or serving cache was mutated. Artifacts are under
`/cache/cch/qwen36-adakv-ascend-20260925/live-prefill-v1/`.

The v2 diagnostic retained selected historical K/V plus the last 32 prompt
tokens, appended each decode token, and compared native contiguous FIA with
the unchanged dense output over three decode calls. A full-support math
oracle agreed with dense (worst max abs 0.006873), and selected-support math
agreed with native FIA (worst RMS below 0.001). Across all four ranks and
three steps, worst selected-vs-dense RMS was 0.1333/0.1073/0.07125/0.03741
at old-token base capacities 256/512/1024/2048 respectively. This is one
repetitive prompt and one layer; it is *not* a task-accuracy loss or
performance result. Artifacts are under
`/cache/cch/qwen36-adakv-ascend-20260925/live-prefill-v2/`.

Source re-audit at official commit `04497ab` found a fidelity difference:
`calcul_attn_sore` computes BF16 QK logits, FP32 softmax, casts probabilities
back to BF16, **then** averages over the observation window and GQA group
before max pooling. v2 kept those probabilities in FP32. Its large errors
therefore characterize a FP32-score derivative, not the exact author score.
The plugin was corrected and v3 run in a new output directory before any
algorithm-level conclusion. The v2 container and logs were preserved stopped.

The source-corrected v3 completed the same 4096-token request (HTTP 200,
four generated tokens) with four TP workers and three observed decode steps
per worker. The BF16 score path also passed a separate NPU4 operator canary.
Across all twelve rank/step comparisons, worst selected-vs-dense RMS at
old-token base capacities 256/512/1024/2048 was respectively
0.13277/0.10691/0.07158/0.03728; worst selected-support math-vs-native FIA
RMS remained below 0.001. The full-support math-vs-dense maximum absolute
difference was 0.00743. The corrected allocation changed some head budgets
but did not materially remove the selected-support error on this one prompt.
The service was stopped without deletion after the request. Immutable v3
artifacts are in
`/cache/cch/qwen36-adakv-ascend-20260925/live-prefill-v3/`;
rank-zero audit SHA256 is
`d0ae5f5f6f572de5738945683f15833e3e783cae44916f714ef376f74a6d88c7`.

This is a **single-layer, single-prompt investment diagnostic**. It does not
show final LongBench-v2/GSM8K loss, any actual cache release, mixed-batch
lifecycle, graph compatibility, or matched service performance. Before
building a new kernel, audit whether native v0.23 cache allocation and FIA
can express per-KV-head variable token lengths at the live hybrid page size
(1536), or whether an opt-in attention-owned compact cache is required.
Do not report the diagnostic's full dense sidecar as memory reduction.

Source-level cache audit: vLLM v0.23's ordinary decoder path requests a
`FullAttentionSpec`, whose capacity is derived from `max_model_len`; the
existing `SlidingWindowSpec` admission calculation uses the configured
sliding window **plus** `max_num_batched_tokens`. At a large prefill limit,
substituting a sliding-window spec alone does not establish lower startup
allocation, and it cannot express Ada-KV's unequal per-KV-head token counts.
Native FIA accepts a block table and effective sequence lengths, so the
next prototype must prove attention-owned compact storage or an explicit
cache-manager/scheduler seam with physical allocation accounting. A selected
block table over an otherwise dense cache is only a functional diagnostic.

The deployed Ascend attention `forward` calls `reshape_and_cache` **before**
`forward_impl`. `reshape_and_cache` writes the incoming K/V through the
native cache operator and marks the write complete; the normal decode FIA
then reads `self.key_cache`/`self.value_cache` with scheduler-provided block
tables and sequence lengths. A replacement only inside
`forward_fused_infer_attention` therefore cannot avoid dense writes. A real
candidate must intercept at or above `forward`, own selected-token update
and read consistently, and establish request/slot recycling before mixed
batch. Do not time the existing read-only hook as an Ada-KV service candidate.

Historical HYPIC remains only the prior segmented-prefix exemplar; it does
not count as this loop's new qualifying technique.

## Single-request compact read/write seam, 2026-09-25

An independent, explicitly opt-in candidate hook now intercepts the target
layer's `reshape_and_cache` **before** the ordinary dense write, constructs a
fixed-capacity compact K/V arena from the author-order cross-rank budget at
prefill, and runs native FIA over that arena for subsequent decode tokens.
The hook is fail-closed outside one request, eager mode, `PrefillNoCache` and
`DecodeOnly`; it is not enabled by merely importing the package. It changes
the model output on this single layer, unlike the read-only v1-v3 probe.

The first same-image import attempt lacked the read-only host driver bind and
failed before registration with `libascend_hal.so` unavailable. Repeating
with the driver bind passed registration without NPU devices. The first HTTP
client attempt had the same missing-bind import error and sent no request;
the corrected client was run once. These are launcher/environment failures,
not numerical results.

The service ran only on physical NPU4-7 and returned HTTP 200 for one
4096-token prefill plus four generated tokens. On **each of four TP ranks**,
the target full-attention layer recorded one skipped dense cache write at
prefill, three skipped decode writes, one compact prefill arena and three
native FIA compact decode outputs. Global safeguarded old-token budgets were
[2182, 2068, 2428, 1514], with the recent 32 tokens retained on every rank.
Across 12 rank/step comparisons, selected-support native FIA versus the
independent math oracle had worst RMS `0.000950319`, under the predeclared
`0.001` local gate. The request summary is
`/cache/cch/qwen36-adakv-ascend-20260925/candidate-single-v1/request-summary.json`
(SHA256 `dad2329ddc71e94c016af08713f27bfdde18b8e63a0ece74069c2fbd69db99b4`);
rank-zero audit SHA256 is
`c626b29651b1b57e49637f16619b7887ce08743e12fe65b9ed637c798dae772e`.
The owned service was stopped without deletion; post-stop NPU4-7 had no
compute processes.

**Scope:** this passes only a real-model, one-layer, one-request eager
read/write and selected-support numerical seam. The vLLM scheduler still
allocates its normal dense cache buffer; only this layer's writes are skipped.
No physical pool reduction, mixed-batch request isolation, prefix-cache
identity, NPUGraph replay, matched dense E2E speed, or task accuracy has been
shown. The next implementation gate is request-indexed compact arenas with
slot reuse and an allocator/spec change that actually removes unused dense
storage; do not benchmark the current single-request hook as a finished
Ada-KV candidate.

## All-full-layer numerical gate and oracle correction, 2026-09-25

An explicit `QWEN36_ADAKV_ALL_FULL_LAYERS=1` variant targets the 16 Qwen3.6
full-attention layers (3, 7, ..., 63); the default remains the single-layer
diagnostic. In `candidate-all-v1`, all 16 layers completed a compact prefill
on all four TP ranks for the same 4096-token prompt. The first decode failed
the predeclared native-vs-FP32-math RMS gate of `0.001` at TP rank 3, layer
19 (`0.0010745003`). No HTTP response or model-level pass exists. Rank-3
audit SHA256: `65d2e04a527be3f2a4930c5d66ff5fbf4b4175665a9099e294514a410543c0b1`.

The new failure-only diagnostic, in a separate immutable directory
`/cache/cch/qwen36-adakv-ascend-20260925/candidate-all-numeric-diagnostic-v1/`,
kept that gate unchanged and recorded output scale and BF16 quantization.
It failed on rank 1/layer 7 (raw RMS `0.00104436`) and rank 3/layer 19
(`0.00122594`). The FP32 oracle's *own* BF16 rounding RMS was `0.00103023`
and `0.00121511`, respectively, while native FIA versus the independently
computed **BF16-rounded** oracle was `0.00069298` and `0.00067082`.
Rank-1/3 audit SHA256: `1b7a6e9d172047d5540aef27e8ea0368fba76a961513c107c01a8e068de17d85`,
`d47d0789bb1846a0f240768728e882a23ad3b6d734b2dd763e84797fa80806fd`.
The first failed run remains preserved; these figures explain a mixed-dtype
oracle gate, **not** final model correctness or task quality.

Before another full-layer run, the independent math oracle is now rounded to
the native FIA output dtype **for the local native-on-selected-support gate**.
The absolute RMS threshold remains `0.001`, with the original FP32 error and
rounding floor logged separately. This is a reference-dtype correction, not a
relaxation of the numeric threshold or a claim that selected KV matches dense.
At that checkpoint the corrected gate had not yet run. A pass would still
require whole-model task-quality screening and a real request-indexed compact
cache allocator; vLLM still preallocates its ordinary dense KV pool today.

The `candidate-all-rounded-v1` run then showed that BF16 rounding alone is
not the whole issue with a fixed absolute tolerance: all 16 layers again
completed compact prefill on all four ranks, but later full-attention layers
with larger outputs exceeded RMS `0.001` against the BF16-rounded oracle.
For example, rank 1/layer 63 had output RMS `6.1634`, native-vs-rounded
RMS `0.004308`, and independent oracle-rounding RMS `0.010092`; the
native-vs-rounded **relative** RMS was `0.000699`. Rank 0/layer 59 was
`0.001478/1.5826 = 0.000934`. This run also has no HTTP response or
model-level pass. Rank-0/1/2/3 audit SHA256 respectively:
`7ee0b491c1a5912a2fb63a00533a34efd7f7419ff3b30d6f6a5520bcff067f15`,
`e01df0143d774e20347d68eae963105d9aa3be8eddaab811a17a7c9463529824`,
`2d01f29eff3a86e686c29db342e54ac17568807078d67922322c49f388d2406e`,
`b8cc9aa4a72e9f3241ae83df82d080cbc3f1958133abb6d57e27e2ff90b2b35e`.

The next one-shot gate is therefore predeclared as independent BF16-rounded
oracle RMS `<= 0.001 * max(1, oracle_RMS)`, requiring finite native output.
This **changes** the tolerance from an absolute to an absolute/relative one;
it does not retroactively pass either failed run. It tests local native FIA
on the selected support, not selected-versus-dense equivalence, whole-model
accuracy, or serving performance. The scale-aware gate had not yet run at
that checkpoint.

The `candidate-all-scaled-v1` run then failed this frozen envelope at several
late layers, including rank 2/layer 47: native-vs-rounded RMS `0.0018845`
against allowance `0.001`, with oracle output RMS `0.8733`. Rank 0/layer 59
was `0.0024392` versus allowance `0.0016704`. All 16 layers completed compact
prefill, but no complete decode or HTTP response was obtained. This run is
preserved separately, not relabeled as passed.

**Stop criterion:** do not keep tuning tolerance to the candidate. The next
NPU experiment is a read-only, all-full-layer *uncompressed dense* numerical
baseline: compare deployed paged FIA, native contiguous full-support FIA, and
independent FP32/BF16-rounded math on the same real Q/K/V over three decode
steps. Its purpose is to establish the native backend's own error envelope
before attributing any extra discrepancy to Ada-KV. This baseline changes
neither model output nor serving cache, and is not performance evidence.

The read-only dense baseline `dense-native-oracle-v1` returned HTTP 200 for
4096 input and four output tokens. All four TP ranks recorded 16 full layers
times three decode calls, 192 complete comparisons. Relative RMS (divided
by the independent math output RMS) for native paged versus native contiguous
full-support FIA was median `0.000587`, P95 `0.001011`, max `0.001536`.
Native contiguous FIA versus **BF16-rounded** independent math was median
`0.000911`, P95 `0.001521`, max `0.002819`; versus FP32 math it was median
`0.001678`, P95 `0.001848`, max `0.002141`. The candidate's available
`candidate-all-scaled-v1` selected-support comparisons (84 points before
fail-closed abort) had BF16-rounded-math relative RMS median `0.000904`,
P95 `0.001525`, max `0.002359`. Their distributions are comparable on this
one prompt, but this does not prove unobserved candidate layers or task
accuracy. Request summary SHA256:
`aabbd92e77d793f205c5122171a36778f0130140f23594d0c9d476b1f74aae22`.
Rank-0/1/2/3 audit SHA256:
`0dba876b80336c63f954944c32e7c091b7390953622e6a82fdd675ec070c870b`,
`64aff5417471131ff20e8ec1a6a6b670b0014ebc729c457ddfec99391193718e`,
`552d1032439ec57eade559e811160b348929d080755b9934f4221a0edc491e88`,
`94dcdeb4500bbe4a4ef0e869f347060b550630e9159d1bd1d284f43847ca5fa8`.
The service was stopped without deletion after this request.

**Predeclared next gate:** one new full-layer candidate run will require finite
native and math outputs and relative RMS `<= 0.003` versus the independent
BF16-rounded math reference on **every** selected-support decode event. The
`0.003` ceiling is rounded upward from the observed uncompressed-native max
`0.002819`, not from a candidate pass. The earlier failed criteria and outputs
remain failed. If this new gate fails, stop threshold tuning; investigate the
specific operator/input discrepancy or close this implementation scope.
Even a pass only validates the native computation on the selected KV; it
cannot replace full-model output/task quality or E2E evidence.

The single-run `candidate-all-native-envelope-v1` passed this scoped gate.
The fixed request returned HTTP 200 with 4096 prompt and four completion
tokens. All four TP ranks recorded 16 compact prefill layers, then three
compact decode calls on each layer (48 per rank), with **zero** numerical
failure events. Worst selected-support native-versus-rounded-math relative
RMS was `0.0025721` at rank 3/layer 55/decode step 2, below the frozen
`0.003` ceiling. Its absolute RMS was `0.0035346` on output RMS `1.37423`.
Request summary SHA256:
`40cdf30282a4580e59ed2ab34648bdc52427b3e386a8cec6b5627d908666323a`.
Rank-0/1/2/3 audit SHA256:
`cc6b14138e1d35f0a692b2452f685c9fce99dac8bd2274cca01a3c0c291ef776`,
`57b6b302dc552812d3ab9ec93dd004ab3a09881a4f60bb1e89e41b6056e9`,
`01f836b167a90932a28307275ccad5df68c7c739f3c46cdbde5bd6c1a07571fc`,
`143f1f6750983c51d2ef656d7e92ae2426f00498101007ee0e0d26a9e23bb4d0`.
The service was stopped but retained; physical NPU4-7 returned to their idle
HBM baseline with no running compute process.

**Decision scope:** real-model, all-full-layer, one-request eager selected KV
read/write through native Ascend FIA passed a baseline-calibrated local
numerical gate. This is stronger than the prior one-layer seam but still
excludes multi-request identity, request/slot recycling, prefix cache,
chunked prefill, NPUGraph, true dense-pool allocation reduction, 1024-output
paired throughput, and LongBench-v2/GSM8K task quality. The selected output
is intentionally different from dense, so this local operator gate cannot
stand in for task accuracy. The next implementation step is a request-indexed
compact-cache lifecycle, not a claim of final Ada-KV deployment.

### Request-indexed mixed-batch seam, 2026-09-25

The next opt-in plugin mode wraps the deployed v0.23 `NPUModelRunner._model_forward`
and carries `input_batch.req_ids` into full-attention execution. Each request
owns a separate compact arena keyed by that identity; completed identities
are dropped. The runner source SHA256 is
`94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968`.
This is still an eager prototype; vLLM retains its ordinary dense KV
allocation, and chunked *continuation* prefill, graph replay and prefix
cache are unsupported.

The first two-request launch (`candidate-two-requests-v1`) failed before
model initialization because the image's default shell entrypoint was not
overridden by the explicit Python interpreter. The exited container was
retained. It is a launch error, not NPU algorithm evidence.

The next run (`candidate-two-requests-v2`) reached real NPU execution and
failed closed before a targeted dense cache write at
`AscendAttentionState.ChunkedPrefill`. The scheduler had one previously
prefilled request decoding while a new 4096-token request entered prefill;
homogeneous-only support was therefore insufficient. The HTTP requests
returned 500; these are **not** numerical or performance results.

After implementing mixed *new-request full prefill + existing-request
one-token decode* with the native Ascend FIA and request-keyed arenas,
`candidate-two-requests-v3` returned HTTP 200 for two concurrent asymmetric
requests: 4096 and 3584 prompt tokens, each with four output tokens. Each
of four TP ranks recorded 32 compact prefill events (16 layers per request),
96 compact decode events (two requests × 16 layers × three steps),
80 skipped dense-write events, and zero numeric failures. The 3584-token
prefill occurred in `ChunkedPrefill` state and the 4096-token prefill in
`PrefillNoCache`; this verifies actual mixed-state dispatch, not just a
synthetic batch. Across all selected-support native-versus-BF16-rounded
math comparisons, the worst relative RMS was `0.002815`, below the frozen
`0.003` ceiling. The candidate still lacks task-quality and matched dense
E2E evidence. The service was stopped, not deleted, after the canary.

Immutable request summary SHA256:
`9d92ebd139a0e42ebacbef10c9fae52e0c839f682cde070009974e5d4d07cf94`.
Rank-0/1/2/3 audit SHA256:
`d2b3cb5b64b5b25eea104ce5f21fea2f5d5b2c26fa75f17fa65b79b1d046ba48`,
`24df72687a157b54d1ef28658780075f8310949e8c0577b64db3b8fe229b0cf1`,
`6ed094d05a3d3bfa35d7291e7129e899a72f9a9e1fc343d60d5832555e128e94`,
`f28791f631f684a69d089aa791a211ec3f02030e35130193256c1bd9b571ba42`.
The prefill output itself was produced by an uncompressed native FIA on
the corresponding per-request Q/K/V. The next gate explicitly crosschecks
this split prefill call against the deployed full-batch native prefill on
the same Q/K/V; do not conflate selected-support decode checks with
prefill or task accuracy.

The opt-in `candidate-two-requests-v4-crosscheck` then performed that
native prefill crosscheck. Both asymmetric requests again returned HTTP 200
and four output tokens each. On every TP rank, all 16 full-attention layers
recorded one whole-output split-versus-original native prefill comparison,
with **zero** relative RMS in all 64 checks. The other request entered
as a new full prefill within a mixed `ChunkedPrefill` turn and used the
same split native call. Each rank again recorded 32 compact prefill and
96 compact decode events; no numeric failure event occurred. Worst
selected-support native-versus-BF16-rounded-math relative RMS was
`0.002448`, below the already frozen `0.003` gate. This establishes
the split native operator path only for these real lengths, current
eager TP4 stack and scheduling states; it does not establish a general
chunked-continuation or graph implementation. The four-output request
times are **not** fixed-1024 end-to-end performance data.

Immutable request summary SHA256:
`53e2ff137aa12f72d54d32357437509f1d7bc9ac8e58c139443583e814c30830`.
Rank-0/1/2/3 audit SHA256:
`871bebdb5d1ba2e8a64c24bcd4c75fc25689a29b795ed1dd86a4068798701b08`,
`c1ff3d858438f06aaac4e32ec7a0494c9f085aa6a613ffbf49f16dca438b6ede`,
`f6c8b96c40be98e2a3103069709dd098b26ad3282d95a6c8f4557f58317296c9`,
`2f05e7634af70323157bbdfb475e83645c332d8f9bc83c667e8f76fc08294c47`.
The service and failed diagnostic containers were stopped or exited but
retained, not removed.

Next: test sequential request retirement/reuse and longer decode state,
then decide whether a plugin-owned cache manager/graph adaptation can
eliminate the ordinary dense allocation without exceeding the paper's
24-hour gate. Only numerically valid service code may enter a same-stack
dense/candidate fixed-1024 throughput screen. Final task accuracy remains
last, per user direction.

The first 1024-output attempt (`candidate-two-requests-v5-long`) **did not
pass**: at the first decode step for the 3584-token request, rank 2/layer 47
reported selected-support native-versus-BF16-rounded-math RMS
`0.003201728` on reference RMS `0.846319258`, relative RMS about
`0.003783` against the previously frozen `0.003` ceiling. The client
did not receive completed 1024-token outputs. No throughput or task-quality
result exists for this run. The service was stopped and its per-rank audits
retained; rank-0/1/2/3 SHA256:
`a09115c2e4e96fa600ba58882424e8cce7f3662d543871bcf727d8f23fa2544c`,
`be73cd4579f3d3187dc3ecc0430a1843d657391acd1b37c9a01d4b31d3dd8351`,
`72a52da5ed637a16c16940e33c1b3827f6074d42012e65bf121f76497d3904cd`,
`5c5bee9c532da4ba6d75245854c88a80cbe73d7a16e3327866b9e66b2181a21a`.
The earlier dense-native envelope came from a different prompt and
activation distribution, so this cannot yet be classified as either a
native backend artifact or an Ada-KV integration bug. Do not relax the
threshold to rescue this run. A read-only uncompressed dense native oracle
on the same 3584-token prompt is the next diagnostic; only new evidence
may define a revised long-output gate. The user's 1% allowance applies to
eventual E2E task accuracy, not this intermediate RMS metric.

Follow-up `dense-native-red-oracle-v1` replayed the exact 3584-token red
prompt (prompt-ID SHA256
`e26502a82de7c787dfeec4504c1a44fe577a57e835c1fdffa392e7f73643699d`)
and returned HTTP 200 with four output tokens. Its read-only dense native
oracle recorded 48 layer/step checks per rank. Maximum contiguous-native
versus BF16-rounded FP32 math relative RMS across ranks was `0.002642`;
rank 2/layer 47/step 1 was `0.000763`. This is **not** identical activation
input to the pruned candidate at later layers. Dense summary SHA256:
`402088599a5f3a64c75eae9c1eadb5d640972738694a9abf95e576138eb1a4d2`.
Rank audit SHA256: `60da2deedf65d02d3eebe496e4d7efe94bfa5f32542972adcffe875b67fa572d`,
`4a847e92f4b969b16fc36c0e66602e763d658b085d2f9350e00dc3f97d05bbcd`,
`5706991d257d7c58c6813dd6f83a5e8374a8d93a4fab45576470b7174a011020`,
`5fa1229aa811b0d87d8ef3d90eafc290c068e1f86d2dcc4e9f6f514d6b4733e2`.

The separate `candidate-two-requests-v6-diagnostic32` retained every old
`0.003` breach as an audit event but, for diagnosis only, continued unless
the values became non-finite. Both 4096/3584-token requests completed 32
outputs (HTTP 200). Four ranks × 16 layers × two requests × 31 decode steps
gave 3,968 comparisons: nine breached `0.003`, worst relative RMS
`0.003757` at rank 2/layer 47/step 9; no monotonic growth or non-finite
values. This diagnostic is **not** a numerical pass and its latency includes
heavy per-layer mathematical audits, so it is not a performance result.
Summary SHA256: `7352d9ad6a5fa35b9104d7e27ea705a3bb13fe8a18a48e254ba0f1dd81372d44`.
Rank audit SHA256: `9f634ebf0f5e9482c5a46fa5f71b2b486fd1da56d0af2f6a5114a85f432a8028`,
`caa539f82cd870eaa4f1c38b00e896f586b6747e44082628bd4598fa46410b7d`,
`75a91ddfa65ce37fbe41187964d030ce779fa3c1989cd2d8235966307f1894bc`,
`7f3fb9b699d154fecee632c998b4cab6ea563443b209d2fdf5c2269ce7dabbe5`.

Before the next long-output run, the selected-support native-versus-math
screen is predeclared at relative RMS ≤`0.005`, cosine ≥`0.99998`, and
finite complete outputs. The 0.005 boundary is a 33% margin over the
observed selected-support pilot maximum, while the independent dense
native envelope was lower. It is a screening tolerance for BF16/native
rounding, not a claim that Ada-KV preserves dense-model task accuracy.
Any later breach remains a failed hard gate. The 1024-token run will sample
steps 1, 2, 8, 32, 128, 512, and 1023 on every target layer and rank;
the full 32-token pilot covers the early dense step range. No formal E2E
performance or task-accuracy result exists yet.

`candidate-two-requests-v7-hardgate1024` used that frozen gate with
diagnostic-only mode **off**. Both concurrent requests (4096 and 3584
input tokens) returned HTTP 200 and exactly 1024 output tokens. Each
rank logged 224 checks (16 layers × two requests × seven sampled decode
steps); all four ranks had zero hard failures. Worst relative RMS was
`0.002046` and minimum cosine was `0.99999797`. This is sampled
selected-support numerical correctness and long request lifecycle on the
current eager TP4 path, not full-step parity or model task accuracy.
Summary SHA256: `6aff3de7da8754333ef7aee9923b131d67211d160dff2e1a92c7df5235358685`.
Rank audit SHA256: `c42a32910c366feba84585d28f6d7d8a8b9376f3dd2febdaef8485360d9f54e4`,
`e69b0f6d7a627e7989cb2cc6d618845424bad0136fa0c61f18fc82c4e27b87bd`,
`3fcfe0b67daad76b11f795b2f27e199c776ccf97296a7be2c6be3420e50cafd9`,
`ae8eabdc04cae01e89dd49a3ba542b04e1f94d2324395c9155d98c235e0dbdf5`.
The timed request included the sampled math checks and must not be used as
the candidate performance measurement. Next is a matched, audit-disabled
dense/candidate 1024-token serving screen with explicit TTFT and TPOT.

That profiler-off, eager TP4, concurrency-two single paired screen is now
complete. Both arms used the same pinned image, model, no prefix caching,
two asymmetric token-ID prompts, four-token warmup, streaming client,
`ignore_eos=True`, and exactly 1024 output tokens per request. The candidate
had `QWEN36_ADAKV_NUMERIC_CHECK_STEPS=none` and audit decode disabled after
the separate 1024-token numerical gate. Candidate: 8.054679 output tok/s,
mean TTFT 0.891986 s, mean TPOT 0.247559 s. Dense: 8.233244 output tok/s,
mean TTFT 0.831510 s, mean TPOT 0.242217 s. Candidate/dense throughput
change is **-2.168832%**, TTFT +7.273002%, TPOT +2.205706% (higher latency
is worse). This is two requests and one paired screen, **not** the planned
40-request/concurrency-16 or three-round acceptance. The result rejects
the current per-request eager implementation as a performance winner,
not the paper mechanism on all possible Ascend implementations. The current
dense allocation remains in place, so no cache-HBM saving is claimed.
Candidate JSON SHA256: `19d246b3e93635a3cc8b39e0f522df1a37a1951afe93612b71efe4a167273ecf`.
Dense JSON SHA256: `67b05a12b0d9dcb8bb85f229633e879fda9f86a80559921026fb28bb3f3daced`.
Client script SHA256: `4d9f114f81aad4d277afbe6ad764fec5d39db30e4cdf7c0f386a36d4765cb35c`.
An initial client `BrokenBarrierError` occurred before HTTP submission
because futures were submitted lazily. That failed container was retained;
the client was fixed to submit all futures before waiting and the result
file did not exist before the successful uniquely named retry.

The next bounded adaptation targets **Ada-KV's variable selected-support
batch**, not an unrelated operator: concatenate the request-specific compact
KV and invoke the existing CANN/torch_npu TND FIA once per full-attention
layer for a pure decode batch. `grouped-fia-abi-v1` on physical NPU4 tested
KV lengths (2200,1888), (2049,3073), and (64,96). In all three cases,
grouped native output was bitwise identical to two separate native calls,
finite, and bitwise repeatable. This is storage/operator ABI evidence only,
not service correctness or speed. The grouped path is opt-in and mixed
prefill/decode still uses the prior per-request path. Gate sequence:
real TP4 grouped-versus-solo native crosscheck and selected-support math,
then 1024-token lifecycle, then another matched profiler-off screen.

## First-loop time-box decision and grouped long-output result

The first formal loop's deadline was 2026-09-26 07:05 UTC. The retained
`grouped-two-requests-v3-hardgate1024` run completed two concurrent HTTP 200
requests with 4096/3584 input tokens and exactly 1024 output tokens each.
On every physical NPU4-7 TP rank, the audit contains 32,704 grouped-decode
events, 32 per-request decode events, 32 compact-prefill events, and 16
split-native-prefill crosschecks. No failure event was recorded. Across all
four rank audits, the largest sampled selected-support native-versus-rounded
oracle relative RMS was 0.002435 (frozen limit 0.005); the minimum cosine
was 0.99999726 (frozen floor 0.99998). These checks support a scoped eager,
two-request, long-output NPU numerical/lifecycle pass, not full-step dense
parity or final task accuracy.

The summary at
`/cache/cch/qwen36-adakv-ascend-20260925/grouped-two-requests-v3-hardgate1024/two-request-summary.json`
has SHA256 `3cc5a349d6b5ef9f3a0628ca6cccf2d45c49eed8465a04d754505419b8fbbbf7`.
Rank 0/1/2/3 audit SHA256 values are respectively
`3963331a2fe97c664c870d12cc72d391cb316702435053bf9e8c64c0864d569c`,
`dec48ebb9b13092c450f53573ba15820ca037dc9fcb92c91dc6ec48e76503662`,
`8fb084e3e5928e659c4e61e9113e9653d3f6aacb3311b98a6b2d5deff59ca9b8`,
and `0d328161fb7ee1590703cea066bf3269bf7dd8e6620c9bfcbbb20af803d1c458`.
The owned container was stopped without deletion on 2026-09-28 after the
result was preserved; `npu-smi info` then showed no compute processes on
physical NPU4-7 and idle-baseline HBM near 2.87 GiB per card.

**Decision at the one-day gate:** no-go for promoting the current Ada-KV
plugin implementation. Its only profiler-off matched E2E screen is the
ungrouped concurrency-two result above (-2.168832% throughput), not the
required +10%; the grouped variant has no matched E2E result. The vLLM
dense cache allocation remains, and mixed continuation prefill, NPUGraph,
final LongBench-v2/GSM8K accuracy, and three-round 40-request/concurrency-16
performance are unproven. This is an implementation/time-box decision, **not**
a claim that the Ada-KV paper cannot benefit another Ascend cache manager.
The plugin remains explicit opt-in and disabled by default. Reopen only with
a distinct allocator/graph mechanism and a new bounded, predeclared loop;
do not spend further NPU time on the same unmeasured grouped path in this loop.

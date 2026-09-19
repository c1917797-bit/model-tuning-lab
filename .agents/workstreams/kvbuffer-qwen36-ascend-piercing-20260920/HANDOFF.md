# KVBuffer Qwen3.6 Ascend Piercing

## Terminal decision — no-go for the current non-speculative objective

Closed at `2026-09-19T22:06:59Z`. The method fits the model and has an
identifiable runtime seam, but its measured service opportunity is too small.
The recurrent GDN share is `4.520%-4.840%`; the paper's `45.17%` local
reduction implies only `1.02084x-1.02235x`, and perfect recurrent deletion
only `1.04734x-1.05087x`. An over-generous derivative scope is
`9.939%-10.063%` and would need `90.341%-91.465%` removal to reach `1.10x`,
despite containing mandatory computation.

Artifact:
`/cache/cch/kvbuffer-qwen36-ascend-20260920/opportunity-gate-v1/opportunity-audit.json`,
SHA256 `87222d251b9c625114d27ef5882d38c32e9cbdc5d4fd431bba1e023843835ee4`.
This is a diagnostic bound, not an E2E result. No operator, service A/B, or
quality run was performed. Physical NPU4-7 remained idle. DeltaLog is next.

## Activation and deadline

Activated `2026-09-19T21:58:01Z`; hard deadline `2026-09-20T21:58:01Z`.
The user explicitly promoted KVBuffer as the second paper from the original operator list. DeltaLog remains next after this slot.

## Scientific question

Can the non-speculative chunkwise-decoding part of KVBuffer, delivered as an opt-in vLLM-Ascend plugin, improve Qwen3.6-27B output throughput by at least 10% on physical NPU4-7 without changing model semantics or final quality? MTP, speculative decoding, retraining, and quantization remain excluded.

The paper is arXiv `2605.19049v1`. It buffers GDN decay, key, and delta-value tensors and periodically folds a chunk into FP32 recurrent state. No paper-linked public implementation was found at activation. The paper reports SGLang v0.5.10, custom Triton kernels, Qwen3-Next, and four NVIDIA L40S GPUs. A target implementation may be called `faithful-port` only if equations and state lifecycle match; any wider Ascend fusion is a `derivative`, never `paper-exact`.

## Architecture and runtime seam

The checkpoint `/cache/efim/Qwen3.6-27B` has 48 GDN and 16 full-attention layers. Global linear geometry is 16 key heads, 48 value heads, Dk=Dv=128; TP4 local geometry is Hk=4, Hv=12, D=128. State is FP32 and activations are BF16.

At pinned vLLM-Ascend commit `5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`, decode normalizes Q/K then calls `torch.ops._C_ascend.npu_recurrent_gated_delta_rule` on a per-request state slot. A faithful port needs paged per-request alpha/K/U buffers, occupancy and flush metadata, buffered output and batch-fold operators, cache-slot lifecycle, scheduler integration, and graph keys. Upstream sources remain read-only.

## Opportunity gate

A real four-rank, 30-step Ascend decode trace at concurrency 16 shows the recurrent GDN operator is only 4.52%-4.84% of NPU interval. Projection, convolution, gating, normalization, full-attention, MLP and collectives remain. The audit must calculate the perfect faithful bound, the paper-reported 45.17% local-reduction bound, and an intentionally over-generous derivative bound including recurrent, gating, normalization and possibly attributable slice/concat work. If the derivative needs near-total removal of mandatory compute to reach 1.10x, close early without manufacturing a microbenchmark.

## Resource state

At activation physical NPU4-7 were process-free, AICore idle and at 2868-2869 MiB HBM. Physical NPU0-3 were occupied by an external TP4 vLLM service and are protected. UDA namespaces declared all devices but had no NPU4-7 compute process or non-idle HBM, so declarations alone did not block or justify stopping them. Repeat the fail-closed check before any NPU run; stop only an exact new external overlap on physical4-7.

## Evidence

- profile: `/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/prefill-mc2-mixed-v1/profile-current-v1/baseline/profile-summary.v1.json`
- SHA256: `b3bddd3b1a8b96571f20c59d801aa21da3da673f875f86a3b04318afbdb480a8`
- paper: `https://arxiv.org/abs/2605.19049`

Kernel attribution is diagnostic, not an E2E result.

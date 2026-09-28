# Follow-on KV/linear quantization reuse gate (2026-09-28)

This is a source and historical-artifact screen, **not** a new formal paper
loop, an NPU run, a matched benchmark, or a quality result. It prevents a new
attention/matmul proposal from relabeling an existing quantization path as a
paper port or repeating an unverified historical experiment.

## Native implementation boundary

The read-only vLLM-Ascend v0.23.0 checkout at
`5cb98caaadeff42b5b62b996e34bb2aaa29d20fd` already has:

- `AscendC8KVCacheAttentionMethod` in
  `vllm_ascend/quantization/methods/kv_c8.py`. It changes the cache dtype to
  INT8, loads K/V per-channel scales and offsets from a quantized checkpoint,
  and selects `AscendC8AttentionBackendImpl`. That backend quantizes K and V
  with static per-channel parameters and invokes paged native FIA for decode.
- W8A8 static and W8A8_DYNAMIC linear methods. The dynamic method uses
  per-token activation quantization, INT8 weights, and native
  `torch_npu.npu_quant_matmul`.

These are reusable deployed primitives, not evidence that a BF16 Qwen3.6
checkpoint already carries calibration parameters or that a new paper method
is active. In particular, C8's **INT8, static per-channel K and V** is not
[KIVI](https://arxiv.org/abs/2402.02750)'s 2-bit per-channel K plus per-token
V, nor [SKVQ](https://arxiv.org/abs/2405.06219)'s reordered, clipped dynamic
group quantization with a high-precision recent window. Using C8 unchanged
must be labeled native C8, not either paper's faithful migration.

## Historical artifact found on host

The host contains untracked-by-this-workstream artifacts at
`/cache/cch/qwen36-smoothquant-20260923/`. Three saved long-context JSON
reports declare 40 successful requests, 32768 input tokens, 1024 output
tokens, concurrency 16, fixed-prefix-v1, and profiler disabled. Their labels
and measured output throughput are:

| Saved label | tok/s | Report SHA256 |
| --- | ---: | --- |
| dense | 119.042214 | `b9b08356136ae58f05d8bf9bb05320ebaf80deb3b37e1f8d430d6a27070acc1e` |
| plain quant | 125.820627 | `1b339baac0ce5cb1047c6edf0f09d800d28ed0b9e06c37478214c3af6bc2bec3` |
| SmoothQuant-labeled | 125.506975 | `52efee59664286285a44bdfb2db38dacf9e7fe0b4c444415d3d12e3b8ba7d29c` |

Arithmetic on these saved labels gives +5.43% for SQ versus dense and
-0.25% for SQ versus plain quant. This is **not an accepted comparison**:
the three client JSON files alone do not bind image, loaded checkpoint and
tokenizer hashes, operator dispatch, resource isolation, service settings,
run order, repeat count, or output/task correctness. Do not inherit the
numbers as a frozen baseline or rerun the same configuration without a new
mechanistic hypothesis.

A separate SQ-labeled diagnostic profile reports 36.9055% decode operator
time for native attention, 33.98% for MatMul, and 2.77325% for dynamic
quantization. It is a single-arm profiler result, not critical-path time or
throughput evidence. Summary SHA256:
`36e16515bf7703c0589fe51f98ca414c851e1c0347dd14c95cfaf3927f59f1d1`.

## Next investment gate

For any follow-on paper, first prove a mechanism absent from the selected
native path and a credible route to the current +10% full-service target.
If a quantized stack is used for an attention paper, apply that same stack to
the dense control; do not credit generic quantization to the new paper. Pin
the historical artifact owner and service manifests before using these
reports as evidence. Only then pre-register one paper-specific correctness
and profiler-off E2E test. No new NPU load was launched in this audit.

## KIVI-4 versus native FIA V5 applicability (2026-09-28)

This is a paper/API contract check, not a KIVI NPU result. The official KIVI
implementation supports 2- and 4-bit K/V; both variants keep a full-precision
recent window and quantize Key per channel *within each group of tokens* while
quantizing Value per token. The paper's default group size is 32 tokens and
residual length is 128. Sources:
https://github.com/jy-yuan/KIVI and https://arxiv.org/html/2402.02750 .

CANN 9.1 documents INT4 Key/Value with `keyAntiquantMode=0` and
`valueAntiquantMode=1` in `aclnnFusedInferAttentionScoreV5`. However its
per-channel Key scale is shaped for a single channel-scale set, not a distinct
scale for each 32-token Key group, and this call does not represent KIVI's
separate full-precision residual window. A direct V5 call using one global Key
scale would be a derivative quantizer, not a faithful KIVI-4 port. The existing
v0.23 C8 backend is more distant still: static INT8 per-channel K **and V**.
API contract:
https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/aolapi/context/ops-transformer/aclnnFusedInferAttentionScoreV5.md .

Decision: no-go for a *direct native V5/C8 relabeling*; do not launch a model
service or count generic cache compression as a KIVI result. Paper-level
performance remains untested. Re-enter only with a fused plugin-owned operator
or demonstrated native ABI that handles per-group Key scales, per-token Value
scales, the residual window and paged decode together, plus a shape-matched
cost gate against BF16 at the observed batch-16/long-context geometry. The
prior KVarN per-block split implementation was locally far too slow; repeating
that architecture under a new label is not a credible route. A local operator
pass would still need real-model NPU state/output/graph checks and matched
profiler-off end-to-end performance before final task accuracy.

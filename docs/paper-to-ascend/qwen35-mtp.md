# Qwen3.5 MTP to Ascend

## Paper contract

Primary method source: DeepSeek-AI, *DeepSeek-V3 Technical Report*,
arXiv:2412.19437. Its MTP design predicts additional future tokens through
sequential prediction modules and explicitly identifies speculative decoding
as an inference use. The implementation target here is not the paper's MoE
model; it is the same inference idea exposed by the MTP head already shipped
inside the frozen dense Qwen3.5-27B checkpoint.

Paper: https://arxiv.org/abs/2412.19437

The original general MTP paper is *Better & Faster Large Language Models via
Multi-token Prediction*, arXiv:2404.19737.

Paper: https://arxiv.org/abs/2404.19737

## Why this is deployable without retraining

The frozen model config declares `text_config.mtp_num_hidden_layers=1`.
Its immutable weight index contains 15 MTP tensors, including `mtp.fc`,
`mtp.layers.0`, `mtp.norm` and the MTP embedding norms. Deployment only
activates those existing weights; this workstream does not train or alter them.

The installed vLLM 0.23.0 and vLLM-Ascend source register
`Qwen3_5MTP`. The vLLM configuration normalizes the Qwen-specific method to
`mtp`, while vLLM-Ascend patches the Qwen3.5 MTP forward path.

## Ascend treatment

Use one attributable algorithm treatment:

```json
{"method":"mtp","num_speculative_tokens":1}
```

One speculative token matches the single model-provided MTP layer. Preserve
TP/DP topology, request rendering, temperature, seed, prefix caching,
`mamba_cache_mode=align`, graph policy and every other baseline input.
Qwen3.5 MTP rejects `mamba_cache_mode=all`; the frozen baseline already uses
`align`. Async scheduling permits MTP in the installed runtime.

## Hypothesis and limits

At perfect acceptance, one draft token can approach two accepted output tokens
per target verification step. That is a ceiling, not a result. Drafter cost,
rejection, scheduling, graph coverage and Ascend kernel behavior can reduce or
reverse the gain. MTP principally targets TPOT; it does not by itself prove the
required TTFT reduction.

## Evidence gates

1. Startup and graph-capture compatibility on physical NPU0-3.
2. Exact output-hash equality at temperature zero and zero request errors.
3. Speculative acceptance, accepted-token length and rejection evidence.
4. Paired TP4 development A/B at concurrency 1, 5, 8 and 16.
5. A paired profile attributing decode-step and kernel changes.
6. Cumulative A/B after adding fused GDN prefill for TTFT.
7. Final three-repetition DP2/TP4 A/B on exclusive NPU0-7.

The final decision remains fail-closed: every concurrency must achieve both
TTFT and TPOT ratios at or below 0.5 against the immutable original baseline.

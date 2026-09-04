# Prompt Lookup Decoding to Ascend

## Paper contract

Primary paper source: Yang et al., Inference with Reference: Lossless
Acceleration of Large Language Models (LLMA), arXiv:2304.04487. LLMA copies a
candidate span from available reference text and verifies it in parallel with
the unchanged target model.

Paper: https://arxiv.org/abs/2304.04487

Prompt Lookup Decoding is Apoorv Saxena's later code-level specialization
rather than an arXiv paper. It uses the current prompt and generated history
as the reference and retrieves continuations by matching n-grams. The exact
runtime's ngram_gpu implementation is the Ascend target for that specialization.

Reference implementation: https://github.com/apoorvumang/prompt-lookup-decoding

This route needs no draft model, added weights, quantization, or retraining.

## Why this candidate follows the real profile

The fixed-runtime TP4 rank-0 CANN profile used one real query_rewrite
request with 1810 prompt tokens and 104 completion tokens. After the detected
prefill boundary, MatMulV2 represented 70.702% and HCCL AllReduce 10.530%
of summed kernel duration. Those sums are diagnostic rather than wall time,
but they establish that the main opportunity is reducing verified target
decode steps, not optimizing the already-small attention share.

The exact vLLM-Ascend 0.23.0 image implements ngram_gpu with
torch.ops._C_ascend.npu_ngram_spec_decode and ships an Ascend 910B binary.
Unlike the CPU ngram proposer, the NPU path is compatible with the frozen
async scheduler.

## Ascend treatment

Use one bounded algorithm-plus-existing-operator treatment:

    {"method":"ngram_gpu","num_speculative_tokens":5,
     "prompt_lookup_min":2,"prompt_lookup_max":5}

The five-token window is a starting point, not an accepted setting. Preserve
BF16, MMAR-off, NZ1, FlashComm1-off, TP4, graph policy, prefix caching, seed,
natural EOS and the first-32 query protocol.

## Evidence gates

1. Startup and activation on assigned physical NPU4-7 only.
2. Zero request errors and natural EOS for all 32 requests per concurrency.
3. Privacy-safe labeled-reference quality aggregates; response hashes remain
   diagnostic because the no-op control proved cross-run hash drift.
4. Acceptance/efficiency counters from /metrics.
5. Fixed-original TTFT/TPOT comparison at concurrency 1, 5, 8 and 16.
6. Candidate-only CANN profiling only if E2E evidence justifies deeper work.

Reject or retune if acceptance is too low to offset verification overhead.
Do not promote it merely because the method is lossless in theory; target
runtime correctness and the frozen business-quality gate remain mandatory.

## Real Ascend result and decision

The real BF16 TP4 run on assigned physical NPU4-7 rejected this treatment.
At concurrency 1, all 32 requests completed naturally and TTFT improved by
1.188x, but TPOT regressed from 38.472 ms to 185.297 ms, or 4.82x slower.
At concurrency 5, only 25 of 32 requests completed before generation stopped
making progress for more than three minutes. The observed subset had 1626.369
ms TTFT and 412.783 ms TPOT, making TPOT 7.67x slower than the original.
Concurrency 8 and 16 were not run after the runtime failure.

The mechanism is clear from the captured counters. Of 65,435 drafted tokens,
only 4,538 were accepted (6.934%). First-position acceptance was 1,938 of
13,087 draft steps (14.809%), and each draft step yielded only 0.3468 accepted
extra tokens. Even a one-token draft cannot justify an extra verification
token at this acceptance rate, so retuning the window is rejected.

The stall evidence, service log, partial cells, decision and checksums are in
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/ngram-gpu-fixedorig-npu4-7-20260904T2048Z`.
The exact container was stopped after evidence capture; NPU4-7 returned idle
and external NPU0-3 were untouched. The next paper-to-Ascend lane is a BF16
dense FFN operator treatment selected from the measured decode shapes.

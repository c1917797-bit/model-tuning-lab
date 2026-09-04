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

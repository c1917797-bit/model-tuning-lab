# Qwen3.5-27B Dense MTP Paper-to-Ascend

## Selection

The selected method is exact speculative decoding using the checkpoint's
built-in Qwen3.5 multi-token-prediction head. The distribution-preserving
verification contract comes from *Fast Inference from Transformers via
Speculative Decoding* (arXiv:2211.17192). This checkpoint already contains the
model-specific MTP weights, so the experiment requires no retraining and no
external draft model.

The choice is tied to this host rather than a generic paper ranking:

- the installed model is a dense 64-layer Qwen3.5 hybrid with one MTP layer;
- its weight index contains 15 MTP tensors;
- installed vLLM 0.23.0 and vLLM-Ascend contain dedicated
  `qwen3_5_mtp` paths;
- existing Decode profiles are dominated by repeated dense MatMul and TP
  communication, which speculative decoding attacks by reducing serial target
  forwards rather than tuning a single kernel.

## Ascend contract

Baseline and candidate keep model, BF16 dtype, TP4, KV allocation, CPU
affinity, device mapping, workload, and cache policy fixed. The candidate uses
eager execution because that is the supported local MTP path; the frozen
runtime delta is:

```json
--enforce-eager
--speculative-config '{"method":"qwen3_5_mtp","num_speculative_tokens":3}'
```

Physical NPU0-3 and port 8220 are leased to this experiment. Physical NPU4-7,
the existing container mapped there, and port 8210 are out of scope.

## Evidence gates

1. Orientation: immutable source/model/image identities and device proof.
2. Baseline: three repeated decode-heavy runs at concurrency 8.
3. Correctness: eight greedy outputs exactly match baseline.
4. Candidate: same repeated protocol, plus draft acceptance metrics.
5. Profiling: comparable steady-state Decode capture for the representative
   concurrency, with top kernel and communication deltas.
6. Decision: accept, reject, inconclusive, or failed using the thresholds in
   the experiment record; preserve raw artifacts by path and SHA256.

## Current gate

The method is selected and the built-in implementation seam is confirmed, but
the serving A/B is not complete. A three-run diagnostic baseline was collected,
then a pre-existing service was found on physical NPU0-3; NPU4-7 were also
occupied by another existing workload. The candidate failed before weight load
because device inspection could not access an available device set.

Therefore the current decision is `inconclusive`. The baseline numbers are
retained for diagnosis but are invalid for an uncontended A/B. No candidate
performance or correctness claim is made. The workstream handoff contains the
exact safe resume sequence and historical lessons from Prefix Cache and Dynamic
MoE.

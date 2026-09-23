---
name: ascend-architecture-fit
description: Use to verify whether a paper-derived method fits the currently selected Ascend model, checkpoint, tokenizer, runtime, and serving stack before implementation or benchmark comparison.
---

# Ascend Architecture Fit

## Purpose

Prove that the target model and runtime actually contain the mechanism a paper
needs. Architecture fit is a live/repository fact, not a preference. It prevents
MoE-only, MTP-only, quantization-only, sparse-only, multimodal, or retraining
methods from being applied to an incompatible target.

## Workflow

1. Start from the user's selected target. If none is selected, use the current
   handoff target only as a default snapshot, not as a permanent restriction.
2. Record checkpoint and tokenizer identity: path or revision, non-secret hash
   when available, config files, dtype/quantization, model family, and serving
   launch parameters.
3. Inspect whether the paper-required mechanism exists: dense, MoE experts,
   MTP/speculative heads, attention form, KV/cache metadata, sparsity,
   quantization metadata, multimodal towers, adapters, or training artifacts.
4. Verify runtime support in the actual stack: vLLM, vLLM-Ascend, torch-npu,
   CANN, operators, launch args, environment variables, and container image.
5. Decide the fit level:
   - `fits-now`: the mechanism and runtime seam exist;
   - `fits-with-config`: no code change is needed, but serving/config changes
     are required;
   - `fits-with-implementation`: source changes are plausible and bounded;
   - `requires-retraining`: stop unless the user explicitly authorizes training;
   - `does-not-fit`: reject or choose another target/paper.
6. Record the decision and evidence in Git before implementation.

## Boundaries

- Dense being current does not forbid future MoE, sparse, quantized,
  multimodal, or retraining work; it only means those targets must be selected
  and proven.
- Do not rely on model names alone. Check config and runtime behavior.
- Do not compare benchmarks across architecture or runtime drift; re-baseline.

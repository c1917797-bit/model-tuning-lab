# Sparse Prefix Ascend plugin

This is an explicit opt-in policy adapter for arXiv:2605.05219. It reuses the
already validated HYPIC v0.8.5 Ascend state/KV materialization and restoration
path and changes only the exact-prefix checkpoint positions.

It does not modify vLLM, vLLM-Ascend, CANN, or the HYPIC source tree.

Enable both plugins and provide a frozen plan:

    VLLM_ASCEND_HYPIC_ENABLE=1
    VLLM_ASCEND_SPARSE_PREFIX_ENABLE=1
    VLLM_ASCEND_SPARSE_PREFIX_PLAN=/absolute/path/plan.json

The plan is fail-closed: positions must be positive, strictly increasing,
aligned to the runtime full-attention block size, within the declared maximum
length, and no more numerous than the declared checkpoint budget.

The plugin alone is not performance evidence. Acceptance requires real NPU
correctness followed by the frozen same-budget end-to-end A/B protocol in the
workstream experiment record.

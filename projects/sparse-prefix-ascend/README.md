# Sparse Prefix Ascend plugin

This is an explicit opt-in research adapter for arXiv:2605.05219. It implements
the paper's distribution-aware checkpoint placement and probes whether the
existing HYPIC v0.8.5 Ascend state/KV path can host that policy.

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

## Current v0.23 decision

The thin-adapter path is rejected for vLLM-Ascend 0.23. On physical NPU4-7 the
runtime loaded the 1536-aligned plan and the patched scheduler selected
checkpoints 7680 and 3072 for a 9216-token request. The next scheduler step
failed closed because HYPIC exact-prefix replay rejects every native prefix
cache manager with caching enabled.

This is not a paper-level rejection. A faithful implementation needs a deeper
runtime seam that keeps full-attention KV pages under the native prefix cache
while committing GDN recurrent checkpoints only after their state is complete.
The v0.23 HYPIC material store otherwise expects both full-attention KV and GDN
material for each segment, which is not the paper's storage contract.

See [PIERCING_REPORT.md](PIERCING_REPORT.md). No end-to-end performance or
accuracy result is claimed from this probe.

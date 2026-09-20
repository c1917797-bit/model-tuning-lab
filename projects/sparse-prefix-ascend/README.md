# Sparse Prefix Ascend plugin

This is an explicit opt-in research adapter for arXiv:2605.05219. It implements
the paper's distribution-aware checkpoint placement and a bounded atomic
coexistence protocol for native full-attention KV plus HYPIC GDN/conv
checkpoints.

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

## Current v0.23 status

The original thin-adapter path is rejected for vLLM-Ascend 0.23. On physical NPU4-7 the
runtime loaded the 1536-aligned plan and the patched scheduler selected
checkpoints 7680 and 3072 for a 9216-token request. The next scheduler step
failed closed because HYPIC exact-prefix replay rejects every native prefix
cache manager with caching enabled.

The v0.2 re-entry implements that deeper seam entirely in this plugin. Native
vLLM owns full-attention KV pages; HYPIC's existing transaction owns GDN/conv
material. Native KV reads are invisible until a matching recurrent checkpoint
is ready, and the native lookup is bounded to exactly that checkpoint. HYPIC
full-attention repair must be disabled and the reviewed HYPIC scheduler source
hash must match.

This code passes 12 focused software tests but failed the real NPU replay gate.
With a deterministic dense reference, only 7/8 measured hot replays matched;
one request diverged from the first generated token despite a complete atomic
transaction event. The current v0.23 integration is therefore a no-go. No
performance or accuracy result is claimed.

See [PIERCING_REPORT.md](PIERCING_REPORT.md). No end-to-end performance or
accuracy result is claimed from this probe.

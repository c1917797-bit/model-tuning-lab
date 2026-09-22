# Qwen3.6 SparQ real-path diagnostic

This is a non-mutating, eager-only diagnostic plugin, **not** a candidate
acceleration. Add both `/workspace/plugin` and `/workspace/tools` to
`PYTHONPATH`, set `QWEN36_SPARQ_PROBE_ENABLE=1`, and provide a writable
`QWEN36_SPARQ_PROBE_AUDIT` path outside Git. Use `--enforce-eager` for this
diagnostic only. The plugin verifies the pinned vLLM-Ascend attention source,
lets dense decode finish, then samples one rank-0, layer-3, batch-1 decode at
sequence length at least 2048. It compares 25% and 50% selected-page native
attention with the unchanged dense layer output and records paper top-k page
coverage. It never substitutes the candidate output into the model.

The diagnostic deliberately uses a full-K materialization and multiple
host synchronizations; its times are *not* candidate service timing.
Graph-mode and full TP4 candidate dispatch are separate gates.

# Qwen3.6 DeltaLog vLLM-Ascend plugin

This directory is a self-contained Python entry-point distribution. Add it to
`PYTHONPATH` and enable it explicitly:

- `QWEN36_DELTALOG_ENABLE=1`
- `QWEN36_DELTALOG_LIBRARY=/absolute/path/libqwen36_gdn_deltalog_decode_ops.so`
- `QWEN36_DELTALOG_AUDIT=/writable/path/evidence.jsonl`

The adapter is pinned to the audited vLLM-Ascend v0.23 GDN source and v3
operator hashes. It allocates persistent per-layer auxiliary state, dispatches
only the exact Qwen3.6-27B TP4 non-speculative decode ABI, and uses the native
path for unsupported calls. Before a native fallback it materializes any live
DeltaLog entries so the dense state remains semantically current; prefill then
resets the addressed auxiliary slots.

A valid service run must contain `plugin_installed`, `aux_allocated`, and
`candidate_dispatch` events from every tensor-parallel worker. These events
prove dispatch only; throughput and task accuracy require separate gates.

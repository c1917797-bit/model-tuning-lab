# Qwen3.6 GDN decode-core vLLM plugin

This directory is a self-contained Python entry-point distribution. Add it to
`PYTHONPATH` and set the two explicit opt-in variables:

- `QWEN36_GDN_DECODE_CORE_ENABLE=1`
- `QWEN36_GDN_DECODE_CORE_LIBRARY=/absolute/path/libqwen36_gdn_decode_core_ops.so`

Set `QWEN36_GDN_DECODE_CORE_AUDIT` to a writable JSONL path. A valid candidate
run must contain `plugin_installed` and `candidate_dispatch` records from
every tensor-parallel worker. Unsupported paths call the unmodified v0.23
implementation and emit a bounded `native_fallback` record.

The plugin is intentionally pinned to the audited vLLM-Ascend source and
candidate-library hashes. It fails closed if either identity or the operator
schema changes. It never edits or globally replaces files in vLLM-Ascend.

# C2 model-layer source audit

Inspected the unchanged official image without devices or model mounts in
operation exec-000000000000005f. Image identity:
`sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
Official `vllm/model_executor/models/qwen3_next.py` SHA256:
`8d614ce262ab9340585f9a2ad4ab117228f076e3672fcb5f04930ff0a38223ae`.

## Observed execution chain

`Qwen3NextDecoderLayer.forward` performs input RMSNorm/residual fusion, calls
linear or full attention, performs post-attention RMSNorm/residual fusion,
then MLP. It returns both hidden states and residual. Full attention invokes
`Qwen3NextAttention.forward`, which performs QKV projection, gated-Q split,
Q/K normalization, RoPE, attention, sigmoid output gating, and O projection.

The current `independent_c2_kv_hook.py` wraps the attention backend after QKV
projection. It truthfully emits `projection_skipped=False` and
`attention_queries_skipped=False`. Its bounded Canary proves relocation and
private ownership only; it does not implement C2 compute pruning.

## Required next implementation

1. Freeze request-owned retained rows before entering decoder layers: private
   prefix, seam window, and suffix; public body rows have reusable material.
2. Keep position, logical sequence length, physical KV slots and per-layer
   attention metadata consistent with compact query rows. Shortening the
   hidden-state tensor alone is invalid.
3. Execute normalization, projections, attention, residual and MLP on the
   retained rows and propagate their hidden states across all hybrid layers.
4. At each linear layer, apply the independently derived body transition to
   the actual incoming state after boundary correction, preserving request
   conv-tail/state ownership. Compact state material alone does not supply
   arbitrary per-token hidden outputs.
5. At each full-attention layer, install relocated body KV into owned physical
   slots before retained seam/suffix queries attend; preserve Q normalization,
   output gating, O projection, and residual semantics from official source.
6. Validate compact metadata, seam propagation and rollback on a bounded real
   request before formal performance. No compute-saving claim until measured
   projected/query row counts prove body work was skipped on every TP rank.

Prior successful experience may guide CPU material placement, seam size,
bounded hot-request admission and replay batching. It is not a source of
algorithm/runner/scheduler implementation bytes. No old HYPIC source was used
in this inspection.

## Current authority

Remote HEAD inspected as `460f26dadd34333b71aa97b16eac2a0e3a9a0ce0`, clean,
ahead21. Credential recovery restored force-direct ma access. No device job
was launched by this audit. Latest user scope remains27B/singleTP4/physical0-3,
with deadline2026-10-14T19:03:48Z. DistributedC3/dualTP2 is excluded by the
later human clarification recorded in task.json.

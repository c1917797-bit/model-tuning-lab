# DASC Source Map

## Validated Runtime Facts

Reference source inspected from `/cache/austinov/src/vllm-ascend`.

### GDN metadata

File: `/cache/austinov/src/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py`

- `block_table_tensor[:, 0]` is used as the non-spec GDN state/cache index for common non-spec paths.
- Prefill metadata records `prefill_state_indices`, `prefill_has_initial_state`, and conv1d `cache_indices`.
- `prefill_has_initial_state` is derived from `context_lens_tensor > 0`, which is the key signal for a reused or continued state.
- Decode metadata records `non_spec_state_indices_tensor` and conv1d cache indices.

### GDN state update

File: `/cache/austinov/src/vllm-ascend/vllm_ascend/ops/gdn.py`

- `self.kv_cache[0]` is the convolution state cache.
- `self.kv_cache[1]` is the recurrent/temporal GDN state cache.
- Prefill path reads `initial_state = ssm_state[prefill_state_indices].transpose(-1, -2).contiguous()`.
- `clear_ssm_states(initial_state, prefill_has_initial_state)` zeroes entries without prior state.
- Prefill writes back `ssm_state[prefill_state_indices] = last_recurrent_state.transpose(-1, -2).contiguous().to(ssm_state.dtype)`.
- Decode path updates `ssm_state` in-place through `torch.ops._C_ascend.npu_recurrent_gated_delta_rule(..., state=ssm_state, ssm_state_indices=...)`.

## DASC-NR Candidate Injection Point

The smallest candidate should hook the live GDN core before recurrent computation and only when a row has prior state. For a cache-hit row, reconstruct the compute-layout recurrent state as:

1. Start from zero for all heads.
2. Copy retained heads from a DASC compressed checkpoint into the matching head positions.
3. Leave omitted heads zero for DASC-NR.
4. Write the reconstructed row into `ssm_state[state_index]` before the native recurrent op consumes it.

This preserves native Ascend recurrent kernels and changes only the recurrent-state checkpoint representation/load policy.

## Still Unknown

- Whether current vLLM-Ascend persists recurrent state checkpoints across prefix-cache entries, or only maintains active request state rows.
- Where prefix-cache hit length and cached state checkpoint identity are exposed to model-layer code.
- Whether conv state must be stored dense for every checkpoint or can be compressed/omitted in local experiments.
- Whether graph capture requires DASC-NR to be part of graph-key/config identity.

## Current Fit Classification

`fits-with-implementation`: the GDN state layout and weight-derived selector fit the target, but DASC's serving benefit needs a plugin-owned state checkpoint store/load path if vLLM-Ascend lacks one.


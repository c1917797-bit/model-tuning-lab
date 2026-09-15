# DASC Source Map

## Source Identity

- vLLM: `/cache/austinov/src/vllm`,
  `0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665`.
- vLLM-Ascend: `/cache/austinov/src/vllm-ascend`,
  `5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`.

These are reference checkouts. The final implementation must remain a
plugin-owned monkeypatch and must prove its live imported paths in the serving
container before an NPU claim.

## Validated GDN Runtime Facts

### GDN metadata

File: `vllm_ascend/ops/gdn_attn_builder.py`

- `block_table_tensor[:, 0]` is the common non-spec GDN state/cache index.
- Prefill metadata records `prefill_state_indices`,
  `prefill_has_initial_state`, and conv1d cache indices.
- `prefill_has_initial_state` is derived from `context_lens_tensor > 0`.
- Decode metadata records `non_spec_state_indices_tensor` and conv1d cache
  indices.

### GDN state update

File: `vllm_ascend/ops/gdn.py`

- `self.kv_cache[0]` is the convolution state cache.
- `self.kv_cache[1]` is the recurrent/temporal GDN state cache.
- Prefill reads the selected temporal row, transposes it to compute layout,
  clears rows without prior state, and writes the final recurrent state back.
- Decode passes the full state tensor plus block-derived row indices to
  `torch.ops._C_ascend.npu_recurrent_gated_delta_rule`, which updates the
  selected rows in place.

## Validated Mamba/GDN Prefix-State Lifecycle

The earlier generic-`KVCacheManager` inspection was incomplete. The current
stack already has a dedicated Mamba/GDN checkpoint lifecycle:

- `MambaManager.find_longest_cache_hit()` searches cached Mamba blocks and
  returns an aligned state block at the prefix-hit boundary.
- In align mode, `MambaManager.allocate_new_blocks()` records that cached
  state block for a new prefix-hit request and allocates a running-state block.
- `vllm_ascend.patch.worker.patch_mamba_utils.preprocess_mamba()` derives the
  previous state block from `req_state.num_computed_tokens`, request block
  IDs, and `mamba_state_idx`.
- `collect_mamba_copy_meta()` visits every GDN layer and both cache tensors,
  copying convolution and temporal state from the cached prefix block to the
  current running-state block.
- `model_runner_v1.execute_model()` executes the state copy immediately before
  model forward, after connector loading. GDN metadata then uses the current
  block ID as the native operator's state index.

Therefore a separate request-ID transport into every GDN layer is not required
for the first DASC port. The existing block lifecycle is the correct seam.

## Revised DASC-NR Implementation Gap

The missing capability is physical compression, not prefix-state identity.
Zeroing omitted heads inside the existing dense temporal-state tensor can test
DASC-NR numerics, but it saves no cache memory and cannot support the paper's
capacity or cache-hit TTFT claim.

The performance-bearing plugin path must virtualize the representation:

1. keep a compact retained-head temporal checkpoint in block-backed cache;
2. materialize a dense per-active-request temporal workspace before the native
   recurrent operator;
3. preserve or separately account for the convolution checkpoint;
4. run the unchanged native Ascend GDN operator on the dense workspace;
5. compress the resulting temporal state back into retained-head storage at an
   aligned checkpoint boundary.

The first physical-capacity canary must prove that page-size accounting and
admitted cache capacity really change. A dense cache plus a sidecar compressed
copy is only a numerical canary.

## Candidate Injection Points

- Scheduler/cache lifecycle:
  `vllm.v1.core.single_type_kv_cache_manager.MambaManager`.
- Worker state movement:
  `vllm_ascend.patch.worker.patch_mamba_utils.preprocess_mamba`,
  `collect_mamba_copy_meta`, and the pre-forward copy call in
  `vllm_ascend.worker.model_runner_v1`.
- State allocation contract:
  `MambaBase.get_kv_cache_spec()` and `MambaSpec.shapes/page_size_bytes`.
- Native compute boundary:
  the GDN core immediately before recurrent prefill/decode execution.

The plugin must install after Ascend runtime patches, use explicit opt-in,
validate source identities, emit activation evidence from every TP worker, and
fail closed on an unsupported layout or version.

## Still Unknown

- Which live binding hook can substitute compact block storage plus dense active
  workspace without upstream edits.
- Whether the convolution checkpoint must remain dense for every retained
  checkpoint in the first faithful port.
- Whether DASC mode, retained-mask identity, and workspace shape must enter the
  graph key, or whether the first canary must force eager execution.
- Whether compact page sizes alter hybrid-group balancing or alignment
  constraints elsewhere in `kv_cache_utils`.

## Canary and Benchmark Boundary

The first numerical canary may use dense storage to validate DASC-NR
reconstruction against a dense control on real Ascend. It cannot claim capacity
or performance. The next canary must prove compact allocation, prefix hit,
state reconstruction, native GDN consumption, cache admission increase, and
rollback. Only then may a one-switch cache-fill/replay TTFT A/B run.

## Current Fit Classification

`fits-with-implementation`: GDN architecture, weight-derived selection, and
the prefix-state lifecycle fit. The remaining feasibility gate is a
plugin-owned compact-cache/dense-workspace virtualization path whose capacity
arithmetic is real rather than simulated.

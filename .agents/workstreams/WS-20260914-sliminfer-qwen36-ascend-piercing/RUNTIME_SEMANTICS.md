# Runtime semantics and first faithful-port gate

## Why the model loop alone is insufficient

The pinned Qwen3.6 path flattens all scheduled request rows before the model and
builds positions, slot mappings and attention metadata once. SlimInfer changes
the active prompt rows per layer. Therefore a correct implementation must
change five identities together:

1. gather hidden and residual rows using request-local absolute token IDs;
2. keep the original absolute positions for RoPE;
3. rebuild compact per-request query boundaries;
4. store full-attention KV in compact logical cache positions;
5. retain each GDN layer's request state index while recomputing its compact
   sequence boundaries and state transition.

Using absolute token positions as compact KV slots would leave holes that the
attention backend cannot distinguish from valid cache entries. Using compact
positions for RoPE would instead change the model's positional semantics.

## Decode continuation

For a request with prompt length P, retained prompt length K, and g
already-generated tokens:

- the next model/RoPE position is P + g;
- the next logical full-attention KV position is K + g;
- each GDN layer continues from the recurrent state produced by its own compact
  prompt sequence.

The plugin must preserve this separation for every request and layer. Physical
full-attention slots are derived from the layer's existing block table and the
compact logical KV position; raw GDN block tables must continue through the
existing mamba_get_block_table_tensor path.

## Whole-prompt gate

The first semantic canary deliberately rejects partial or resumed prompt
prefills. A pruning decision made after only an early chunk cannot retroactively
save later-layer work for prompt rows that already crossed the full model. The
formal concurrency-16 ruler may schedule partial prompt chunks under the
40,960-token batch budget, so production admission additionally requires one
of:

- scheduler-level whole-prompt admission for eligible long requests; or
- a proven cross-chunk hidden-state staging design that delays later layers.

The first option is the bounded piercing route. Its scheduling effect must be
applied to the dense comparison as a common optimization or separately
decomposed; it cannot be hidden inside the treatment claim.

## Evidence currently available

stream_contract.py is a device-independent executable specification. It checks
paper-faithful first-sink retention, request-local row gathering, absolute
position identity, compact cache positions, physical block-table mapping,
decode continuation and fail-closed whole-prompt admission. Generated response
tokens are retained separately from prompt-block selection. Passing these tests
is only a precondition for building live Ascend metadata; it is not NPU,
performance or quality evidence.

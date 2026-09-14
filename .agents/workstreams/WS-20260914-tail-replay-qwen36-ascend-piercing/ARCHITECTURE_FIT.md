# Architecture fit — Tail-Replay on Qwen3.6-27B

## Decision

**fits-with-implementation, medium-to-high integration risk**.

Unlike SlimInfer, the paper directly evaluates Qwen3.6-27B and targets the
exact three-GDN/one-full-attention hybrid pattern. The algorithm is therefore
better aligned with this checkpoint and the shared-prefix workload, but the
paper does not provide an Ascend or vLLM implementation.

## Proven target identity

- Checkpoint: /cache/efim/Qwen3.6-27B.
- Architecture: 64 layers, with GDN at 0-2, 4-6, ..., 60-62 and full attention
  at 3, 7, ..., 63.
- GDN state is FP32; TP4 gives 12 local value heads with 128 by 128 state
  matrices per layer.
- The live model loop keeps hidden_states and residual separately and
  executes one flattened token tensor through all layers.
- The live attention metadata has four shared objects: one for all 16
  full-attention layers and three for the three relative GDN positions.

## Required adaptation

- Cache identity must include model, weights, layer, token identity, positions,
  dtype/layout and algorithm version.
- A full-attention boundary hidden in the paper corresponds to the next GDN
  input. In this vLLM loop the residual decomposition must be preserved or
  combined exactly; caching only the temporary MLP output is not equivalent.
- Layers 0-2 precede the first full-attention layer. Their exact replay source
  must be the model-input embedding/residual boundary, not an invented prior
  full-attention output.
- Replaying a GDN group must reconstruct both the recurrent matrix state and
  the short causal-convolution state.
- Shared metadata objects cannot hold layer-local replay state. State remains
  per request and per layer; metadata updates must be transactional.
- Prefix-cache hits, partial blocks, chunked prefill, eviction and graph keys
  need explicit contracts before end-to-end enablement.

## Portability rule

The design must use public PyTorch/vLLM/vLLM-Ascend seams and feature-detect
the live model pattern. Ascend-specific acceleration may replace replay
kernels later, but cache format and algorithm semantics must not depend on one
910B kernel binary, fixed pointer layout, or global monkeypatch side effect.

## Admission order

1. Projected-recurrence oracle on the existing NPU kernel.
2. Full GDN-layer replay including causal convolution.
3. One independent three-GDN group from a cached boundary hidden.
4. All groups plus first-token parity/quality.
5. Prefix-cache hit integration.
6. Only then FFN skip, transfer overlap, graph support and formal performance.

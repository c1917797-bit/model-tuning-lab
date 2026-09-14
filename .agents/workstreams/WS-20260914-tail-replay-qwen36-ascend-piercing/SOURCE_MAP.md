# Validated source map — Tail-Replay

## Paper concept to pinned seam

| Concept | Pinned source seam | SHA256 |
|---|---|---|
| Qwen3.6 layer selection | /vllm-workspace/vllm/vllm/model_executor/models/qwen3_5.py | 04f3de5372973770d71c5c05f2e8a5e221ec52b62cca7a1e302d9201b61b8adc |
| Outer layer loop and residual pair | /vllm-workspace/vllm/vllm/model_executor/models/qwen3_next.py | 8d614ce262ab9340585f9a2ad4ab117228f076e3672fcb5f04930ff0a38223ae |
| Live Ascend model patches | /vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py | 21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3 |
| GDN projection, conv and state commit | /vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py | d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816 |
| GDN request/state metadata | /vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py | 42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16 |
| Chunk recurrence implementation | /vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/chunk.py | 6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5 |

All identities were read from pinned image
sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1.

## First canary seam

AscendGatedDeltaNetAttention._forward_core provides the exact layer prefix.
Its module-global chunk_gated_delta_rule receives post-convolution Q/K/V, raw
log-gates, beta, a fresh initial state, cumulative sequence lengths and returns
the final FP32 recurrence state.

The plugin wraps these two live objects:

- the core wrapper establishes request-local layer identity;
- the chunk wrapper executes the normal call first, leaves its output
  unchanged, then performs diagnostic exact-split and zero-tail calculations
  using separate state tensors.

The first canary is eager, batch one, one fresh prefill, and 128-4096 tokens.
It does not write replay state into vLLM cache and cannot change generated
tokens. This intentionally separates recurrence feasibility from service
integration.

## Later seams still to prove

- capture of combined FA output/residual boundaries;
- model-input boundary for GDN layers 0-2;
- per-layer convolution and matrix-state replacement;
- exact FA KV block reuse and cache identity;
- cache-hit matched/unmatched boundary in the scheduler;
- NPUGraph keys and cache lifecycle;
- host transfer stream and synchronization.

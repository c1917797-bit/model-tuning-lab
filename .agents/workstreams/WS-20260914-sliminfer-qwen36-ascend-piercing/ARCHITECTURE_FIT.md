# Architecture fit — SlimInfer on Qwen3.6-27B

## Decision

**fits-with-implementation, high semantic and serving-integration risk**.

This is not `fits-now`: the official code supports Hugging Face Llama-3.1 and
Qwen2.5 with FlashAttention2 and a batch-one custom cache. It is not compatible
with the frozen Qwen3.6/vLLM-Ascend service as-is.

## Proven target identity

- Checkpoint: `/cache/efim/Qwen3.6-27B`.
- Architecture: `Qwen3_5ForConditionalGeneration`, text config
  `qwen3_5_text`, BF16, no quantization declared in the checkpoint config.
- Layers: 64 total, repeating three `linear_attention` layers and one
  `full_attention` layer: 48 GDN linear-attention and 16 full-attention.
- Full attention: 24 query heads, 4 KV heads, head dimension 256.
- GDN: 16 key heads, 48 value heads, key/value dimension 128, FP32 recurrent
  state.
- MTP exists in the checkpoint metadata but remains disabled in this ruler.
- Pinned serving image:
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
- Reference vLLM-Ascend: v0.23.0,
  `5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`.

## Required adaptation

The live model uses a flattened token tensor and alternates GDN and full
attention. Official SlimInfer removes token rows after selected layers and
propagates a layer-specific active token set. On this target that also changes:

- the tokens consumed by later GDN recurrences and their persistent state;
- the full-attention KV slots that exist at each layer;
- positions, masks, and request boundaries in a flattened continuous batch;
- graph shapes/keys and TP4-consistent selection;
- scheduler/cache-manager accounting, which normally assumes one computed-token
  count per sequence rather than one per layer.

These are genuine method-chain requirements. Omitting them would create a
SlimInfer-inspired derivative, not a faithful port.

## Staged identity

1. `faithful-port-feasibility`: no CPU offload; preserve the paper's
   layer-specific active token and hidden-state restoration semantics.
2. `faithful-port-with-async-cache`: add overlap-aware NPU/CPU prompt-KV
   movement only after stage 1 is correct and beneficial.
3. Any hybrid-safe scatter/pass-through shortcut is labeled
   `sliminfer-inspired-derivative` and receives a separate experiment ID and
   baseline.

No retraining is required by the paper, but this target architecture was not
validated by the authors; local quality evidence is mandatory.

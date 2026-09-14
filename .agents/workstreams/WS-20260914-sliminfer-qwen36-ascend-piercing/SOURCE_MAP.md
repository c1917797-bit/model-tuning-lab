# Validated source map

## Paper concept to target seam

| Concept | Pinned target seam | Required evidence |
|---|---|---|
| Layer-wise token stream | `/vllm-workspace/vllm/vllm/model_executor/models/qwen3_5.py`, `Qwen3_5Model` / `Qwen3_5DecoderLayer` | exact live import and worker-rank activation |
| Hybrid layer execution | `/vllm-workspace/vllm/vllm/model_executor/models/qwen3_next.py`, decoder/model forward loops | active row count and request ownership at every pruning boundary |
| Full-attention KV | vLLM attention layer plus vLLM-Ascend attention backend/cache metadata | absolute position, block table and slot identity |
| GDN recurrent state | Qwen gated-delta attention and vLLM-Ascend GDN operators | multi-step state parity for the selected stream |
| Request/token metadata | vLLM-Ascend model runner/input batch | per-request selections, no cross-request mixing |
| Graph capture | vLLM-Ascend model runner/graph wrapper | explicit graph key or eager-only first canary |
| CPU/NPU swapping | separate, opt-in plugin cache manager | stream/event correctness and measured overlap |

## Pinned execution-path findings

- `vllm/model_executor/models/qwen3_5.py` selects `linear_attention` GDN or
  `full_attention` in `Qwen3_5DecoderLayer`; `Qwen3_5Model` then uses the
  `Qwen3NextModel` loop.
- `qwen3_next.py` carries one flattened `hidden_states` tensor and one
  `positions` tensor through every layer. A row-pruning implementation must
  therefore restore hidden rows, not only shorten a KV view.
- `vllm_ascend/worker/npu_input_batch.py` holds request-global token counts.
  `model_runner_v1.py` builds positions, sequence lengths and slot mappings
  before model forward, and attention layers within a cache group share the
  same common metadata.
- `gdn_attn_builder.py` converts the GDN block table into persistent state
  indices. `gdn.py` consumes every received prefill row and commits FP32
  recurrent state, so pruning rows changes GDN semantics rather than only
  cache size.
- `vllm_ascend/patch/worker/patch_qwen3_5.py` replaces decoder-layer,
  full-attention and GDN methods, but not the outer Qwen3.5 model loop. A
  general vLLM plugin can therefore hook the outer loop without editing the
  pinned repositories, provided the live import is proven on all ranks.

## Faithful-port contract implied by the map

A faithful hybrid port needs per-layer active absolute token IDs, layer-local
attention metadata/slots/sequence lengths, TP-consistent score reduction before
top-k, hidden-state restoration for later decode, and an explicit definition of
GDN recurrent state over the compressed sequence. The existing request-global
metadata cannot simply be reused with a smaller row tensor. A shortcut that
only masks full-attention KV is a derivative and must use a different result
label.

The first semantic implementation must reject partial/resumed prefill. Under
the 40,960-token batch budget a 32K request can fit whole, but a second request
may be admitted only partially. A scheduler gate is therefore part of the
candidate design, not an incidental benchmark setting.

## Smallest first change

Do not edit the original vLLM or vLLM-Ascend repositories. Add an explicit,
environment-gated plugin under this repository that initially contains only:

- a pure per-request block planner with stable absolute indices;
- a frozen Qwen3.6 layer plan;
- activation/invariant events;
- a disabled-by-default model-loop hook for an eager, single-request canary.

The repository now contains that planner plus an identity-preserving runtime
canary registered through `vllm.general_plugins`. It is disabled by default and
supports only `identity-canary`; no pruning code is active. The first NPU canary
still excludes CPU offload and graph capture. It must prove the
exact imported object, all TP ranks, request success, finite outputs/state,
stable absolute-token mapping, and disabled-control marker absence.

## What not to change yet

- no CANN operator generation;
- no NPU/CPU asynchronous cache manager;
- no continuous-batching scheduler rewrite;
- no NPUGraph enablement;
- no full HYPIC-sized performance or quality run.

Those stages are admitted only after the planner and layer/state semantics pass
their smaller gates and the opportunity bound is positive.

## Rollback

The plugin is disabled unless `MST_SLIMINFER_ENABLE=1`. Removing the plugin
mount or unsetting the variable restores the baseline without changing the
pinned image or reference repositories.

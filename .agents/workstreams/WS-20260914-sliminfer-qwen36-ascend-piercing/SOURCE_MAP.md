# Initial source map

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

## Smallest first change

Do not edit the original vLLM or vLLM-Ascend repositories. Add an explicit,
environment-gated plugin under this repository that initially contains only:

- a pure per-request block planner with stable absolute indices;
- a frozen Qwen3.6 layer plan;
- activation/invariant events;
- a disabled-by-default model-loop hook for an eager, single-request canary.

The first NPU canary excludes CPU offload and graph capture. It must prove the
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

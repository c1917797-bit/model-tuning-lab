# Production GDN contract: next evidence, not an established root cause

The physical1 standalone BOLE call matches the FP64 oracle for P/U/Y and four selected states (7/7). The saved production P/U/Y replay still differs (relative L2: 0.1779066855 / 9.4778606130 / 7.6592700021). Qualification remains false. A stream-change benefit has not been isolated by matched old/new binary A/B.

First inspect only host-local actual installed files/commits and actual callee identities; the current upstream implementations below are reference hypotheses, not proof of this host's behavior.

1. Verify same request/token/layer, after conv+activation and before GDN; Qwen3.5 projections use [q,k,v,z] / [b,a], not an assumed interleaving.
2. Verify Q/K L2norm, dtype/epsilon and scale happen exactly once. Ascend can normalize before kernel and pass scale separately.
3. Verify beta=sigmoid(b); g is log decay, with state factor exp(g). Name, order, shape and domain must agree at actual call.
4. Verify [T,Nk,Dk], [T,Nv,Dv], [T,Nv], TP-local head grouping, actual sequence lengths and state slot indices.
5. Verify state layout: current upstream Ascend recurrent cache [Block,Nv,Dv,Dk] vs HF/FLA [N,H,Dk,Dv]; fallback transposes. Dk=Dv=128 hides a content transpose error from shape checks.
6. Verify input snapshot precedes inplace state update and owns independent storage. detach alone does not isolate a view; compare stride/storage offset and snapshot completion.

Primary sources:
- https://github.com/vllm-project/vllm-ascend/blob/main/vllm_ascend/ops/gdn.py
- https://github.com/vllm-project/vllm/blob/main/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py
- https://github.com/vllm-project/vllm/blob/main/vllm/third_party/flash_linear_attention/ops/fused_gdn_prefill_post_conv.py
- https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen3_5/modeling_qwen3_5.py

Device lessons: is_available() short-circuits count evaluation; count was not measured in earlier failures. Native function identities unchanged across bootstrap rule out claiming an observed import substitution. HAL87=RESOURCE_OCCUPIED and ACL507899=driver internal error do not establish compute occupancy or missing mounts. Exact own PID kernel logs locate UDA mount-namespace conflict. Do not solve by privileged/all-device access or guessed mounts. Current public namespace_node debug reading may recycle idle registration; do not repeatedly read it under a 'strictly read-only' assumption.

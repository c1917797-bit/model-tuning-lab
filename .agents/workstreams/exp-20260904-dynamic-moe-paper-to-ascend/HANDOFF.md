# Dynamic MoE Paper-to-Ascend Workstream

## Status

- Execution: `in-progress`
- Integration: `not-ready`
- Base: `fbc79c41c37c8900f0623ce8941304e9bfde5cf1`
- Hardware lease: `chicaihong01 NPU0-3`
- Do not use NPU4-7; they are owned by the active prefix-cache workstream.

## Paper exemplar

- Paper: *Harder Tasks Need More Experts: Dynamic Routing in MoE Models*
- ACL 2024 / arXiv:2403.07652
- Upstream code: `https://github.com/ZhenweiAn/Dynamic_MoE`
- Pinned upstream commit: `f56bc20db176f22ab51cb56b7dcb96403fb2cd8a`
- Local read-only reference: `/home/mtuser/cch/paper-sources/Dynamic_MoE`
- Upstream behavior to preserve: softmax router probabilities, descending sort, then keep the minimal expert prefix whose cumulative routing mass reaches `top_p_threshold`.
- Historical upstream default in `MoEConfig`: `top_p_threshold=0.4`.

## Pipeline state

1. `paper-contract`: implemented as documentation/config.
2. `npu-reference`: NPU-native PyTorch implementation and smoke benchmark added and run on physical NPU0.
3. `correctness-gate`: NPU-vs-reference routing parity passed for the smoke workload.
4. `ascend-profile`: script emits router latency/activation statistics; full CANN profiling remains next.
5. `framework-integration`: planned route to vLLM-Ascend fused MoE / CANN ops-transformer; no production code changed yet.
6. `end-to-end-decision`: pending full model/representative MoE integration.

## First NPU evidence

Physical NPU0 was live-checked free before the run. The first minimal container attempt failed during `aclInit` because only device nodes were mapped; the container could not obtain SoC information. Re-running with the same driver/DCMI bind mounts used by the known-good vLLM container succeeded. This is recorded as a migration-environment failure/recovery, not an algorithm failure.

Successful smoke configuration:

```text
device: physical NPU0 -> container npu:0
tokens: 4096
experts: 8
top_p: 0.4
correctness: PASS
mean activated experts: 1.75244140625
activation histogram: {1: 1228, 2: 2654, 3: 214}
dynamic router median: 362.805 us
fixed Top-2 router median: 175.645 us
```

Interpretation: the target device reproduces the paper's key adaptive-expert behavior on synthetic router distributions, but the dynamic selection operation is roughly 2x the fixed-Top2 router in this microbenchmark. The paper hypothesis is therefore not accepted yet: the next stage must test whether saved expert compute outweighs routing/dispatch overhead end to end.

## Concrete integration seams found

`vllm-ascend`:

```text
vllm_ascend/ops/fused_moe/router/router_factory.py
vllm_ascend/ops/fused_moe/router/grouped_topk_router.py
vllm_ascend/ops/fused_moe/router/fused_topk_router.py
vllm_ascend/device/device_op.py::moe_gating_top_k
```

`ops-transformer` CANN 9.1:

```text
moe/moe_gating_top_k*
moe/moe_init_routing_v2|v3
moe/moe_token_permute*
moe/moe_compute_expert_tokens
moe/moe_finalize_routing*
gmm/grouped_matmul*
mc2/moe_distribute_dispatch/combine* and grouped_mat_mul_allto_allv
```

The likely production representation is a bounded/padded `max_k` expert-id/weight tensor plus a per-token dynamic expert count (or equivalent mask). That keeps data-dependent K while preserving shapes usable by graph capture and grouped dispatch.

## Resume

```text
cd /opt/host/vnf/austinov/worktrees/exp-20260904-dynamic-moe-paper-to-ascend
git status --short --branch
cat .agents/experiments/exp-20260904-dynamic-moe-paper-to-ascend.yaml
npu-smi info
python -m unittest discover -s tests -p 'test_dynamic_moe_routing.py'
```

Before any new NPU run, prove NPU0-3 remain free in the same session.

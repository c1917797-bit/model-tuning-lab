# Paper-to-Ascend Pipeline

This is a reusable engineering pipeline for turning a research-paper implementation into an Ascend NPU experiment and, if evidence supports it, a production-framework change.

The first exemplar is **Dynamic MoE** from *Harder Tasks Need More Experts: Dynamic Routing in MoE Models*.

## Pipeline contract

```text
paper + upstream code
        |
        v
1. Paper Contract
   - algorithm invariant
   - tensor shapes
   - state/weights required
   - claimed metrics
   - implementation-specific assumptions
        |
        v
2. Migration Unit Classification
   router / kernel / graph / scheduler / distributed / serving
        |
        v
3. Ascend-Native Reference
   PyTorch + torch-npu is allowed directly on NPU
   CPU is optional, not a mandatory stage
        |
        v
4. Correctness Gate
   deterministic cases + upstream semantic parity + numerical/quality gates
        |
        v
5. Device Baseline + Profiling
   latency / throughput / HBM / utilization / CANN profiler
        |
        v
6. Hardware-Aware Lowering
   vllm-ascend / torch-npu / CANN / ops-transformer / TileLang / Triton / AscendC
        |
        v
7. Framework Integration
   production scheduler, fused MoE, HCCL/MC2, graph capture, serving API
        |
        v
8. Apples-to-Apples Decision
   accepted / rejected / inconclusive / failed
        |
        +----> evidence + next loop
```

## Dynamic MoE paper contract

The upstream inference code computes router logits, applies softmax, sorts expert probabilities in descending order, computes a cumulative sum, and keeps a **variable number of experts**: the smallest prefix whose cumulative probability reaches `top_p_threshold`.

This means the portable research idea is **not** the upstream Python loop. The portable unit is:

```text
router probability tensor [..., E]
        -> dynamic cumulative-mass selection
        -> variable expert ids/weights/counts per token
        -> weighted expert dispatch/aggregation
```

The upstream repository historically defaults `top_p_threshold` to `0.4`. Treat the threshold as an experiment variable, not a universal optimum.

## Why this paper is a useful exemplar

It forces the pipeline to cross several real last-mile boundaries:

1. **Algorithm migration:** fixed Top-K becomes variable K per token.
2. **Shape migration:** dispatch sizes become data dependent.
3. **Kernel migration:** sort/cumsum/mask and expert dispatch need efficient NPU execution.
4. **System migration:** dynamic K can change load balance and communication volume in TP/EP.
5. **Serving migration:** lower expert compute only matters if router/dispatch overhead does not erase the gain.

## Ascend implementation ladder

Do not jump directly to hand-written AscendC. Move down only when profiling requires it:

```text
torch-npu reference
  -> torch.compile / graph-friendly vectorization
  -> vllm-ascend integration seam
  -> existing CANN ops-transformer GMM/MoE/MC2 primitives
  -> TileLang/Triton/PyPTO prototype when a missing fused primitive is identified
  -> AscendC only for the final hot path when justified by profile evidence
```

## Dynamic MoE-specific migration risks

### Router cost

Dynamic top-p needs sort + cumulative sum instead of a fixed Top-K selection. The routing operation may cost more even when expert compute falls.

### Variable dispatch

Tokens no longer have a constant number of expert assignments. Efficient packing and grouped GEMM are therefore central to the production implementation.

### Load balance

Average experts can fall while individual experts become imbalanced. Always record per-expert token counts and max/mean load ratio.

### Communication

With expert parallelism, variable K changes all-to-all/dispatch volume. Measure HCCL/MC2 traffic rather than assuming fewer experts always means lower latency.

### Graph capture

Data-dependent expert counts can create graph-shape instability. Prefer bounded/padded representations or bucketed K/counts if full dynamic shapes block graph capture.

## Concrete last-mile map on this host

The source inspection on the checked-out `vllm-ascend` and CANN 9.1 `ops-transformer` trees identified the following path:

```text
paper top-p router
  -> vllm-ascend router abstraction
     ops/fused_moe/router/{router_factory,grouped_topk_router,fused_topk_router}.py
  -> DeviceOperator.moe_gating_top_k
  -> dynamic ids / weights / counts representation
  -> CANN routing and token permutation
     moe_gating_top_k*
     moe_init_routing_v2/v3
     moe_token_permute*
     moe_compute_expert_tokens
  -> grouped expert compute
     gmm/grouped_matmul*
  -> unpermute/finalize
     moe_token_unpermute*
     moe_finalize_routing*
  -> for EP/communication cases
     mc2/moe_distribute_* / grouped_mat_mul_allto_allv
```

The first production prototype should **not** make tensor rank dynamic. Use a fixed `max_k` width with `-1` expert ids / zero weights for inactive slots plus a per-token count or mask. This gives Dynamic MoE semantics while preserving a bounded representation that is easier to feed into graph capture, permutation and grouped matmul pipelines.

## First target-device result

The NPU-native router reference was run on physical Ascend 910B4 NPU0 with 4096 synthetic tokens and 8 experts at `top_p=0.4`:

```text
correctness: PASS
mean activated experts: 1.75244140625
counts: 1 expert=1228, 2 experts=2654, 3 experts=214
dynamic median router latency: 362.805 us
fixed Top-2 median router latency: 175.645 us
```

This is a **migration-unit verification**, not a paper performance reproduction. It proves the adaptive K semantics execute correctly on 910B4 and exposes the immediate hardware question: can reduced expert/GMM work recover the extra router/dispatch cost?

The first container attempt also failed with `aclInit` 507008 because only NPU device nodes were mounted. Matching the working vLLM container's DCMI/driver binds fixed initialization. The pipeline therefore treats container/runtime mapping as a formal environment gate before algorithm diagnosis.

## Evidence ladder

### Gate A — Routing semantics

- Minimal prefix crosses threshold.
- No expert after the crossing point is selected.
- At least one expert is selected.
- Selected weights are the router probabilities associated with selected ids.

### Gate B — NPU execution

- Run the reference directly on Ascend.
- Prove the intended physical NPU with `npu-smi` in the same session.
- Record device/kernel timing and activation-count distribution.

### Gate C — Fused MoE prototype

Replace only the routing/dispatch policy while keeping model weights, requests, dtype, parallelism and framework fixed.

### Gate D — Production integration

Benchmark fixed Top-2 vs dynamic routing with identical requests and repeated measurements. Report quality, throughput, TTFT/TPOT, HBM, CPU, NPU utilization, expert counts, load balance and communication.

## Reuse for another paper

For a new paper, keep the eight pipeline stages but replace the migration unit and gates. The first question is always:

> What is the smallest semantic unit introduced by the paper that must survive the hardware/framework translation?

For Dynamic MoE that unit is the **variable-expert routing policy**, not the original Python implementation.

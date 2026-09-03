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

## Whole-block A/B result on 910B4

The next gate ran a real Ascend-native MoE block on physical NPU0. Both sides used the same BF16 expert weights and per-repetition hidden/router inputs. The only policy change was fixed Top-2 versus Dynamic cumulative-mass routing at `top_p=0.4`. The block included compact token/expert dispatch, `npu_moe_init_routing_v2`, two `npu_grouped_matmul` calls with SwiGLU, unpermute, routing weights and token combine.

Five repetitions with 20 warmups and 100 measured iterations per side produced:

| Tokens | Fixed Top-2 median | Dynamic median | Dynamic latency change | Mean experts | Pair compute reduction |
|---:|---:|---:|---:|---:|---:|
| 128 | 957.07 us | 1776.36 us | **+85.60% slower** | 1.7297 | 13.52% |
| 512 | 960.32 us | 1818.12 us | **+89.33% slower** | 1.7375 | 13.13% |
| 2048 | 985.00 us | 1931.16 us | **+96.06% slower** | 1.7517 | 12.42% |
| 4096 | 1309.43 us | 2386.40 us | **+82.25% slower** | 1.7437 | 12.82% |

The regression was stable across repetition order. At 4096 tokens each repetition showed an 81.08% to 83.55% slowdown for the Dynamic path.

The 4096-token stage breakdown explains why:

| Stage | Fixed | Dynamic | Dynamic effect |
|---|---:|---:|---:|
| routing / pair selection | 218.465 us | 1389.640 us | **536.09% slower** |
| CANN dispatch/permute preparation | 290.870 us | 271.340 us | 6.71% faster |
| expert GMM + SwiGLU + GMM | 611.225 us | 557.140 us | **8.85% faster** |
| unpermute / weighted combine | 516.315 us | 508.800 us | 1.46% faster |

The important result is therefore not that Dynamic MoE's compute-saving idea is false. The device really performs less expert work and the expert GMM stage is measurably faster. The current **full sort + cumsum + boolean compaction lowering is the bottleneck**: routing grows from about 0.22 ms to 1.39 ms and overwhelms the ~9% GMM benefit.

This direct lowering is rejected for performance. The next implementation should preserve a bounded `max_k` representation and fuse or otherwise replace the expensive dynamic selection/compaction path before another whole-block A/B. Full-paper acceptance remains pending because the paper's real model checkpoint is not available locally and this host could not reach Hugging Face during the run.

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

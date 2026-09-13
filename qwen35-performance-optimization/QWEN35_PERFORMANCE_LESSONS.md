# Qwen3.5-27B performance lessons and takeover summary

## Canonical objective

Optimize Qwen3.5-27B BF16 TP4 on physical NPU0-3. Relative to a fresh,
same-environment control, reduce TTFT P95 by at least 20% and TPOT P95 by at
least 10% at concurrency 1, 5, 8, and 16, with three repetitions per cell,
zero request errors, natural EOS, and no accuracy regression. Deliver the
accepted stack as a removable runtime Python monkeypatch in the unchanged
official vLLM-Ascend v0.23.0 image. This objective is independent of
Paper-to-Ascend.

Upstream-first means: absorb upstream operators and engineering lessons,
never duplicate an existing wheel, then add and independently measure a
profile-grounded Qwen3.5-specific delta. Pure copying is not completion.

## Retained successes

| Result | Evidence | Durable lesson |
|---|---|---|
| T20 bounded-prefill c1/32: TTFT 6310.576 -> 808.224 ms, 87.193% reduction; TPOT 29.107 -> 28.282 ms, 2.835% reduction; 32/32, zero errors, natural EOS | /cache/austinov/qwen35-t20-candidate-prefill-20260911 | Retain as the TTFT component, not a final stack. |
| T32 upstream fused-GDN prefill c1/32: TTFT 841.073 -> 617.432 ms, 26.590% reduction; TPOT 28.909 -> 28.276 ms, 2.189% reduction; 32/32, zero errors, natural EOS | /cache/austinov/qwen35-fused-prefill-service-20260913-v3 | This is the current TTFT base; compose only with a separately proven decode treatment. |
| Historical T11 c1: TTFT reduction 47.7%, TPOT reduction 17.3% | Runtime monkeypatch manifest | It clears the corrected c1 thresholds, but lacks the current full matrix and quality proof. Reproduce before claiming. |
| T27 upstream SwiGLU MLP FLOAT smoke passed on NPU0 | /cache/austinov/qwen35-t21-upstream-float-smoke-20260912T163200Z | The minimal official six-argument ExecMmOp ABI adapter is viable. |
| T27 exact TP4 BF16 matrix passed 12/12 for M=1/5/8/16 x seeds 1/2/3 | /cache/austinov/qwen35-t21-bf16-numerical-20260912T163327Z | Every case was bit-exact against official Matmul -> SwiGLU -> Matmul; the operator may enter model integration but is not promoted. |
| T28 task-queue-safe public ACL bridge builds and imports without private vLLM-Ascend symbols | /cache/austinov/qwen35-t21-public-acl-bridge-20260912-v3 | Public ACL descriptors plus torch-npu `RunOpApiV2` preserve stream ordering and object lifetimes without the failed private-symbol seam. |
| T28 zero-copy model-layout gate passed three fresh 20/20 matrices plus 500-call stress per run | /cache/austinov/qwen35-t21-public-bridge-numerical-20260912-v4, -v5, -v7 | `.t()` views are bit-exact with contiguous candidate weights; the former intermittent NaN was eliminated by task-queue-aware scheduling and captured ownership. |
| T29 removed the artificial Python dynamic-M gate and rebuilt the public bridge | /cache/austinov/qwen35-t21-public-acl-bridge-20260912-v5; numerical -v8 and -v9 | Upstream documents positive flattened rows without an M ceiling. M=128/512/1024/4096 passed; Python M branching before fullgraph capture had frozen the official fallback. Bridge v5 also preserves symbolic M in its Meta output so AOT does not specialize a dynamic range to 32768. |
| Reproducible benchmark, accuracy, resource-lock, rollback, official-image, and evidence tooling exists | This workstream and external artifact roots | Infrastructure is part of the result; reuse it rather than creating ad-hoc tests. |

## Failed or rejected routes

| Route | Decision | Reuse rule |
|---|---|---|
| T17 current AIC GEMV | Closed for current implementation | Do not rerun unchanged. |
| T18 native NK vector variants | Candidate slower than stock in valid same-round comparisons | Do not continue blind BN/BK scans. |
| Dense FFN NZ layout | Isolated win but 0.992x geometric-mean incremental TPOT and E2E regressions | Keep rejected unless a materially different profile-grounded mechanism appears. |
| Built-in torch_npu.npu_ffn BF16 | Installed no-expert-tokens path accepts FP16 only | Precision casting is forbidden; do not retry on this runtime. |
| A3-only AttentionToFFN/FFNToAttention and dense-incompatible fine-grained TP | Hardware/topology contract mismatch | Hard reject for A2 TP4. |
| Old T12 GDN projection candidate | c1/32 improved TTFT only 12.38%, TPOT 0.36%, and only 16/32 response hashes matched | Loader/activation evidence only; not a quality-preserving performance result. |
| First T21 PyTorch bridge | Compiled, but load failed on private, non-exported vllm_ascend::NPUBridge symbol even with explicit vllm_ascend_C linkage | Do not copy or reimplement NPUBridge. Build the next bridge only from public ACL tensor APIs and the current torch-npu stream, or use an upstream public registration seam. |
| T21 public fused-MLP TP4 service | c1 TTFT improved only 7.51%, while TPOT regressed 144.3% against the paired fresh control | The operator's numerical gate is necessary but not sufficient; reject a correct local kernel when its complete projection/collective path regresses end to end. |
| T30 upstream MRV1 Super Kernel | All four workers activated the exact upstream backport, but CANN AclskOptimize failed with ACL 500001 during graph capture | Never swallow an optimization failure. Upstream provenance plus unit tests is not target-stack validation, and a service that never becomes ready produces no admissible performance or quality claim. |
| T31 bounded prefill MMAR rerun | After a separate 32-request warmup, c1 TTFT P95 was 850.068 ms and TPOT P95 was 31.342 ms versus fresh-control medians 841.073/28.909 ms; 32/32, zero errors, natural EOS | The historical 87% TTFT result was a cold-control artifact. Compare steady state on one live service and reject this component before the full matrix. |
| T33 zero-copy M=1 QKV views | Warmed c1 TTFT passed at 609.652 ms, but TPOT regressed 2.147% to 29.530 ms/token | Sub-one-percent layout/copy work is not the retained stack's TPOT bottleneck. Do not compose or rerun unchanged. |
| T35 upstream-derived GDN conv-weight prepack | Warmed c1 TTFT passed at 619.023 ms and TPOT improved 5.477% to 27.326 ms/token, but TPOT missed the 26.018 ms gate | The upstream KDA prepack idea is sound but too small alone. Do not rerun unchanged; target the complete profile-proven GDN preprocessing-to-recurrent chain. |

## Decisions changed by the corrected target

Do not mechanically carry forward rejections that depended only on the old
40% TTFT / 20% TPOT threshold.

- T11 is now performance-admissible at c1, but still lacks current matrix and
  accuracy evidence.
- T34 remeasured the T19 GDN terminal envelope on the retained stack at a
  3.108 ms/token zero-cost upper bound. The current c1 gap is 2.2583 ms/token,
  so this route would have to realize about 72.7 percent of the whole envelope.
  The existing fused AddRMSNorm path already regressed end to end; only a
  materially different, numerically gated boundary may reopen it.
- Compatibility, accuracy, hardware, and measured-regression failures remain
  closed regardless of the lower target.

## Upstream adoption lessons

1. Pin source commits and audit why experimental code is not in the stable
   runtime. Upstream origin is not a quality waiver.
2. Prefer the upstream implementation and write only the missing model/runtime
   delta. Use an ablation with official control, upstream base, and upstream
   base plus project delta.
3. The T27 installed public header omits aclnn_util.h. The FLOAT example needs
   the upstream source helper include directory read-only; the BF16 gate
   declares only the already-exported C ABI.
4. The upstream fused MLP does not include TP AllReduce or a vLLM PyTorch
   binding. The project delta must preserve the supported TP collective and
   rollback path.
5. Avoid private vLLM-Ascend C++ symbols. A bridge that compiles but cannot
   load is failed integration, not device evidence.

## Device and evidence lessons

- The operator authorizes a run when physical NPU0-3 have no actual NPU
  processes and the cooperative lease is held. Idle privileged or
  device-declaring containers alone do not block. Recheck immediately after
  acquiring the lock.
- Never touch NPU4-7. Use one-shot owned containers, network disabled,
  read-only source/OPP mounts, exact identity cleanup, and before/after
  npu-smi snapshots.
- Separate cold compilation, warm steady state, boundary concurrency,
  lifecycle, and resource evidence.
- A faster output is not accepted until paired quality passes. The
  query_rewrite set is a latency workload, not reference-backed accuracy;
  final quality additionally uses the frozen GSM8K gate.

## Immediate resume point

1. Keep the fresh v14 control matrix as the only current acceptance reference.
2. Keep bounded-prefill MMAR rejected: its warm c1 fail-fast missed both current
   gates. Do not rerun it unchanged or use its historical cold-control result.
3. Keep the zero-copy M=1 QKV view candidate rejected: it retained a 27.515%
   TTFT reduction but regressed TPOT by 2.147% after a separate same-service
   warmup. Do not rerun or compose this exact implementation unchanged.
4. Keep T35 conv-weight prepack rejected as a standalone component. Its formal
   c1 retained the TTFT pass but reached only a 5.477% TPOT reduction.
5. Continue the post-v0.23 upstream audit for a Qwen3.5/910B full GDN decode
   chain or materially different collective boundary. T34 measures only
   0.63456 ms/token in transpose but 2.796 ms/token in the complete
   transpose-to-recurrent envelope. The next candidate must contain an
   upstream-derived base plus a measurable project-specific whole-chain delta.
   Only a passing c1 fail-fast result may enter c1/c5/c8/c16 x3 and the full
   paired quality gate.

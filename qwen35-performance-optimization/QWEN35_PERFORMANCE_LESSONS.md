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

## Decisions changed by the corrected target

Do not mechanically carry forward rejections that depended only on the old
40% TTFT / 20% TPOT threshold.

- T11 is now performance-admissible at c1, but still lacks current matrix and
  accuracy evidence.
- T19 measured a theoretical maximum of about 3.048 ms/token for the GDN
  terminal interval. That was insufficient for the old roughly 6.10 ms/token
  gap. The corrected c1 TPOT target from the T20 control needs roughly
  2.91 ms/token. Recalculate overlap and realizable savings before deciding
  whether T19 can contribute to a stack; the theoretical interval is not an
  achieved speedup.
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

1. Keep T20 bounded-prefill as the TTFT component.
2. Start the no-dynamic-M `candidate-prefill-t21` TP4 service and require four-rank
   activation, natural EOS, and clean rollback.
3. Run fail-fast official/upstream-base/project-delta ablation. Only then run
   c1/c5/c8/c16 x3 and full paired quality.

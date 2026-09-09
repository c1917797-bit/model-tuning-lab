# Qwen3.5 t13 candidate plan

This note narrows the next optimization step after the t12 standalone runtime
patch failed the current performance gate. It is intentionally evidence-scoped:
it does not promote t12 and it does not authorize touching the official
vLLM-Ascend 0.23.0 image or host source tree.

## Current target

- Model/framework: Qwen3.5-27B on vLLM-Ascend 0.23.0.
- Hardware scope: Ascend 910B4, tensor parallel size 4, physical NPU0-3 only.
- Protection: physical NPU4-7 must never be used or stopped by this workstream.
- Delivery form: standalone runtime patch/plugin loaded by read-only mount plus
  Python path mechanics inside a disposable container.
- Acceptance: each of c1/c5/c8/c16 must reduce TTFT P95 by at least 40% and
  TPOT P95 by at least 20%, with zero material quality regressions.

## What t12 proved and did not prove

t12 proved that the standalone loader shape is viable:

- official vLLM-Ascend 0.23.0 image identity was preserved;
- the patch was mounted read-only and injected without source overlays;
- activation markers were observed in four TP workers on physical NPU0-3;
- fixed-input smoke completed with natural EOS and matched the control hash.

t12 did not prove the performance or quality target:

- c1/32 TTFT P95 moved from 6502.636 ms to 5697.694 ms, only 12.38% lower;
- c1/32 TPOT P95 moved from 31.754 ms to 31.641 ms, only 0.36% lower;
- only 16/32 response hashes matched the paired control run, so t12 cannot be
  promoted as precision-lossless without deeper paired review.

## Closed routes that should not be repeated

- Simple decode MMAR decomposition into ordinary matmul plus all-reduce: the
  official fused MMAR path is already about 2x faster for the real M=1 shapes.
- Blind MMAR launch-parameter retuning: timeline evidence shows decode M=1
  cross-rank start spread is already small.
- Ascend 950/dav-3510 APACE or AIV+URMA MC2 assumptions: the CANNBot MC2
  capability table does not register this as a supported direct route for
  Ascend 910B4/dav-2201 collective-comm kernels.
- Previously rejected variants: down-proj NZ, online HCCL tiling, K4352-only
  tiling, HCCL_BUFFSIZE variants, MMAR x3 residual, ShortGPT layer skip, and
  broad bounded-MMAR t11 promotion.

## t13 hypothesis

The remaining gap is probably not a single faster decode GEMV/MMAR primitive.
Existing profile evidence points to lifecycle and scheduling effects around
prefill and collective arrival: prefill shapes showed millisecond-scale rank
start skew while decode M=1 MMAR launches were already closely aligned.

t13 should therefore start as a narrow diagnostic runtime patch before any new
operator is generated:

1. Instrument the Qwen3.5 request path at privacy-safe boundaries to separate
   prefill, decode, graph compile/capture, first-token scheduling, and per-token
   collective wall time.
2. Add shape/range counters for GDN projection fusion, MMAR, RMSNorm, and
   prefetch hooks so E2E gains can be attributed to the exact code path.
3. Re-profile one fresh control and one candidate on c1/c16 fail-fast only,
   using the same resource gate and cache-salt protocol as t12.
4. Only if attribution identifies a causal bottleneck, implement the smallest
   runtime hook or OPP-backed call-site change that preserves mathematical
   equivalence.

## Operator-generation policy

Use `/cache/cch/cannbot-skills` and `/cache/cch/ops-transformer` as references,
not as carte blanche to create a new collective operator. A new operator is
allowed only after a requirements note proves all of the following:

- the chip route is supported for Ascend 910B4/dav-2201, or the unsupported
  status is explicitly accepted as an experimental route;
- the op has a precision oracle with BF16 inputs and expected tolerances;
- the benchmark uses L2 flush and multi-rank max latency, not optimistic average
  timing;
- the runtime loader can mount the resulting OPP read-only without modifying the
  base image;
- c1/c16 fail-fast beats both TTFT and TPOT gates before full-matrix testing.

## PR policy

Do not push a final performance PR until the validation artifacts prove the
current target. It is acceptable to push a packaging or diagnostic PR only if
the PR title and body state its exact evidence boundary and explicitly say that
it is not the final money patch.

The absence of host `unittest` and GitHub CLI is not a blocker:

- tests must be runnable with shell scripts or direct Python assertions;
- branches can be pushed with `git`, and PRs can be opened from GitHub compare
  URLs or API calls.


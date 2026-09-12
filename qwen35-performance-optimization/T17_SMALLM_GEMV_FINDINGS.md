# Small-M AIC GEMV: runtime fix, numerical pass, performance rejection

Date: 2026-09-11. Branch-local record; no final promotion, commit, or push.

## Decision

The exact current AIC GEMV implementation is rejected before service
integration. Its runtime packaging error is fixed, and deterministic dense
operator correctness passes, but the affected-projection opportunity budget
is negative in both A/B orders. Do not rerun its full TP4/E2E matrix unchanged.
This does not reject every GEMV or weight-layout method.

External evidence root:
`/cache/austinov/qwen35-smallm-gemv-debug-r3-20260911`.

Authoritative derived decision: `CONFIRMED_DECISION.json`, SHA256
`221533fc6648db0ba206ca6d540d9c1d703c108038c5288ba4282a2a8c75241d`.

## Proven root cause of all-zero output

The preceding experimental package accidentally included the locally built
`common/stub/op_api/opapi_stub.cpp` implementation as `libopapi_math.so`.
Its `ViewCopy` returns the input without copying to the destination. Its
`Contiguous` implementation is also only a placeholder. Satisfying the dynamic
linker with that library is not runtime validation.

The build-stub SHA256 is
`dbcf3ec4a5dc360d520f74556d0c591fce0183ad7c29fee5dc95cd3db366e937`.
The correct pinned image's real math library is
`/usr/local/Ascend/cann-9.1.0/aarch64-linux/lib64/libopapi_math.so`, SHA256
`f9868c0ecdcd35c38adc44e0653463cc8d97a1a171edd4af855b3250c1c82958`.

Controlled proof sequence:

1. Replace GEMV with clean-built original MatMul while keeping host/runtime
   plumbing unchanged: full-chain output remained zero (`ab-canary`).
2. Profile that failure: actual BF16 keys 3101/3102/3103 all executed with
   expected shapes (`ab-msprof`). Kernel absence was not the explanation.
3. Independent external stage outputs and a three-stage external-buffer chain
   passed for both original MatMul (`ab-stages-v6`) and GEMV (`gemv-stages-v6`).
4. Copy the original GEMV bundle into a new root and remove ONLY the bundled
   build stub. Verify real-image library resolution with `ldd -r`. The
   unchanged full-chain harness then produced 0.73046875, the BF16-rounded
   expected result, with one nonzero output (`gemv-fullchain-runtime-fixed`).

The original GEMV object remains SHA256
`bbaba426d886e8265ee60129d6057847167708b4c5fc704bade546a21bdc5eea`.
The custom host API remains SHA256
`9a4eaaf6bfe7ef36b8909ec67e429fea18b7884eb30d7217a89a9284d89b5161`.
No GEMV arithmetic change was necessary for this fix.

`scripts/check_qwen35_opp_runtime_bundle.py` now rejects bundled CANN runtime
shadows and the known build stub. Its scope is packaging only: still require
real-image `ldd -r`, physical numerical tests, and performance/quality gates.

## Numerical evidence

Each executable/round ran eight shapes with two seeds, 16 cases and 58,400
checked elements. All outputs were finite and bit-identical to the host
double-accumulated, BF16-RNE reference in both execution orders.

Shapes: M=1 with (K,N)=(5120,8704), (5120,4096), (5120,3584), (4352,5120),
and tail (160,272); M=5/8/16 with (K,N)=(128,256).
Inputs were deterministic dense exactly representable binary fractions.
This is bounded numerical evidence, not a general floating-point proof or
the required all-357 paired model-quality gate. Only a sparse canary covers
the complete self-stage FFN API at this point.

## Repeated performance screen

Physical NPU0 only, BF16, pinned official image. System MatMul and custom
direct-stage GEMV execute in separate processes, without `libcust_opapi.so`
being co-loaded into the measurement harness. Timed intervals are device
events around phase-2 execution. Every cold-weight sample follows a separate
512 MiB weight-reading system MatMul and stream synchronization. This is an
explicit weight-eviction protocol, not a proof of full-model cache equivalence.

Each shape/cache regime has five repeats of 20 samples, plus warmup. Round 1
ran system then candidate; round 2 reversed order and retained all 1,600 raw
event samples. Values below are median-of-five per-repeat medians in us,
NOT E2E P95 measurements.

| K x N | Round 1 system / GEMV | Round 2 system / GEMV | Conclusion |
|---|---:|---:|---|
| 5120 x 8704 gate-up | 134.580 / 167.770 | 133.990 / 165.260 | Regresses 23.3–24.7% |
| 5120 x 4096 qkvz | 60.000 / 77.270 | 60.750 / 77.200 | Regresses 27.1–28.8% |
| 5120 x 3584 attention projection | 58.690 / 63.480 | 58.170 / 58.040 | Shape-local result is not repeatable |
| 4352 x 5120 plain down MatMul | 67.720 / 76.180 | 67.440 / 77.020 | Regresses 12.5–14.2%; not MMAR |

Including the attention shape's small round-2 gain, the 64 gate-up, 48 qkvz,
and 16 attention-projection call-count translation is -3.030 and -2.789
ms/token of hypothetical savings. Negative means projected additional cost,
not an improvement. This is only an operator-to-model estimate; no actual
model regression measurement is claimed. Never count plain down MatMul as
replacing MMAR or sum overlapping AICPU envelopes.

## Reusable maintenance lessons

- Kernel compilation and dynamic symbol resolution alone do not establish
  runtime correctness. Never ship common/stub output as a runtime library.
- A failed full-chain canary need not implicate GEMV arithmetic. Expose stage
  outputs before changing the kernel.
- A direct L0 test still requires proper L2 context initialization. Omitting
  L2_DFX_PHASE_1/2 produced zero platform core counts and tiling error 561000.
- msprof can return zero after exporting an application that exited nonzero.
  `ab-msprof/result.json` contains the old misleading wrapper-success label;
  `PROFILE_STATUS_CORRECTION.md` explicitly corrects it to numerical FAIL.
  The runner now checks numerical markers, not just profiler exit status.
- Incremental target success may leave staged kernel headers unchanged.
  Prove source staging and a changed object digest for an A/B kernel change.
- AWMCP transport timeout is ambiguous execution status. Inspect artifacts
  and exact owned containers before retrying; a command continued remotely
  after a timeout in this round. Never restart unrelated jobs to recover it.
- Keep hot-only wins separate. The N=3584 hot gain did not establish a
  repeatable cold-weight or meaningful full-model opportunity.
- A shell brace group used with `||` can suppress errexit inside the group.
  A first validation wrapper printed PASS after the host's trimmed Python
  could not import unittest. Preserve `final-validation.log` as a failed
  aggregate attempt; `VALIDATION_STATUS_CORRECTION.md` documents the correction.
  The strict validator now checks every subprocess return code explicitly.
  Its `strict-validation.json` reports all ten checks passed, including eight
  packaging fixtures run in the pinned image with no network or NPU devices,
  MST (18 skills), P95/quality-checker contract tests, syntax and diff checks.
  Checker tests passing is not model performance or model quality passing.
- The TLA class name does not itself prove a hardware M=1 MMAD instruction:
  this AIC block passes the vector helper's aligned M dimension to TileMmad.
  Future mechanisms require actual data-path evidence, not naming alone.

## Reproducibility and takeover

Operator worktree:
`/cache/austinov/worktrees/exp-20260911-qwen35-smallm-gemv`,
base `0684247214bae5abb5cb6dc7d90b34a6ad401cdd`.
Its source currently retains the GEMV-disabled A/B guard (`false && M==1`).
The fixed runtime bundle retains the ORIGINAL enabled GEMV binary. Do not
confuse the source state with runtime binary identity or release either as-is.

The working diagnostic bundle is `gemv-runtime-fixed-opp` under the evidence
root. It is still assembled from a legacy OPP scaffold, not a production
release. Do not source its inherited legacy set_env script; the guarded
runner sets exact mount-relative paths explicitly. Final packaging must be
rebuilt coherently and include no stale paths, stubs, or rejected components.

Read `CONTRACT.md`, `DENSE_PERF_CONTRACT.md`, `CONFIRMED_DECISION.json` and
the raw `dense-*-screen-v2/container.log` files. `run_probe.py` captures
resource checks, binary/source snapshots, exact commands, logs, and cleanup.
`summarize_screen.py` verifies all raw round-2 timing statistics.

Next: retain T16 as the TTFT component; do not integrate this AIC GEMV
implementation. Admit a materially different weight-read/layout path only
after quantifying a credible decode opportunity against the exact T16 profile.
Do not reopen MMAR lifecycle-only accounting or optimize padded arithmetic
alone when the relevant profile is dominated by MTE2. AIV/prepacked-layout
options remain hypotheses, not implemented or admitted performance candidates.

All resource statements are snapshots, not reservations. Re-prove physical
devices and live declarations and hold the complete-lifetime lease before any
new experiment. NPU4-7 remained excluded. Validation precedes commit/push.

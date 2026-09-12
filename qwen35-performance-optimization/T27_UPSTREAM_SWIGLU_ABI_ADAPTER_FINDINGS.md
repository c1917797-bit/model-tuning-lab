# T27 upstream SwiGLU MLP ABI adapter findings

## Decision

`ABI integration PASS; device and promotion gates OPEN`.

The original ops-transformer v9.1 package could not resolve its private
four-argument `ExecMmOp` declaration in the official vLLM-Ascend v0.23.0 /
CANN 9.1.0 image. The current isolated candidate fixes only that adapter seam:

- official source baseline:
  `c77c0829f1f0f0b8f882db1d9b051a758b605472`;
- isolated worktree:
  `/cache/austinov/worktrees/exp-20260911-qwen35-t21-abi-adapter`;
- official ABI used:
  `ExecMmOp(self, mat2, out, cubeMathType, executor, isFusion)`;
- `isFusion=true`, matching composition inside a single ACLNN executor;
- MM1 and MM2 output tensors are allocated explicitly, as required by that
  ABI;
- upstream matmul, SwiGLU kernel, dtype behavior, and formula remain in use;
- `libopapi.so` is linked explicitly so the install-time validator sees a
  self-contained dependency graph.

The final and installed `libcust_opapi.so` SHA-256 is
`ef99d0382ead18f4ef565fb62b40e679adaa9ee120af56089989430fa5a38afb`.
It passes `ldd -r` without preload and normal installer validation.

The reproducible runner
`scripts/run_qwen35_t21_upstream_float_smoke_npu0.sh` pins the unchanged
official image, holds the NPU0-3 lease, rejects conflicting processes and
containers, disables networking, mounts the OPP read-only, exposes only
physical NPU0, and records provenance plus before/after device snapshots.
`bash -n`, repository `diff --check`, its actual `npu-smi` parser, and
static device-isolation checks pass.

No candidate kernel has run yet. Three guarded attempts stopped before Docker
launch because another cooperative task held NPU0-3; two used a bounded
45-second wait. Four `VLLMWorker_TP` processes appeared on physical NPU0-3
during those intervals. No workload was interrupted.

This is not a numerical or operator failure. Retry the guarded runner after a
fresh idle check. A passing FLOAT smoke must be followed by exact Qwen3.5-27B
TP4 BF16 comparison against the official unfused
MatMul -> SwiGLU -> MatMul chain for M=1/5/8/16 and multiple seeds.

Do not load this OPP into the service or runtime monkeypatch yet. A FLOAT smoke
cannot prove BF16 accuracy, exact-shape support, stress behavior, dense-tail
economics, TP collective composition, or end-to-end quality.

## BF16 gate implementation

`tools/qwen35_t21_bf16_numerical_gate.cpp` now implements the next
same-device check at the exact TP4-local dimensions
`5120 -> 8704 -> 4352 -> 5120` and admits only M=1/5/8/16. Candidate output
uses `aclnnSwigluGatedMlp`; reference output uses only the official CANN
`aclnnMatmul -> aclnnSwiGlu -> aclnnMatmul` chain. Deterministic BF16 inputs
and weights, finite-output checks, maximum absolute error, relative L2 error,
and exact-BF16 fraction are reported as one JSON record.

The installed upstream public header references an `aclnn_util.h` file that
the package does not install. The gate declares the two exported C ABI
functions directly instead of copying a build-only helper header into the OPP.
This packaging defect is separate from runtime numerical behavior.

The gate compiles warning-free with `-Wall -Wextra -Werror` in a no-network,
no-device official-image container. `ldd -r` resolves the candidate and
official `libopapi`, `libnnopbase`, and `libascendcl` dependencies. This
is compile/link evidence only; no BF16 numerical result exists while the
privileged external container blocks safe NPU admission.

The shape contract is also verified against
`/cache/austinov/Qwen3.8-27B/config.json`: despite the directory label, the
file declares `model_type=qwen3_5`, `text_config.dtype=bfloat16`,
`hidden_size=5120`, and global `intermediate_size=17408`. TP4 therefore
uses local intermediate 4352 and local fused gate/up 8704. The runner checks
these fields before acquiring a device and records the config SHA-256.

The upstream tree contains BF16 kernel-test source, but the frozen build has no
generated SwiGLU MLP ctest target or executable. Its test shapes do not include
the exact 5120/8704/4352 model dimensions. Those sources are useful provenance,
not a substitute for the new same-device matrix.

`scripts/run_qwen35_t21_bf16_numerical_npu0.sh` now compiles the gate once
and runs M=1/5/8/16 across seeds 1/2/3 in a single guarded, one-shot container.
It checks result counts and requires all twelve JSON records to pass. Syntax,
invalid-input rejection, model-config validation, dependency contract, and
live fail-closed rejection of the external privileged container pass.

## Operator-approved admission policy update

The operator subsequently authorized device tests whenever the cards have no
actual NPU process, regardless of idle container device declarations or
privileged mode. Both guarded runners now enforce the cooperative lease and an
immediate `npu-smi` process check on physical NPU0-3, but do not reject an
otherwise idle declared container. Container state remains captured in the
evidence bundle. The test container still exposes physical NPU0 only.

## Device gate result and corrected delivery target

- The upstream FLOAT example passed on physical NPU0. Evidence:
  /cache/austinov/qwen35-t21-upstream-float-smoke-20260912T163200Z.
  The installed public header omits aclnn_util.h; the smoke compiler used the
  upstream source helper include directory read-only. No operator math or
  kernel code changed.
- The exact TP4 BF16 matrix passed 12/12 cases for M=1/5/8/16 and seeds
  1/2/3. Every case had zero non-finite values, zero max absolute and
  relative-L2 error, and exact BF16 fraction 1 against official
  Matmul -> SwiGLU -> Matmul. Evidence:
  /cache/austinov/qwen35-t21-bf16-numerical-20260912T163327Z.
- The project target is TTFT P95 >=20% and TPOT P95 >=10% improvement at
  c1/c5/c8/c16 with three repetitions, delivered as a removable runtime
  Python monkeypatch. This task is independent of Paper-to-Ascend.
- Upstream is the foundation, not the whole project result. Do not rewrite
  its fused operator; add and independently measure a profile-grounded
  Qwen3.5-27B-specific integration, layout/lifecycle, scheduling,
  communication, or fusion-composition delta behind the monkeypatch boundary.
- Operator numerical admission is complete. Model integration, stress,
  rollback, paired end-to-end quality, and the complete performance matrix
  remain open.

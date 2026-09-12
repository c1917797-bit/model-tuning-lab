# T21 upstream experimental quality gate

## Candidate boundary

The upstream source baseline is the CANN-matched ops-transformer `v9.1.0` tag
at `c77c0829f1f0f0b8f882db1d9b051a758b605472`, not default-branch HEAD.
The initial unchanged build exposed an internal matmul ABI mismatch. The
current device-admission candidate is a minimal adapter on top of that exact
operator: it supplies the output tensors required by the official CANN 9.1
six-argument `Ops::NN::ExecMmOp` ABI and links the already-required official
`libopapi.so`. It does not replace either matmul, the SwiGLU kernel, or their
BF16 semantics.

The resulting package is:

- `build_out/cann-ops-transformer-qwen35_t21_v910_linux-aarch64.run`
- SHA-256
  `3a1cdc8b209f5e4963990038fa0c825913a19edc633371830fe9b8ecccc513c1`
- one 83,888-byte `libcust_opapi.so`
- no generic `libopapi_math.so`

Pinned upstream build dependencies are ops-transformer
`c77c0829f1f0f0b8f882db1d9b051a758b605472`, opbase
`cd48c600c4b37146f504217eab2bf3956f7fee8b`, ops-tensor
`b24535e30a6f7a3909c53c8b09713a9c0d08e54b`, and cann-cmake
`7e5691ce110367662017d9d94114845a7d6a8d8a`.

The separately built default-branch artifact at
`d967eeb08ceef7c394d0d5e27767e5b08b77aa58` identifies itself as
ops-transformer 9.2.0. It is retained only as research evidence and is rejected
for CANN 9.1.0 device admission.

This provenance does not establish production quality. The operator is
explicitly experimental and no accepted vLLM-Ascend integration was found in
the audited upstream tree. Therefore it is not a final optimization and must
not be loaded into a service until the gates below pass.

## Required non-promotion audit

Before device admission, record:

1. the folder's commit history and author-provided tests;
2. stable-release and hardware/model support status;
3. related vLLM-Ascend issues, pull requests, reviews, and release notes;
4. whether lack of integration is caused by correctness, shape coverage,
   performance, ABI, lifecycle, or simply missing adapter work.

An unknown reason remains a blocking risk for promotion, even if a microbench
looks favorable. It does not authorize filling the gap with a parallel
reimplementation.

## Audit findings

- The operator entered ops-transformer through contribution MR `!6133`,
  related issue `#2576`, at commit
  `1e3925ea8c153e9a5b3138e376f45d545c143f99`.
- The contribution classified itself as a new feature, not a performance
  optimization. Its recorded validation was the single-operator build command;
  it did not provide Qwen3.5 end-to-end latency, numerical-regression,
  repeated-shape stress, or vLLM-Ascend integration evidence.
- The tag contains unit sources for kernel, infer-shape, and tiling plus a C++
  ACLNN example. Their presence is reusable upstream evidence, but no executed
  test result for this exact image, device, model shape, or workload has yet
  been established.
- The current audited vLLM-Ascend tree has no
  `SwigluGatedMlp`/`swiglu_gated_mlp` adapter, accepted integration commit,
  or release-note entry.
- No explicit upstream rejection or maintainer explanation for that missing
  integration was found. Therefore the reason must remain `unknown`; likely
  explanations such as missing adapter work, insufficient shape/performance
  evidence, ABI/lifecycle concerns, or correctness coverage are hypotheses,
  not facts.
- The exact packaged `libcust_opapi.so` fails `ldd -r` in the official
  CANN 9.1.0 runtime because
  `Ops::NN::ExecMmOp(const aclTensor*, const aclTensor*, int8_t,
  aclOpExecutor*)` is unresolved. The library declares
  `libopapi_math.so` as a dependency, but the official CANN 9.1.0
  `libopapi_math.so` does not export that internal symbol. The uninstalled
  33,568-byte build-tree library does not define it either.
- Consequently, the unchanged upstream C++ example cannot link against the
  package in the official image. Adding local matmul code or copying an
  unrelated private implementation would conceal an upstream integration/ABI
  defect and is forbidden by the upstream-first rule.
- A later ABI audit found the official CANN 9.1 `ExecMmOp` export with
  explicit output-tensor and `isFusion` parameters. The isolated adapter
  worktree
  `/cache/austinov/worktrees/exp-20260911-qwen35-t21-abi-adapter` now calls
  that exact ABI and allocates only the output tensors the ABI requires.
- The final adapted `libcust_opapi.so` has SHA-256
  `ef99d0382ead18f4ef565fb62b40e679adaa9ee120af56089989430fa5a38afb`.
  It declares `libopapi.so`, passes `ldd -r` without preload, and the normal
  installer accepted it into
  `/cache/austinov/qwen35-t21-abi-adapter-opp-r2-20260911`. The installed
  library has the same hash.
- This resolves the original link-time ABI blocker only. It does not establish
  device execution, numerical equivalence, useful speedup, stress safety, or
  vLLM-Ascend integration quality.

The practical consequence is asymmetric: upstream code may be reused for a
controlled experiment, but it cannot inherit a production-quality label from
its repository location. Promotion requires our local gates to cover every
unresolved risk dimension and must remain reversible.

## Admission gates

1. Use exact Qwen3.5-27B TP4 BF16 layouts: input width 5120, local
   intermediate width 4352, fused gate/up width 8704, output width 5120.
2. Prove gate/up ordering and weight-layout conversion without per-token weight
   copies.
3. Compare against the official unfused NPU path on the same device and inputs;
   require finite outputs and a documented BF16 error bound.
4. Require the dense-tail speedup needed by the measured end-to-end TPOT gap;
   a statistically weak or shape-limited win is rejection, not promotion.
5. Run alternating-shape repeated-call stress and verify no drift, leak, hang,
   or cross-rank divergence.
6. Only then compose the operator with the existing upstream TP collective
   through a removable runtime monkeypatch. Do not reimplement either
   computation or collective.
7. Run smoke, fail-fast, all-357 paired quality, and c1/c5/c8/c16 x3 final
   gates. Any failure restores the official path.

## Current decision

`ADMIT ABI adapter to FLOAT device smoke only; no promotion`.

The reproducible guarded runner is
`scripts/run_qwen35_t21_upstream_float_smoke_npu0.sh`. It pins the unchanged
official image, maps only physical NPU0, mounts the candidate OPP read-only,
disables networking, holds the cooperative NPU0-3 lease for the whole run, and
captures provenance plus before/after device snapshots.

Three device attempts stopped before container launch because another TP4
workload held the cooperative lease; two bounded retries waited 45 seconds
each. During the contention, four `VLLMWorker_TP` processes were visible on
physical NPU0-3. This is a resource-admission result, not an operator failure.
The candidate remains excluded from the runtime monkeypatch and from all
end-to-end claims until every admission gate passes.

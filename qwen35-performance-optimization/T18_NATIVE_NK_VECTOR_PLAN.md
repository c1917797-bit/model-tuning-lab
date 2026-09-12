# T18 native-NK vector reduction: historical admission plan

Current status (2026-09-11): device screen completed, numerical canary passed,
tested configuration family not promoted on performance. Read
`T18_NATIVE_NK_VECTOR_FINDINGS.md` and the newest branch-local HANDOFF section.
The resource-blocked observations below are historical, not a live blocker.

Date: 2026-09-11. No final performance or model-quality claim.

## Admission and scope

The T17 AIC GEMV implementation remains closed. Its two opposite-order
cold-weight screens both had a negative affected-projection opportunity
budget. Do not reopen that exact implementation based on hot-cache gains.

Fresh source/profile inspection shows a material layout difference: the exact
T16 MatMulV2 projections consume ND weights [N,K], whereas the closed AIC
GEMV screen consumed [K,N] interpreted as column-major. The pinned image's
`vllm_ascend/ops/linear.py:53-58` implements unquantized_gemm using F.linear;
`AscendUnquantizedLinearMethod.apply` forwards the original layer weight.

Rank0 exact T16 operator observations (diagnostic, not new measurements):

| Weight NK | Calls in capture | Mean duration |
|---|---:|---:|
| 8704 x 5120, gate-up | 6720 | 133.444 us |
| 4096 x 5120, GDN qkvz | 5040 | 63.428 us |
| 3584 x 5120, full-attention projection | 1680 | 58.732 us |

Source path, digest and summaries are in the external
`NK_PROFILE_PROVENANCE.json`. T18's distinct primary variable is native-NK
row-wise BF16 vector loading and FP32 reduction through Triton-Ascend, not a
cube GEMV or an additional weight-transpose operation. The F.linear NK and
torch.mm KN controls use the same logical matrix to expose layout effects.

An optimistic halving of the approximately 12.52 ms/token exclusive projection
budget would save approximately 6.26 ms/token, comparable to the remaining
6.1 ms gap. This is a hypothesis requiring measurement, not demonstrated
bandwidth or E2E gain. Do not count plain down-MatMul as fused-MMAR savings.

## Bounded implementation and checks

External source/evidence root:
`/cache/austinov/qwen35-t18-nk-vector-20260911-01`.

- `nk_probe.py`: gate-up [1,5120] and [8704,5120], BN1/4/8 only; CPU FP64
  oracle from BF16 inputs; finite and tolerance check before timing.
- `run_probe.py`: full-lifetime cooperative NPU0-3 lock, physical-device
  reservation checks, only physical NPU0 mounted, >=48 GiB ordinary available
  memory, 600-second deadline and exact-owner cleanup. No custom OPP or
  build-only runtime libraries are loaded.
- `test_offline.py`: seven device-free tests passed in the pinned official
  image with no network and no NPU device mounts. This is not kernel accuracy.
- Hot and 512 MiB distinct-weight-read eviction timings are separate; three
  repeats of twenty event samples in alternating orders are retained.
  NPUGraph/eager mode is explicit, and graph failure must not become a mixed
  comparison. Any positive initial screen requires expanded accuracy and
  actual-shape/multi-rank evidence before T16 service integration.

## Current blockers and exact interpretation

The guarded NPU attempt stopped before creating our test container because
`/vllm-ep-profile-ep4-910b` actively reserved physical NPU0-3. At the subsequent
08:51:34 UTC snapshot, that owner's `/vllm-ep-profile-tp4-910b` container was
running with physical NPU0-3 declarations. NPU4-7 belong to the external DRRQR
workstream. Empty process telemetry does not override a live reservation.
No external container was stopped, replaced or modified.

The no-device compile-only attempt failed before compiling any candidate:
the pinned compiler's triton_key() imports cv_autotune, which queries the
current NPU and fails with aclInit/SoC code 507008 without device mounts.
Explicit GPUTarget/arch and TRITON_COMPILE_ONLY did not remove that dependency.
BN4/BN8 import KeyErrors are secondary to partial initialization, not separate
kernel failures. No compiled-binary or device-correctness PASS is claimed.

Status authority: external `STATUS.json`, SHA256
`6b4b5fb840a1bdbcfe99dd9db5a32bed262427d05697eaf8bcc453a9765017c2`.
The external HANDOFF contains a guarded resume command with a fresh output
root. Re-prove availability before launch; do not rerun the offline failure
unchanged, borrow physical NPU4-7, or bypass the reservation gate.

## Delivery boundary

Only diagnostic source and branch-local notes exist. No T18 device run,
performance result, TP4 service, full matrix or all-357 quality has occurred.
The corrected final TTFT >=20% and TPOT >=10% thresholds apply. Keep T16's
validated TTFT component. No commit/push or final promotion in this round.

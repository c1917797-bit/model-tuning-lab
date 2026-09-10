# Qwen3.8 NVFP4 on Ascend 910B4 Handoff

## Status

- Dedicated worktree: `/opt/host/vnf/austinov/worktrees/qwen38-nvfp4-ascend-910b4`.
- The fixed image's vLLM core can parse this official checkpoint through
  `modelopt_mixed` and already handles its Qwen3.5 prefix aliases. Do not
  translate it into the separate ModelSlim `quant_model_description.json`
  format.
- The actual blocker is that the Ascend platform does not list
  `modelopt_mixed` as supported, and vLLM core's selected per-layer methods are
  GPU implementations rather than Ascend execution methods.
- The checkpoint is mixed precision: 193 dense NVFP4 layers at group size 16
  and 208 FP8 layers. The fixed image registers `W4A16_MXFP4` only for MoE and
  defaults that path to group size 32; no dense group-16 registration exists.
- ops-transformer contains useful E2M1/A16F4 source, but it is not proof of
  910B4 support: FP4-specific kernels are under `arch35`, and the per-group
  checker accepts only 32/64/128/256 while this checkpoint requires 16.
- A dependency-free exact-format reference codec and tests are now present.
- The reference test passed both on the host and in a network-disabled,
  device-free, disposable `quay.io/ascend/vllm-ascend:v0.23.0` container.
- The fixed image itself contains CANN 9.1.0, Bisheng, ATC, OPP, msprof and
  cannsim. A read-only CANNBot environment check passed inside a disposable
  container, so it can also be used as the isolated build environment.
- The exact official snapshot is complete at
  `/cache/cch/Qwen3.8-27B-NVFP4`. All three shards have recorded SHA256
  identities in `checkpoint-evidence.json`.
- A fail-closed checkpoint inspector passes host and fixed-image tests.
- Representative rows from all three shards were independently decoded against
  NVIDIA ModelOpt commit
  `079078de9d3cd26fa5baafdb754bba29dde24f7d`: all 15,360 sampled values
  matched exactly (maximum absolute error `0.0`). Together with the full
  checkpoint inspector, this verifies the packed-nibble, finite-E4M3 local
  scale, FP32 global scale, and group-16 storage contract. It does not yet
  prove end-to-end model accuracy.
- The checkpoint inspector now also validates every FP8 layer's rank-2
  `F8_E4M3` weight plus scalar FP32 `input_scale` and `weight_scale`. All 208
  FP8 layers pass, so all 401 mixed-precision layer declarations now have a
  checked tensor-storage contract. This still does not validate an Ascend FP8
  execution path.
- A proposed `nvfp4_group16_matmul` L0 operator contract now exists under
  `qwen38-nvfp4-ascend/operator/`. CANNBot strict validation passes stages
  1-7 with no warnings. Stages 8-11 are explicitly skipped because the current
  formula harness cannot preserve relational `K:K/2:K/16` symbolic shapes;
  executable tensor truth remains covered by `validate_real_tensor.py`.
- The contract correctly exposes finite-E4M3 checkpoint data as raw `uint8`
  bytes because Ascend 910B4 has no native FP8 dtype. It does not claim native
  FP8 hardware support.
- No NPU kernel, performance result, or accuracy result is claimed yet.

## Current blockers

1. The 2026-09-10 live audit found NPU0-3 occupied by four Qwen3.5 TP workers.
   NPU4-7 had no processes but remain in an external DRRQR container declaration.
   The current test requires all physical NPU0-7 in one exclusive lease; re-audit
   before any device action and never stop or alter either external workload.
2. The fixed image needs an external, fail-closed ModelOpt method adapter plus
   dense NVFP4 group-16 and calibrated FP8 Ascend execution methods. The exact
   AscendC adapter/kernel is not implemented yet. The FP8 path must also be
   validated because this checkpoint
   has 208 FP8 layers; it is not an all-FP4 model.
3. Two pushes of the latest local commits failed with a transient GitHub TLS
   receive error. The commits and unpushed operator spec remain safe locally;
   retry without rewriting history.

## Next actions

1. Reuse and unit-test vLLM core's `ModelOptMixedPrecisionConfig` layer
   resolution, then implement a guarded external plugin which enables the
   method only for this contract and returns Ascend-specific per-layer methods.
2. Run a build-only 910B4 capability probe against the ops-transformer A16F4
   source. If it cannot compile for 910B4, do not port its arch35 kernels
   blindly; implement the smallest 910B4 group-16 stream-dequant + BF16 Cube
   path. Build only inside the fixed image with source/output bind mounts.
3. Gate TP4 M=1 Qwen shapes for correctness and repeated latency.
4. Only after promotion, integrate through a read-only mounted plugin in a
   fresh disposable container and run BF16/NVFP4 paired performance and quality.

## Verified operations

- Chip detection: `exec-0000000000001385`, DCMI `Ascend910B4`.
- Host reference codec: `exec-0000000000001386`, pass.
- Fixed-image device-free codec: `exec-000000000000138c`, pass.
- Fixed-image CANNBot environment: CANN 9.1.0, pass with one non-blocking
  runtime-library-path warning.
- Checkpoint inspector host and fixed-image tests: pass.
- Complete official checkpoint contract: `exec-00000000000013df`; 3/3 shards,
  2,194 tensors, all 193 NVFP4 layers validated with zero ABI errors.
- Representative real rows from all three shards:
  `exec-00000000000013e3`, `exec-00000000000013e4`, and
  `exec-00000000000013e5`; 15,360 decoded values total, exact matches,
  maximum absolute error `0.0`.
- Checkpoint SHA256 manifest: `exec-00000000000013e6`; recorded in
  `checkpoint-evidence.json`.
- CANNBot strict L0 spec validation: `exec-000000000000001c`; stages 1-7
  PASS, stages 8-11 explicit SKIP for the documented relational-shape harness
  limitation, zero warnings and zero failures.
- Real `lm_head.weight` row-0 ModelOpt cross-check:
  `exec-00000000000013cd`, exact match, maximum absolute error `0.0`,
  packed-row SHA256
  `31c1dd3c007d2daca930d927d6217ade2a96ba42826bfd3ae8073c22d7f0c4d7`.
- Fixed-image ModelSlim/registry/API audit:
  `exec-000000000000003a` through `exec-0000000000000045`; recorded in
  `runtime-compatibility-evidence.json`. It proves that an external execution
  method adapter and dense group-16 scheme are required. It is device-free evidence,
  not an NPU support or speed claim.
- Mixed NVFP4/FP8 checkpoint inspector: host `exec-000000000000004b` and
  fixed-image read-only mount `exec-000000000000004d`; 193/193 NVFP4 and
  208/208 FP8 layers passed with zero tensor-contract errors.
- Fixed-image `torch_npu` public API contract and ops-transformer source audit:
  `exec-0000000000000064`, `exec-0000000000000066` through
  `exec-0000000000000069`. A2 documentation does not establish FP8/FP4
  `npu_quant_matmul`; ops-transformer group-16/910B4 capability remains
  unproven and must be probed rather than assumed.
- Whitespace/error check: `exec-0000000000001387`, pass.
- Live resource audit: `exec-000000000000138a` and
  `exec-000000000000138b`; NPU0-3 unavailable.

## Safety

Do not modify the fixed image, site-packages, host framework sources, external
containers, or NPU4-7. Store raw datasets, weights and runtime artifacts outside
Git and commit only code, protocols, manifests and summarized evidence.

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
- A device-free, network-disabled build probe in the fixed image selected the
  real top-level `matmul_all_reduce` target for `ascend910b`. Configuration,
  host/arch22 tiling compilation, and 298 kernel objects succeeded before the
  deliberately bounded probe was stopped. The op contract explicitly says
  FP8/FP4 support is new on Ascend 950 and requires antiquant group sizes that
  are multiples of 32. This closes direct reuse for the checkpoint's group-16
  NVFP4 tensors; it is not an NPU execution or speed result.
- A dependency-free exact-format reference codec and tests are now present.
- A separately installable vLLM general plugin now registers
  `modelopt_mixed_ascend_bf16_reference`. It preserves core ModelOpt layer
  resolution, reconstructs NVFP4/FP8 weights with per-fused-shard scales, uses
  BF16 linear compute, and refuses construction unless the explicit reference
  opt-in is set. It does not emulate activation quantization and is therefore
  an integration/quality upper-bound reference, not the final quantized path.
- The reference test passed both on the host and in a network-disabled,
  device-free, disposable `quay.io/ascend/vllm-ascend:v0.23.0` container.
- The fixed image itself contains CANN 9.1.0, Bisheng, ATC, OPP, msprof and
  cannsim. A read-only CANNBot environment check passed inside a disposable
  container, so it can also be used as the isolated build environment.
- The exact official snapshot is complete at
  `/cache/cch/Qwen3.8-27B-NVFP4`. All three shards have recorded SHA256
  identities in `checkpoint-evidence.json`.
- The BF16 control is complete at `/cache/austinov/Qwen3.8-27B`: all 18
  safetensor shards are present (55,563,006,776 bytes), its architecture is
  `Qwen3_5ForConditionalGeneration`, and it has no quantization config.
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
- The quality protocol is now frozen in `QUALITY_PROTOCOL.md`. Stable request
  manifests were generated for 57-subject MMLU (14,042 tests), GSM8K (1,319),
  and HumanEval (164), with source/output SHA256 identities recorded in
  `quality-protocol-evidence.json`. Strict MMLU/GSM8K paired scoring code and
  fixed-image unit tests pass. Generated artifacts remain ignored by Git.
- The old eight-device DP2 launcher has been removed. Matched launchers now
  expose only physical NPU0-3 and use TP4: `start_bf16_tp4.sh` for the control
  and `start_nvfp4_reference_tp4.sh` for the external reference plugin. Model
  and plugin mounts are read-only; candidate installation is confined to its
  disposable container layer. Shell syntax validation passes, but neither
  launcher has been executed while the lease is unavailable.

## Current blockers

1. The 2026-09-10 live audit found NPU0-3 occupied by four Qwen3.5 TP workers.
   NPU4-7 had no processes but remain in an external DRRQR container declaration
   and are protected. The current test requires one exclusive lease for physical
   NPU0-3 only; re-audit before any device action and never stop or alter either
   external workload.
2. The fixed image now has a device-free validated external, fail-closed
   ModelOpt BF16 reference adapter, but it has not passed a four-rank model
   startup. Native or faithfully emulated activation quantization is still
   required before claiming the official NVFP4/FP8 runtime semantics.
   Native reuse of the ops-transformer FP4 path is closed for 910B4/group16.
   The next correctness-first implementation is exact ModelOpt NVFP4 and FP8
   decoding to BF16 weights at load time. That path can establish checkpoint
   semantics and full-model quality but must be labelled a BF16-compute
   fallback, not native quantized acceleration. A later 910B4 stream-dequant
   kernel is eligible only after this reference path passes.
3. Two pushes of the latest local commits failed with a transient GitHub TLS
   receive error. The commits and unpushed operator spec remain safe locally;
   retry without rewriting history.

## Next actions

1. On the next valid NPU0-3 lease, start the BF16 control with TP4 in a fresh
   disposable container and record four-rank activation, load time and memory.
2. Then start the BF16-compute reference plugin
   through a read-only mount and disposable installation. Require four-rank
   activation and record load-time plus per-rank memory before any request.
3. Run deterministic smoke and a small paired quality canary. Label these
   results as weight-fidelity BF16-compute reference results because activation
   quantization is not yet emulated.
4. Only after the reference adapter passes, evaluate a 910B4 group-16
   stream-dequant + BF16 Cube operator against it; do not port arch35 code.
5. Integrate through a read-only mounted plugin in a
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
- Offline ascend910b build probe: dependency discovery
  `exec-00000000000000d6`; real top-level build
  `exec-00000000000000f5`; bounded stop of the exact disposable container
  `exec-000000000000011a`; source identities and post-build inspection
  `exec-000000000000011e`. Configuration and arch22 host compilation passed,
  298 kernel objects were generated, and no full-build or FP4 capability claim
  is made.
- BF16 reference adapter tests: unit/load-after-process
  `exec-000000000000013a` (7/7 pass); real checkpoint NVFP4 and FP8 rows
  `exec-0000000000000136` (5120 and 6144 values, exact); standard package
  install and vLLM entry-point discovery `exec-0000000000000134`; all 401
  official layer mappings `exec-000000000000013b` (193 NVFP4, 208 FP8).
  Detailed evidence and preserved development failures are in
  `reference-adapter-evidence.json`.
- BF16 control and local evaluation data discovery: `exec-0000000000000148`,
  `exec-0000000000000147`, and dataset structure/count audit
  `exec-0000000000000149` through `exec-000000000000014a`.
- Frozen full quality manifests: `exec-000000000000014e`; fixed-image,
  network-disabled, device-free tests: `exec-000000000000014f` and
  `exec-0000000000000151`. See `quality-protocol-evidence.json`.
- Four-device TP4 launcher syntax validation: `exec-0000000000000159`, pass.
- Whitespace/error check: `exec-0000000000001387`, pass.
- Live resource audit: `exec-000000000000138a` and
  `exec-000000000000138b`; NPU0-3 unavailable.

## Safety

Do not modify the fixed image, site-packages, host framework sources, external
containers, or NPU4-7. Store raw datasets, weights and runtime artifacts outside
Git and commit only code, protocols, manifests and summarized evidence.

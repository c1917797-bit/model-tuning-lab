# Qwen3.8 NVFP4 on Ascend 910B4 Handoff

## Status

- Dedicated worktree: `/opt/host/vnf/austinov/worktrees/qwen38-nvfp4-ascend-910b4`.
- Stock vLLM-Ascend 0.23.0 has no ModelOpt NVFP4 loader.
- ops-transformer proves E2M1/A16F4 capability, but its available per-group
  contract starts at 32 while the checkpoint requires 16.
- A dependency-free exact-format reference codec and tests are now present.
- The reference test passed both on the host and in a network-disabled,
  device-free, disposable `quay.io/ascend/vllm-ascend:v0.23.0` container.
- No NPU kernel, performance result, or accuracy result is claimed yet.

## Current blockers

1. The official NVFP4 checkpoint is not present under `/cache`, and current
   host access to Hugging Face endpoints times out.
2. The host has driver/firmware but no host CANN Toolkit installation. Compile
   in an isolated Toolkit development container rather than changing the host.
3. The 2026-09-10 live audit found NPU0-3 occupied by four Qwen3.5 TP workers.
   NPU4-7 had no processes but remain in an external DRRQR container declaration.
   Re-audit before any device action and never stop those workloads.

## Next actions

1. Select an isolated CANN Toolkit development image and run the CANNBot
   environment check inside it.
2. Make the official checkpoint available locally and compare sampled decoded
   tensors with an independent ModelOpt/vLLM reference.
3. Implement the group-16 stream-dequant + BF16 Cube direct AscendC operator.
4. Gate TP4 M=1 Qwen shapes for correctness and repeated latency.
5. Only after promotion, integrate through a read-only mounted plugin in a
   fresh disposable container and run BF16/NVFP4 paired performance and quality.

## Verified operations

- Chip detection: `exec-0000000000001385`, DCMI `Ascend910B4`.
- Host reference codec: `exec-0000000000001386`, pass.
- Fixed-image device-free codec: `exec-000000000000138c`, pass.
- Whitespace/error check: `exec-0000000000001387`, pass.
- Live resource audit: `exec-000000000000138a` and
  `exec-000000000000138b`; NPU0-3 unavailable.

## Safety

Do not modify the fixed image, site-packages, host framework sources, external
containers, or NPU4-7. Store raw datasets, weights and runtime artifacts outside
Git and commit only code, protocols, manifests and summarized evidence.


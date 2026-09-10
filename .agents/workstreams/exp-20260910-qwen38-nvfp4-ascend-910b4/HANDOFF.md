# Qwen3.8 NVFP4 on Ascend 910B4 Handoff

## Status

- Dedicated worktree: `/opt/host/vnf/austinov/worktrees/qwen38-nvfp4-ascend-910b4`.
- Stock vLLM-Ascend 0.23.0 has no ModelOpt NVFP4 loader.
- ops-transformer proves E2M1/A16F4 capability, but its available per-group
  contract starts at 32 while the checkpoint requires 16.
- A dependency-free exact-format reference codec and tests are now present.
- The reference test passed both on the host and in a network-disabled,
  device-free, disposable `quay.io/ascend/vllm-ascend:v0.23.0` container.
- The fixed image itself contains CANN 9.1.0, Bisheng, ATC, OPP, msprof and
  cannsim. A read-only CANNBot environment check passed inside a disposable
  container, so it can also be used as the isolated build environment.
- The exact official snapshot download is active as
  `exec-00000000000013ad`, using `hf-mirror` with Xet disabled and a
  resumable local directory at `/cache/cch/Qwen3.8-27B-NVFP4`.
- A fail-closed checkpoint inspector passes host and fixed-image tests.
- One real row from the already complete third shard was independently decoded
  against NVIDIA ModelOpt commit
  `079078de9d3cd26fa5baafdb754bba29dde24f7d`: all 5,120 values matched
  exactly (maximum absolute error `0.0`). This proves the packed-nibble,
  FP8-local-scale and FP32-global-scale semantics for that sampled tensor; it
  does not yet prove checkpoint completeness or end-to-end accuracy.
- No NPU kernel, performance result, or accuracy result is claimed yet.

## Current blockers

1. The official NVFP4 checkpoint download is still incomplete. Partial shards
   may be inspected read-only, but do not declare checkpoint completeness or
   start serving until the operation completes and the full shard index passes
   the checkpoint inspector.
2. The 2026-09-10 live audit found NPU0-3 occupied by four Qwen3.5 TP workers.
   NPU4-7 had no processes but remain in an external DRRQR container declaration.
   Re-audit before any device action and never stop those workloads.

## Next actions

1. Poll `exec-00000000000013ad`; after completion, run
   `inspect_checkpoint.py`, record identities and extend the independent
   ModelOpt comparison to representative tensors from every completed shard.
2. Implement the group-16 stream-dequant + BF16 Cube direct AscendC operator,
   building inside the fixed image with source/output bind mounts.
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
- Real `lm_head.weight` row-0 ModelOpt cross-check:
  `exec-00000000000013cd`, exact match, maximum absolute error `0.0`,
  packed-row SHA256
  `31c1dd3c007d2daca930d927d6217ade2a96ba42826bfd3ae8073c22d7f0c4d7`.
- Whitespace/error check: `exec-0000000000001387`, pass.
- Live resource audit: `exec-000000000000138a` and
  `exec-000000000000138b`; NPU0-3 unavailable.

## Safety

Do not modify the fixed image, site-packages, host framework sources, external
containers, or NPU4-7. Store raw datasets, weights and runtime artifacts outside
Git and commit only code, protocols, manifests and summarized evidence.

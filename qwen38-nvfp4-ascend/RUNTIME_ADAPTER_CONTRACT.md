# Runtime Adapter Contract

This document defines the smallest safe integration boundary for the official
Qwen3.8-27B-NVFP4 checkpoint and the immutable vLLM-Ascend 0.23.0 image.

## Why an adapter is required

The checkpoint is not a single-format FP4 model. Its ModelOpt description
contains 193 dense NVFP4 layers and 208 FP8 layers. NVFP4 uses group size 16.

The fixed image has a ModelSlim configuration loader, but it reads
`quant_model_description.json`. The official checkpoint instead contains
`hf_quant_config.json`. The fixed image also registers `W4A16_MXFP4` only for
MoE layers, with group size 32 as its default. Qwen3.8 needs dense linear,
group-16 loading. Therefore, changing a serve flag cannot make the checkpoint
load correctly.

## Plugin boundary

The deliverable must be an external, read-only mounted plugin. It may:

1. parse `hf_quant_config.json` in memory;
2. translate every checkpoint layer to an explicit runtime scheme;
3. register a dense `W4A16_MXFP4` group-16 implementation;
4. reuse a fixed-image FP8 path only after tensor and numerical validation;
5. reject startup before allocating model weights when any layer is unmapped.

It must not create or overwrite `quant_model_description.json`, edit the
checkpoint, modify site-packages, overlay framework sources, or commit a
container.

## Fail-closed gates

- Exactly 193 NVFP4 and 208 FP8 layer declarations must be consumed.
- Every NVFP4 weight must be packed `uint8`; its local scale must be finite
  E4M3 data and its global scale a scalar FP32 value.
- Every NVFP4 layer must declare group size 16.
- Packed fused projections must have one consistent quantization scheme across
  all shards.
- Unsupported shapes, dtypes, device generations, or operator return dtypes
  must stop startup with a diagnostic; no silent BF16 fallback is allowed in a
  performance comparison.
- Operator correctness must pass against the checked-in reference decoder
  before a full-model run.

## Evidence boundary

`runtime-compatibility-evidence.json` records the fixed-image source audit.
It proves the adapter is necessary, not that the proposed kernel works on
Ascend 910B4. Performance and MMLU/GSM8K/HumanEval claims remain blocked until
paired on-device validation completes.

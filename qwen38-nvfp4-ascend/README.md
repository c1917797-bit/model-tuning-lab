# Qwen3.8-27B NVFP4 on Ascend 910B4

This directory owns the exact-format feasibility and validation work for
`nvidia/Qwen3.8-27B-NVFP4` versus Qwen3.8-27B BF16 on Ascend 910B4.

## What is proven

- The checkpoint uses ModelOpt mixed precision: MLP/lm_head NVFP4 E2M1 with
  group size 16 and FP8 local plus FP32 global scales; attention uses FP8.
- CANN ops-transformer contains `FLOAT4_E2M1` support and an A16F4 path on
  910B-class hardware.
- The available A16F4 per-group contract accepts 32/64/128/256, not NVIDIA's
  group 16. Directly relabeling the checkpoint would be numerically wrong.
- `nvfp4_codec.py` is the dependency-free golden reference for low-nibble
  packing, E2M1 values, E4M3FN scales, and group-16 dequantization.

## Implementation route

1. Validate the reference codec against tensors from the official checkpoint.
2. Build a direct AscendC operator that streams packed group-16 E2M1 weights
   and their scales from GM, expands tiles to BF16, and feeds the 910B4 Cube
   matmul path. It must not materialize the whole BF16 model.
3. Gate exact Qwen tensor-parallel M=1 shapes before runtime integration.
4. Load the accepted operator and Python adapter into a fresh vLLM-Ascend
   0.23.0 container through read-only mounts/PYTHONPATH only.
5. Compare the exact NVFP4 checkpoint against BF16 with the same prompts,
   chat template, decoding parameters, TP degree, device set and repetitions.

The existing vLLM-Ascend image and its site-packages are immutable. No
`docker commit`, `docker cp`, source overlay, or in-image replacement is
permitted.

## Acceptance protocol

- Performance: repeated TTFT/TPOT P50/P95/P99 and throughput at c1 and c16
  first, then the declared full matrix if the fail-fast gate passes.
- Quality: full MMLU, GSM8K (1,319), and HumanEval (164), with the same
  deterministic evaluation harness for BF16 and NVFP4.
- Correctness: synthetic codec tests, sampled real-tensor dequantization
  comparison, operator error envelope, and four-rank activation proof.
- Evidence: raw outputs, protocol, image/model identities and SHA256 manifest.

Run the device-free codec check with:

```bash
python3 qwen38-nvfp4-ascend/test_nvfp4_codec.py
```

After downloading the official snapshot, fail closed on format and shard
completeness before any conversion or serving attempt:

```bash
python3 qwen38-nvfp4-ascend/inspect_checkpoint.py \
  /cache/cch/Qwen3.8-27B-NVFP4
```

Cross-check a real packed row against the independently pinned NVIDIA
ModelOpt dequantization semantics:

```bash
python3 qwen38-nvfp4-ascend/validate_real_tensor.py \
  /cache/cch/Qwen3.8-27B-NVFP4 --tensor lm_head.weight --row 0
```

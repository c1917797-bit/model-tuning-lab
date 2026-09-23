# Qwen3.6 Ascend matmul paper shape gate (2026-09-23)

This is a source/profile applicability screen, **not** a new NPU benchmark,
candidate implementation, or end-to-end result. Its purpose is to avoid
commissioning an Ascend operator solely because aggregate MatMul time is high.
The target remains Qwen3.6-27B BF16, vLLM-Ascend v0.23.0/CANN 9.1, TP4 on
physical NPU4–7, with an explicit opt-in plugin delivery and a matched dense
fixed-1024 output throughput target of at least +10%. Final task accuracy is
evaluated separately; the latest user allowance is at most one percentage
point loss on each matched task.

## Measured shape distribution

The existing 4-rank, 30-worker-step decode profile has MatMulV2/MatMulV3 at
50.297% of summed operator time. This is diagnostic operator time, **not**
critical-path time or a direct end-to-end opportunity bound. In the four
decode `kernel_details.csv` files, the MatMul input shapes are consistently
`M=16` at the tested 16-way decode concurrency. Representative rank0
totals over the capture are:

| Activation M×K | Weight N×K | MatMul time, ms | Calls |
| --- | --- | ---: | ---: |
| 16×5120 | 8704×5120 | 309.024 | 1920 |
| 16×4352 | 5120×4352 | 135.281 | 1920 |
| 16×5120 | 4096×5120 | 92.259 | 1440 |
| 16×1536 | 5120×1536 | 53.594 | 1920 |
| 16×5120 | 62080×5120 | 27.991 | 30 |
| 16×5120 | 3584×5120 | 27.580 | 480 |
| 16×5120 | 24×5120 | 17.151 | 1440 |

All four ranks have about 662 ms of MatMul time each. Using `K > 2N` only
as an explicit heuristic for a strong large-K/small-N shape, the only
qualifying row is N=24: 17.03–17.18 ms per rank, or 2.57–2.59% of MatMul
time. The paper itself does **not** specify this 2× cutoff. The rank0
operator totals, call counts and shapes are extracted from the pinned raw
profile rather than inferred from model configuration.

Profile summary:
`/cache/cch/qwen36-paper-portfolio-synthesis-20260920/dense-profile-v1/profile-summary-v2.json`,
SHA256 `7d7554583eb202c26d51e946e8e3fd741e1a8578b1bba882f1af02104da06d81`.
It references the four raw decode traces and their individual checksums.

## Paper and deployed-source fit

1. [Vectorization of Narrow Matrix Multiplication for Ascend AI Inference
   Acceleration](https://arxiv.org/html/2609.16009v1) formally requires
   `min(M,N)=1`, idle AIVs, and subsequent independent Cube work that can
   overlap with the offloaded narrow MatMul. Its reported 20% is an MLA
   operator gain in a **single-token** DeepSeek-V3 case, not a Qwen3.6
   serving result. The current M=16 trace fails the stated narrow-dimension
   condition. This is a no-go for a faithful port under the frozen 16-way
   decode screen; it says nothing about a separate batch-one workload.
2. [W4A16 Mixed-Precision Matrix Multiplication on Decoupled
   Architecture](https://arxiv.org/html/2601.16536v2) proposes vector-side
   INT4 dequantization, Cube GEMM, and Split-K. It reports a maximum 1.48×
   kernel speedup over native FP16 matmul on tested shapes, **not** an E2E
   speedup or a quality result for this checkpoint. Its Split-K advantage is
   strongest for K much larger than N; the strong-ratio heuristic above covers
   only a small fraction of the current MatMul time. This is an investment
   warning for that specialized shape, not a proof against all W4A16 linear
   quantization.
3. The pinned vLLM-Ascend commit
   `5cb98caaadeff42b5b62b996e34bb2aaa29d20fd` already registers a
   W8A16 **linear** method and a W4A8_DYNAMIC **linear** method whose
   `apply` keeps activation `x` unquantized and calls
   `torch_npu.npu_weight_quant_batchmatmul`. Its W4A16 registration is
   **MoE-only**, not a dense Qwen linear implementation. The W4A8 method
   requires an msModelSlim-formatted checkpoint; this installed target is
   BF16, with no local Qwen3.6 quantized checkpoint found in the checked
   model directory. Reuse these native paths before inventing a kernel.
4. The inspected `CANN/ops-transformer` checkout at
   `0684247214bae5abb5cb6dc7d90b34a6ad401cdd` contains
   `weight_quant_batch_matmul_v2_custom_mix_splitk.h` (SHA256
   `7d3a3d71e4edf456cde6d9897d0ac1bf7fed6b7011c5541e2e3542e53972628d`).
   Source presence does not prove that the deployed CANN binary selects this
   tiling or that its numerical/performance behavior matches the paper.

## Next bounded decision

Do not generate a custom vector-matmul or W4A16 Split-K operator yet.
The next distinct matmul candidate must cover the dominant M=16 projection
shapes and demonstrate a measured algorithm-specific gap against the
existing native weight-quantized path. A weight-only PTQ variant is worth
screening only with (a) a pinned quantization rule and plugin-owned loading
seam, (b) real NPU quantized-vs-BF16 numerical checks, (c) capability and
actual tiling evidence, and (d) a same-stack dense/candidate service screen
before final LongBench-v2/GSM8K. If that cannot be assembled inside a
one-day paper timebox, close it as inconclusive and pivot to a different
measured attention or matmul mechanism. No new profiling capture is needed
until an exact kernel/tiling question remains after reusing these traces.

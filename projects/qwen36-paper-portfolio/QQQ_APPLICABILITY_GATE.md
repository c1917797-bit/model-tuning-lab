# QQQ W4A8: Qwen3.6/Ascend applicability gate

Date: 2026-09-28 UTC. This is a source and historical-artifact audit, not a
QQQ candidate, a new NPU benchmark, or a performance/quality claim. The next
experiment must be bounded by the one-day per-paper rule.

## Mechanism and provenance

- Paper: https://arxiv.org/html/2406.09904v3. QQQ combines selectively
  smoothed activation channels, Hessian/GPTQ weight-error compensation,
  symmetric per-token INT8 activation quantization, and per-channel or
  per-group INT4 weight GEMM. Its reported service gains were on NVIDIA A100,
  LLaMA-2, 1024 input/128 output; none transfers numerically to this target.
- Author source: https://github.com/HandH1998/QQQ at
  `54c5c99037200f3b42b94877dcc932989e458409`, inspected in a separate
  read-only research checkout at `/cache/cch/QQQ-official-20260928`.
  Its implemented model adapters are LLaMA and Qwen2, not Qwen3.6 hybrid GDN.
- The author script defaults to `--smooth false --rotation true`, and says
  no smoothing currently gives better results. This **code-default** route
  must not silently stand in for the paper's adaptive-smoothing route.
  Rotation across Qwen3.6 hybrid attention/GDN needs a separate equivalence
  proof. A paper-faithful smoothing+GPTQ arm and an author-default
  rotation+GPTQ arm are distinct candidates.
- The checkout has no tracked LICENSE/COPYING file. Do not copy author code
  into the plugin without establishing permission; an implementation can use
  the published equations and independently written, tested code.

## Target and existing substrate

The frozen target is Qwen3.6-27B BF16, vLLM-Ascend v0.23.0/CANN 9.1, TP4 on
physical NPU4-7, fixed 1024 output tokens. The 4-rank/30-step decode trace
shows M=16 MatMuls at 50.297% of **summed operator time**, not a critical-path
share. The dominant shapes are recorded in `MATMUL_PAPER_SHAPE_GATE.md`.

Pinned vLLM-Ascend's `W4A8_DYNAMIC` dense linear method consumes BF16 `x`
at its Python boundary and calls `npu_weight_quant_batchmatmul` with packed
INT4 weights and per-group antiquant scales. This is a reusable loading and
operator seam. The Python call alone does not establish the deployed kernel's
internal activation arithmetic or whether it implements QQQ's fused INT4-to-
INT8/GEMM/dequant pipeline. Verify actual operator/tiling behavior before
claiming equivalence or commissioning a replacement. No `qqq` scheme is
registered in the pinned vLLM-Ascend source.

Historical non-QQQ msModelSlim AWQ W4A8 checkpoints exist under
`/cache/cch/qwen36-awq-w4a8-20260923/`. A physical-NPU4 batch-16
native packed-INT4 eager/graph ABI probe passed; a real layer-3, 5120-to-12288
group-128 probe reported ~0.117 relative RMS against BF16 on two inputs.
Those are **intermediate** observations, not task accuracy. `quantized-awq-v4`
contains only incomplete shards and must not be treated as a loadable model.
The previous W8A8/SmoothQuant client-only throughput JSONs in
`KV_QUANT_REUSE_GATE.md` are screening clues, not matched acceptance results.

## Next bounded decision

1. First check the native substrate on the actual physical 4-7 lane: exact
   container/device mapping, operator identity and loaded weight layout,
   BF16-vs-quantized reference correctness under eager and NPUGraph, and the
   dominant M=16 shapes. Reuse the complete non-QQQ AWQ checkpoint only as a
   **substrate** control, never as a QQQ result. A local operator timing is
   merely an investment gate, not end-to-end speedup.
2. If the substrate leaves a credible >=10% service opportunity, implement
   independently named, opt-in QQQ-specific calibration for Qwen3.6 linears
   (paper-faithful selective smoothing plus Hessian compensation, symmetric
   group-128 weights), convert to a plugin-owned checkpoint/loading seam, and
   prove quantizer equations and NPU output/state/graph behavior. If true
   W4A8 arithmetic is absent, identify its measured gap against the native
   operator before creating a CANN kernel.
3. Only after correctness, run profiler-off paired BF16-dense and candidate
   service screens with identical common optimizations, 1024 output tokens,
   throughput/TTFT/TPOT and bound manifests. Repeat promising candidates;
   assess final LongBench-v2 and GSM8K last. Report both percentage-point and
   relative task-accuracy loss for the user's 1% allowance.
4. If the one-day gate cannot establish a distinct QQQ mechanism and a
   service opportunity, preserve an `inconclusive` or implementation-scoped
   `no-go` with the exact failed gate. Do not declare the paper invalid from
   an AWQ probe or a synthetic operator benchmark.

No QQQ model, operator, service run, or final acceptance evidence exists yet.

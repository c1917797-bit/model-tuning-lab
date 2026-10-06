# DAMP compressed-state decode operator (v1, not yet validated)

Status: same-image no-device v3 compilation passed; v1 library-load/Meta gate
failed on an unavailable format-helper export. The public-export repair below
still requires a fresh build/load gate. **No NPU operator correctness, graph
support, vLLM cache-manager integration, or end-to-end benefit is claimed.**
Parent agent exclusively owns build / NPU / Git.

The algorithm-specific gap is fused load of FP16 high-K and INT8 low-K state,
FP32 reconstruction in UB, DAMP per-value-head K/V permutation and SR transform,
one-token recurrent update, original-coordinate readout, and requantized store.
It is not a general normalization/gating fusion or a dense-state shortcut.

## Frozen ABI

Call with contiguous ND NPU tensors on the same device:

Physical storage is explicitly checked using the same-image public header
torch_npu/csrc/aten/CustomFunctions.h and
at_npu::native::custom_ops::get_npu_format(tensor) == ACL_FORMAT_ND. It is not
inferred from is_contiguous(), shape or dtype. Other base/internal/blocked
formats are rejected synchronously, without a silent format conversion.
Construct or explicitly convert inputs to ND outside capture. Output and
tiling allocations are checked as well. This strict v1 seam does not accept
NCHW merely because its physical storage may sometimes be contiguous.

The original FormatHelper::GetFormat declaration is not dynamically exported
in this image and failed the real no-device load gate. The chosen replacement
is declared TORCH_NPU_API int64_t get_npu_format(const at::Tensor&) in namespace
at_npu::native::custom_ops, and the same-image libtorch_npu.so has a defined,
GLOBAL, DEFAULT-visible dynamic symbol:
_ZN6at_npu6native10custom_ops14get_npu_formatERKN2at6TensorE.
The v3 link command already used -ltorch_npu and its actual ELF DT_NEEDED
includes libtorch_npu.so: this was an unavailable API export, not missing
linkage. No storage-format guard was removed or weakened. Library ABI audit:
libtorch_npu.so SHA256
83fb9a0eb249aef6bca7f8463047fcb4d3062cc4849f17ddf31a5e050c838842,
ELF64 little-endian AArch64, 82429241 bytes. The failed v3 plugin SHA256 is
6550e522d3012a97bd7a114fe1a3d0d6b750dba049fcb162c76e39e166ce0a82.
Its DT_NEEDED also includes libascendcl.so, libstdc++.so.6, libgcc_s.so.1,
libc.so.6 and ld-linux-aarch64.so.1. Its RPATH includes the image's
/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/lib.
Logs: external operator-build-v3.log and operator-library-meta-v1.log.

| Tensor | Shape | Type / units |
| --- | --- | --- |
| query, key | [T,4,128] | BF16, already native-normalized |
| value | [T,12,128] | BF16, post-convolution/SiLU |
| g / beta | [T,12] | FP32 / BF16 |
| high_state | [S,12,128,16] | FP16, value-major |
| low_state | [S,12,128,112] | signed INT8, value-major |
| low_scale | [S,12,4,112] | FP32, each group covers 32 reordered V rows |
| pk, pv, inv_pv | [12,128] | INT32 logical indices 0..127, NOT byte offsets |
| sr | [12,128] | positive finite FP32 c in original V coordinates |
| actual_seq_lengths | [T+1] | INT32 [0,1,...,1], not cumulative lengths |
| state_indices | [T] | INT32 distinct active slots, no padding |

Only T=1 or16 is supported. There is no speculative/mixed-length/prefill path.
Pk and Pv map reordered to original coordinates. InvPv is its value-axis
inverse: inv_pv[pv[i]]=i. GQA is hQK=hV//3, but Pk is applied independently per
value head. Byte offsets are created only inside the Gather implementation.

Prepare once **outside capture** for each device/T/S/static-plan identity:

    torch.ops.load_library(EXPLICIT_SO_PATH)
    torch.ops.qwen36_damp.prepare(query, hi, pk, pv, inv_pv, sr)
    output = torch.ops.qwen36_damp.decode(
        query, key, value, g, beta, hi, lo, scales,
        pk, pv, inv_pv, sr, actual_seq_lengths, state_indices)

TORCH_LIBRARY schemas use mutable aliases (a!) hi, (b!) lo, (c!) scales and
return a fresh BF16 [T,12,128] output with no alias. Meta registration does only
shape/dtype work and is NOT evidence of graph support. Prepare validates static
permutations/inverse/SR on CPU, retains the immutable plans, and uploads tiling.
Decode rejects an unprepared identity rather than doing H2D allocation/copy in
capture. Static plans must never be mutated in capture, including inference
tensors with no version counter. Dynamic tensors/indices may change during
replay only after graph-specific numerical gates pass.

Unsupported shape/dtype/alias/static plan values raise TORCH_CHECK. Invalid
device metadata (padding, duplicate/out-of-range slots, non-unit length) causes
**all-NaN output with every state buffer untouched**, not partial updates.
The serving scheduler must also validate active metadata on its CPU seam before
dispatch. This direct operator gate is not a replacement for that integration.

## Equation / packing mapping

Reconstruct the current state: high FP16 cast to FP32; low INT8 multiplied by its
per-K, V-group scale. Apply g decay, native K128 dot/update/readout with q scaled
by 128^-0.5. Input V is divided by original-coordinate c then gathered by Pv;
Q/K are gathered by each value head's Pk. Readout comes from **updated FP32 UB
state before requantization**, then inverse Pv and original-coordinate c restore
the BF16 output. Store only compressed state; no persistent dense FP32 sidecar.

High K16 casts directly FP32->FP16 RNE. For each low K column use max(abs(V32)),
multiply by exact binary32 reciprocal 0x3c010204 (0.007874015718698502f),
and use scale=1 only when the original amax is exactly zero. Nonzero scale
underflow is not silently treated as zero. Quantize by FP32 division, first
FP32->INT32 CAST_RINT (ties-even), clamp [-127,127], then exact integer
FP32->FP16->INT8 conversion. Never convert to half before the first rounding.

Independent oracle: projects/damp-ascend/tests (math agent owns those files).
K128 reduction explicitly adds lower64+upper64 then WholeReduceSum64 per row;
outer update uses native-style MulAddDst. FP32 arithmetic divergence across a
discrete INT8 boundary must be diagnosed, not hidden by relaxing gates.
Div lowering, CAST_RINT, FP16 range, quantizer boundary and scale subnormals all
require real 910B4 tests. A passing equation/packing Python gate does not prove
this custom kernel, and a failing CPU oracle does not disprove the paper.

## Ownership / UB

One AIV task owns one complete (token,value-head), processes four groups, and
writes the complete 256-byte head output. Every state's group region is a
multiple of 64 bytes: high1024 / low3584 / scales448. No per-row 112-byte store
or arbitrary-Pv GM scatter, avoiding neighboring-writer DMA clobbering.

Declared UB: work79872 + queues18944 = **98816 bytes** (~96.5KiB).
Work: control/inputs/plans/vectors10240, FP32 state16384, FP32 matrix16384,
low3584 FP32=14336, reduction A14336, scratch B8192.
Queues: metadata160, token864, plans2048, packed input5120,
two packed output5120 buffers, two whole-output256 buffers.
A2 RA max is a five-pass Max ping-pong tree over V32, independently for K112;
the tree has no destructive overlap and finite max is order-independent.
Use TQue producer/consumer events and PIPE_V/HardEvent::V_S, not speculative
MTE2-only barriers. Runtime/compiler must verify UB/event resources.

B1 has only12 head tasks; B16 has192. This is a correctness-first tile and not
a throughput claim. Three typed buffers still need slot/page copy ownership,
prefix identity, allocation, scheduler and graph-key integration before serving.

## Build preparation (parent executes; no NPU required)

Use the existing v0.23/CANN9.1 image without modifying its upstream sources.
Source the **already verified** CANN set_env.sh and set ASCEND_HOME_PATH to that
same SDK; set Python3_EXECUTABLE to the verified image Python. Reserve this
fresh build path only if it is absent:

    cmake -S /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator \
      -B /cache/cch/qwen36-damp-20261006/operator-build-v1 \
      -DCMAKE_BUILD_TYPE=Release \
      -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3
    cmake --build /cache/cch/qwen36-damp-20261006/operator-build-v1 --parallel 4

Do not run those commands on an existing directory, silently pick another SDK,
or import/load the binary merely to claim a no-device compile passed.
Expected shared library: libqwen36_gdn_damp_decode_ops.so.

First build reached ASC/bisheng setup but stopped before any kernel compilation:
this image's torch import emits an npu-smi warning on stdout, contaminating
the original whole-stdout path discovery. CMake now checks both Python return
codes, extracts explicit DAMP metadata markers, verifies TorchConfig.cmake and
torch_npu's actual include/lib/CustomFunctions.h/libtorch_npu.so, and restricts
Torch discovery to that active-Python configuration. Old failed build/logs
must be preserved; rebuild in a fresh directory. This is build plumbing, not
an algorithm or performance result.

The wrapper is compiled LANGUAGE ASC, includes the kernel, launches inside the
queued OpCommand::RunOpApi lambda with stream(false). A C++ unqueued direct
launch instead requires stream(true): these routes must not be mixed.

## Upstream reuse / identity

- Native ordinary 910B recurrent arithmetic:
  /cache/austinov/src/vllm-ascend, commit
  5cb98caaadeff42b5b62b996e34bb2aaa29d20fd,
  csrc/attention/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h,
  SHA256 96e6d9667af1e3457316ffce92a8a983fcb90096df08e3efd13ec0b35b8b1c5b.
  Native adapter uses EXEC_NPU_CMD(aclnnRecurrentGatedDeltaRule,...).
- Queued direct invoke / K128 scaffold:
  projects/qwen36-deltalog/operator, last source commit
  5f6fda3fed9fc5a47a6c6326b7ac48053a7093f0.
- A2 RA/reduction/quantization audit:
  /cache/cch/ops-transformer, commit
  0684247214bae5abb5cb6dc7d90b34a6ad401cdd;
  attention/fused_infer_attention_score/op_kernel/attn_infra/epilogue/block/CombineScale.hpp
  explicitly has AtlasA2 RA ReduceMax with supplied scratch. Native OpDef
  provides no DAMP mixed-state storage ABI.
- Cannbot skill/template guidance:
  /cache/cch/cannbot-skills, commit d5e0d44b7a1d2e90c5f0b9fb62970fb3bac89ec3;
  torch-ascendc-op-extension, direct-invoke template, precision/pipeline/API
  guidance were read. CMake preserves CANN template notices (LICENSE-CANN).
  Kernel arithmetic provenance retains Huawei attribution (LICENSE-APACHE).
  This implementation is hand-adapted algorithm code, not an unmodified
  "Cannbot-generated" artifact. No 950/arch35 kernel is substituted on 910B4.

Independent namespace, explicit library path and opt-in integration; never
override all vendor operators or modify the original runtime/image.

# QQQ W4A8: Qwen3.6/Ascend applicability gate

Date: 2026-09-28 UTC. This record now includes source/history audit and
physical-NPU4 native A8W4 numerical and local operator-sequence screens. It is
not a calibrated QQQ candidate, service benchmark, or task-quality claim. The
one-day per-paper rule bounds further work.

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
INT4 weights and per-group antiquant scales. The pinned source explicitly says
`activation x is not quantized`; the native operator is weight antiquantization
plus BF16 matmul, **not** QQQ's INT8-activation/INT4-weight GEMM. Do not infer
arithmetic from the `W4A8_DYNAMIC` label. Source SHA256:
`bae32ab026ebe12de1f74a3323d1d19114166dd1110dcfa4bf6320434edf3089`.
No `qqq` scheme is registered in the pinned vLLM-Ascend source.

Historical non-QQQ msModelSlim AWQ W4A8 checkpoints exist under
`/cache/cch/qwen36-awq-w4a8-20260923/`. A physical-NPU4 batch-16
native packed-INT4 eager/graph ABI probe passed; a real layer-3, 5120-to-12288
group-128 probe reported ~0.117 relative RMS against BF16 on two inputs.
Those are **intermediate** observations, not task accuracy. `quantized-awq-v4`
contains only incomplete shards and must not be treated as a loadable model.
The older `quantized-awq-v3` also cannot be launched unmodified as a QQQ
candidate: its global `group_size` is 0 while pinned v0.23 divides the input
width by that value, and its real `scale_bias` shape does not match the v0.23
linear loader's `[output,1]`/`[output,16]` ABI. It is non-QQQ AWQ in any case;
repairing it would not demonstrate QQQ. No four-card service was launched from
this checkpoint in the present workstream.
The previous W8A8/SmoothQuant client-only throughput JSONs in
`KV_QUANT_REUSE_GATE.md` are screening clues, not matched acceptance results.

## Physical-NPU4 native W4A8 repeatability gate (2026-09-28)

The owned one-card container mapped physical `/dev/davinci4` to container
`/dev/davinci0`; `npu-smi` showed NPU4 idle before the one-shot run. The
immutable v1 result is
`/cache/cch/qwen36-qqq-native-substrate-20260928-v1/native-substrate.json`.
Its SHA256 is `b1de6164d2789551fb6de6db4e7235ced8cbadf4cf9278671d8c11c32605d69d`.
At M16/K5120/N8704/group128 the native packed-INT4 call returned finite
values and 0.001342889 relative RMS versus a BF16 dequantized matmul, but
failed a predeclared bitwise graph/eager assertion. No timing was produced.

The separate non-overwriting diagnostic
`/cache/cch/qwen36-qqq-native-substrate-20260928-v1/replay-envelope-v2.json`
has SHA256 `23010fc2bfd3faecf0aae522873692ac559553527261edbd5eca0a1806e9f913` and
isolated the source of that difference. Native W4A8 eager repeat differed in
5/139264 elements (relative RMS 4.742e-6); graph repeat differed in 3
elements (1.897e-5); graph versus eager for fixed input differed in 4
elements (1.897e-5). Maximum absolute difference across these comparisons
was 0.0078125. The BF16 dense control was bitwise identical in all four
repeat/graph comparisons. Thus v1 did **not** establish a graph-specific
fault: this native quantized operator itself varied between identical eager
calls. The observed two-run envelope is a diagnostic, not a universal
tolerance, QQQ model result, E2E gain, or task-accuracy result. Preserve the
v1 failure; do not relabel it passed or silently relax its frozen assertion.
The owned container was stopped after this earlier v2 and resumed only for the
separate true-A8W4 v1-v5 tests below.

## True A8W4 native route and the 2026-09-28 physical-NPU4 decision

CANN 9.1's `aclnnQuantMatmulV5` is present in the deployed `libopapi.so`, and
the installed `torch_npu 2.10.0.post4` exposes `npu_quant_matmul` with INT8
activation and INT32-packed INT4 weight inputs. This is the relevant existing
primitive, unlike `npu_weight_quant_batchmatmul`. The native API documents
per-channel A8W4 and a K-group mode fixed at 256, so the tested path is QQQ's
per-channel variant, not its group-128 variant. The official contract is:
https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/aolapi/context/ops-nn/aclnnQuantMatmulV5.md .

The owned one-card container used image
`sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`
and mapped only physical NPU4 to container device 0. Before each run, NPU4
had no running NPU process. All files below are immutable, unique results
under `/cache/cch/qwen36-qqq-native-substrate-20260928-v1/`:

| File | SHA256 | Evidence |
| --- | --- | --- |
| `qqq-a8w4-v5-20260928-v1.json` | `cb8453caa0293ca6167910eb0cea6025c3b777e526448211ec682dd191f0f8af` | First call versus independent FP32 oracle: 0.000407 relative RMS; same-input second call and graph replay fail badly. Frozen gate failed. |
| `qqq-a8w4-v5-replay-20260928-v2.json` | `cb04db1ac5fc2be6f415a866d961b19f5189aceb2f56f8fc89d8c393c2168ede` | Explicit synchronization did not fix it; the native call mutated its INT8 activation, at both N=512 and N=8704. Other inputs were unchanged. A pristine buffer restored the first-call result. |
| `qqq-a8w4-copy-guard-20260928-v3.json` | `b79e0d1c9695667a7a0eec6c3cbe2035e1e95b6b96669c4d78cf85b45a321246` | With a disposable activation copy, eager repeat, graph repeat, and graph/eager were all bitwise identical at M16/K5120/N8704; source activation stayed unchanged. The raw call changed 81,033 of 81,920 activation elements. |
| `qqq-a8w4-dynamic-20260928-v4.json` | `0a2d535732c8373c96b69e1b3879d11c68c6531f707580771cf80ad207187321` | Native per-token dynamic quantization feeding V5 passed the numerical/graph gate without mutating source BF16. Relative RMS versus the quantized arithmetic oracle was 0.000265; versus BF16 dense output was 0.009177 (intermediate, not task accuracy). Local eager sequence was slower than BF16: median 0.116445 vs 0.090438 ms. |
| `qqq-a8w4-graph-cost-20260928-v5.json` | `4abfde2935cbc941325252b94f408ad34b76d1ac164b57f9280e1c607ae9337c` | Same-run graph replay screening: M16 median 0.066519 ms A8W4 versus 0.058817 ms BF16; M256 median 0.175036 versus 0.140695 ms. Both graph numerics and repeats passed. |

**Decision:** reject this *existing per-channel native V5 dynamic pipeline* as
a current-service investment: it is locally slower at the observed decode M16
shape and a larger prefill M256 shape, before QQQ calibration and plugin
overheads. These event timings are not critical-path or matched E2E throughput,
and cannot reject the QQQ paper, alternative fused operators, other shapes, or
a memory-constrained workload. No QQQ model, checkpoint, opt-in service plugin,
matched BF16/candidate E2E comparison, LongBench-v2, or GSM8K result exists.
The user's permitted 1% task-accuracy loss is not an intermediate-tensor gate.

## Next bounded decision

1. Do not spend a model-calibration day or four-card service launch on this
   slower V5 sequence. A *different* A8W4 fused kernel is justified only if
   its full dynamic-quant-plus-GEMM path first demonstrates a substantial
   shape-matched graph advantage over the same BF16 control, with exact input
   preservation and numerical/graph parity. Reuse CANN/CannBot/open-source
   code where it implements the QQQ-specific need; do not optimize unrelated
   matmul work and call it QQQ.
2. If that investment gate is met in a later bounded loop, implement
   independently named, opt-in QQQ selective smoothing plus Hessian/GPTQ
   compensation and model loading, then run actual TP4 service and final
   task-accuracy gates. Otherwise move to the next paper mechanism.

# MXR-only v0.23 thin-backend preparation (source audit, NOT ready)

Prepared 2026-10-13 from read-only historical source and raw-result inspection.
No NPU, container, framework edit, backend installation, or model run occurred.
Fixed current window ends 2026-10-13T08:06:34Z; this document does not renew it.

## Finding that changes the next action

MXR was never integrated into the current Qwen3.6 service. The old workstream
stopped on an opportunity estimate derived from a Qwen3.8 service profile. The
current Oct6 inventory explicitly withdraws that estimate as a Qwen3.6 no-go.
The old local numerical/timing results remain valid at their recorded scope:
3.158x / 3.140x triangular inversion at 4096 / 16384 tokens, and chained
FP16-input output/state/repeated-input checks. Those checks do NOT validate
the actual service's FP32 triangular matrix or current graph/lifecycle path.

## Immutable source anchors

Reference vLLM-Ascend tag v0.23.0 resolves to
`5cb98caaadeff42b5b62b996e34bb2aaa29d20fd` in
`/cache/austinov/src/vllm-ascend`.

| Source | SHA256 |
| --- | --- |
| `vllm_ascend/ops/gdn.py` | `d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816` |
| `vllm_ascend/ops/triton/fla/chunk.py` | `6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5` |
| `vllm_ascend/ops/triton/fla/solve_tril.py` | `2d8cd5d3bd365fa5894c7ee0cddc106d1d2b34dd3f3e05f4dbf15e8010d89fc0` |

These are hashes of exact Git blobs read during this preparation, NOT a fresh
claim about a running worker's imported code. Before installation, the same
source/active-callable identity must be proved inside every real TP4 worker.

Official MegaGDN revision `d357fd38608f99ddf9b9fb2d217b2e731ecd3a72` is under
`/cache/cch/paper-sources/mxr-tri-inverse-20260918/extracted/megagdn-pto-d357fd38608f99ddf9b9fb2d217b2e731ecd3a72`.

| Official source | SHA256 |
| --- | --- |
| `megagdn_pto/fast_inverse.py` | `3f0049160d846800a51669c0eb9be36058ac02edea2100f2bf99c6599714c722` |
| `megagdn_pto/compile.py` | `23bbe505d415e1e9992cb7e7686046da07fedde00b3831c64309be285cb9bfd4` |
| `vllm_patch/chunk_gated_delta_rule.py` | `6ec625ef4f672e5b191cd372ae2cabd04c259c4c510f206037d6e0b5f684e469` |

The retained MXR plugin scaffold is on Git branch
`work/mxr-qwen36-ascend-piercing-20260918`, tip
`b2414a5397b58285099507bc8f47e8a798da8894`, under
`projects/mxr_vllm_ascend`. Only config/runtime/install scaffolding exists;
its `MST_MXR_BACKEND_MODULE` expects an exported `chunk_gated_delta_rule`.
There is no delivered backend satisfying that requirement.

## Actual reference call chain and minimal seam

`AscendGatedDeltaNetAttention._forward_core` uses a dedicated native recurrent
operator for decode. For prefill it obtains/transposes/clears initial state and
calls the imported `gdn.chunk_gated_delta_rule` with `prebuilt_meta`, varlen
boundaries, `output_final_state=True`, and Q/K normalization enabled.

The exact `chunk_gated_delta_rule_fwd`:

1. Computes chunk-local cumulative gating with chunk size 64.
2. Calls `chunk_scaled_dot_kkt_fwd(..., output_dtype=torch.float32)`.
3. Calls its module-global `solve_tril(A, cu_seqlens,
   chunk_indices_large_block, chunk_indices_bt, output_dtype=k.dtype)`.
4. Preserves the existing W/U and AscendC state/output stages.

The narrow MXR-only implementation seam is this module-global `solve_tril`
binding, NOT replacement of all six GDN stages. A process-local, explicitly
opt-in patch can preserve original chunk/state/control code and substitute only
that binding after source and active-function identity checks. Patching the
separate solve_tril module alone does not replace the callable already imported
by chunk.py. The scaffold's whole-chunk replacement API needs a deliberate
small install adapter; do not satisfy it with an unrelated MegaGDN wrapper.

Native solve computes `(I + A)^-1`; A is strictly lower triangular. It accepts
BT16/32/64, but the actual reference service seam uses BT64. Output dtype must
remain exactly the original request, not be assumed FP16.

## Do not hide the precision delta

The official MXR ABI consumes FP16 A and writes FP32 workspace; its convenience
solve wrapper then returns FP16. The service seam supplies FP32 A and requests
BF16 for the current model. Therefore naive `A.half()` plus output BF16 changes
the rounding contract. The previous FP16 synthetic test does not cover this.

Before any service candidate: capture source-bound actual FP32 A, lengths and
dtype from the deployed seam, retain the original output, compare against an
independent FP64 `(I + A)` inverse, and run a diagnostic three-way comparison:
original native / independent reference / explicit FP32->FP16 MXR route. Keep
the existing numerical gate unchanged. If conversion fails it is an adaptation
issue requiring an FP32-input/mixed-precision MXR repair, not task-tolerance
relaxation and not proof that the paper is ineffective.

## Support and fallback contract to implement

| Dimension | MXR-only adapter decision | Full MegaGDN distinction |
| --- | --- | --- |
| Activation | Default OFF; no imports/allocations/hooks when OFF. Explicit new ON mode after source checks. | Separate candidate name and experiment. |
| BF16 model | Keep native Q/K/V, normalization, state and output stages. Qualify FP32 A conversion separately. | Official wrapper converts Q/K/V/beta to FP16; additional error/traffic. |
| FP16 model | Still receives FP32 A from native KKT; not automatically qualified. | Whole FP16 chain already has limited local evidence. |
| Initial state | Solve itself has no state parameter; preserve original later state calculation and test nonzero multi-step state. | Official whole wrapper falls back for nonzero state. |
| Variable lengths | Preserve original boundary/order/tail semantics. Need actual metadata validation; reject/fallback unsupported empty/irregular boundaries. | C128 vs native C64 and wrapper metadata handling are separate changes. |
| Graph | Unqualified. Cold-bind stable buffers and CPU-precomputed source-qualified metadata; no `.item()`, tensor truth testing, allocation or host sync in captured candidate path. | Official wrapper includes tensor-dependent fallback and stage syncs; not graph-ready. |
| Unsupported paths | Exact original callable and unchanged args; count fallbacks. A successful all-fallback run is NOT candidate validation. | Same rule, separately scoped. |
| PCP/unknown shapes | Initially original path until separately covered; no global reinterpretation of state. | Official whole wrapper falls back for PCP >1. |

The official `_solve_tril_num_matrices` calls `.item()` on device data; it
cannot be used unchanged inside graph capture. Do not fabricate current host
metadata. Bind against actual `prebuilt_meta`/builder behavior before coding
the graph-safe thin route. Per-layer context must not leak across requests.

## Binary reuse without rebuilding a wheel

The following existing binary was rehashed and matches its original manifest:
`/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v11/compiled/tri_inverse_jit_MEMORY_BASE.so`
SHA256 `1a518ef0603d266d3d62218d0a30a97e14618a7657faf6ab586f417ca59267af`.

The exact old environment was Ascend910B4, MEMORY_BASE, Python3.12.13,
torch2.10.0+cpu/torch_npu2.10.0.post4. The official compile_tri_inverse reuses an
existing library; the official full chunk/mega compile functions unconditionally
build on their first call in each process. Reusing the triangle library is a
viable preparation input, not a fresh dlopen/ABI/NPU qualification. Pin actual
loaded-library identity and exports in the same image before native execution.
Do not run the author's install_hook.py: it edits installed framework files.

## Next exact work and missing evidence

Ready count from this packet: ZERO. There is deliberately no runnable NPU or
service launch command. Historical gate v1-v11 outputs are immutable and must
not be rerun or overwritten.

1. Obtain current installed chunk.py/solve_tril.py and already-active callable
   identities; compare with the exact blob hashes above. Identify any legitimate
   existing patches, rather than forcibly restoring the reference callable.
2. Reuse the existing MAIN-owned capture/runner and source-qualified aggregate
   budget to obtain actual prefill A/metadata. No new generic controller needed.
3. Implement the tiny MXR-only module binding and independent semantic gate on
   a new source identity. First test default-OFF and fallback/identity failures
   without devices in the actual image; then the affected real NPU matrix.
4. Only then actual TP4 worker activation smoke, fixed1024 dense/MXR pair, and
   promising three-run formal pairs. Profile only if needed to discriminate
   integration overhead; never estimate Qwen3.6 rejection from Qwen3.8 trace.
5. Current user task gate: GSM8K, HumanEval, MMLU; smoke before full evaluation,
   thinking OFF, normal EOS, max2048. Freeze dataset/scorer/prompt identities;
   HumanEval generated code needs an isolated execution sandbox. Report both
   task-loss percentage points and relative percentage against the same dense
   control. The allowed task loss is not a tensor-error threshold.

MXR-only and MegaGDN are not interchangeable evidence. A sub-10% verified
gain may be retained for a separately validated combination; gains are not
arithmetically additive. Historical old no-go is preserved, but its withdrawn
cross-model justification cannot block the missing current-model experiment.

# Packed recurrent-state migration: DAMP lessons

Evidence date: 2026-10-06. Workstream:
`.agents/workstreams/qwen36-damp-ascend-20261006/`.
These are engineering lessons, not evidence of DAMP throughput or quality gain.

## Preserve the real runtime before testing the algorithm

- Same-image tests must use the actual tokenizer/API version. Transformers
  5.5.4 `apply_chat_template` defaults to BatchEncoding; request
  `return_dict=False` and validate integer token IDs. Converting an arbitrary
  mapping to a list can silently use its field names instead of token IDs.
- `VLLM_PLUGINS` filters platform plugins as well as general plugins. Preserve
  the source-verified Ascend platform and required model/loader/runtime patches
  in both control and candidate. Do not use a candidate-only whitelist that
  filters out `ascend`. Keep profiling disabled for formal timing.
- Split NO-device preparation from device-dependent checks. Activating the
  platform is inspectable without NPU, but FLA import can query Triton's SoC,
  and native-op loading can also require SoC discovery. Read frozen source
  hashes in static preflight; require real library/schema/dispatch proof on
  inspected device mappings. Do not substitute a mock or claim static pass
  proves loaded ABI. Retain failed preflight logs and change the action based
  on their exact traceback, rather than repeating unchanged failures.
- Python imports can print warnings on stdout. CMake metadata discovery must
  check the process return code, extract an explicit marker and verify the
  selected Torch/torch_npu headers/config/library paths. Complete stdout is
  not necessarily a filesystem path.
- Contiguous is not proof of physical ND format on Ascend. Validate the real
  torch_npu physical format before raw-pointer kernels. Reject unsupported
  formats; any explicit conversion belongs outside capture and in both arms.
- A header declaration does not prove a dynamically exported ABI. The real
  v3 library failed load on FormatHelper::GetFormat even though its link line
  and DT_NEEDED already included libtorch_npu.so. Audit the deployed ELF, not
  just linker flags. The same-version public TORCH_NPU_API
  custom_ops::get_npu_format was exported; using it preserved the ND gate and
  v4 compiled/load/schema/Meta passed. This is still not NPU numerical proof.
- Pure text in a multimodal-capable model need not have 1D positions. Qwen's
  source-proven MRoPE branch broadcasts three text rows with zero delta.
  The collector v2 rejected non-1D positions at first forward; it had not
  logged the actual shape. Repair bookkeeping only after proving identical
  rows, pure token requests, zero delta and agreement with CPU request order.
  Preserve the original native tensor/arguments; never blindly flatten.
- Read sequence metadata from the actual backend builder. This frozen Ascend
  one-token decode ABI is [0,1,...,1], not cumulative [1,2,...,B].
  Test metadata gates against the pinned producer before loading a model.
- Check keyword-only boundaries of the actual Torch schema, not just tensor
  order or argument count. Native recurrent Q/K/V/state are four positional
  arguments; beta/scale/lengths/indices/g and other optional arguments are
  keyword-only in this image. Restricted gate v1 failed at that binding before
  either recurrence ran. Keep it as a harness failure; require schema/call
  signature tests before a corrected new run, never label it a numeric no-go.
- Immutable inference images may lack preparation-only Parquet libraries.
  Preflight those dependencies; install an exact hash-pinned wheel into an
  external isolated target, not the original runtime/image. Strict TLS and
  upstream size/SHA remain mandatory when using a faster public mirror.
- A platform patch may copy function objects onto the real model class rather
  than use inheritance. On frozen v0.23, patch_qwen3_5 copies Ascend GDN methods
  onto QwenGatedDeltaNetAttention; later donor-only patching left the receiver
  unchanged. Collector v3 reached the model but observed zero GDN hooks and
  failed exact48 coverage. Audit the constructor, copier and dispatcher; bind
  the verified receiver too, and prove all actual instances' owning functions
  before the first real model call. Do not clear a failed turn to hide coverage
  failure. Software alias tests are still not live capture proof.
- Pure-text request admission must be checked at the request boundary. A
  multimodal-capable native model may legitimately preprocess text into
  inputs_embeds; rejecting that tensor alone misclassifies ordinary text.
  Inspect request media/prompt-embedding fields and actual token masks, and
  keep unsupported encoder/model kwargs fail-closed.

## Source-bound identity and diagnostic tooling

- Client request IDs need not equal worker IDs. In this pinned vLLM image,
  add_request returns an internal randomized ID while RequestOutput exposes
  the external ID. Observe the original engine-instance return symmetrically
  in both arms; preserve the original arguments and return object. Never
  guess identities by stripping suffixes. A source-bound audit of the original
  stopped v4 container recovered its complete TP4/48-layer smoke capture and
  exact output parity without rerunning the model or editing the failed report.
  This is collector evidence, not compressed-state or service acceptance.
- A raw-pointer diagnostic must validate its own new output allocations, not
  just inputs. The v1 trace's default four-dimensional FP32 at::empty output
  failed physical ND validation before kernel launch. Use the deployed public
  format-conversion ABI when appropriate and keep the physical-format guard;
  declaring ND in factory options alone is not proof of the returned layout.
  Diagnostic conversion costs cannot enter a performance claim.
- Regex synchronization audits may miss helper-call boundaries. Retain the
  original red findings, inspect the exact SetFlag/WaitFlag helper, and use
  an external expanded-source snapshot only as a crosscheck. A zero-red
  expanded scan is not compiler, device ordering or numerical proof.
- Inspect static-auditor side effects before use. This Cannbot scanner rebuilt
  a missing sync_cases.db in its reference tree. For future missing-cache runs,
  use an isolated tooling copy/result directory rather than quietly writing
  into the original reference repository. Do not erase the observed side effect.

## Preserve slot lifecycle and isolate arithmetic from quantization

- Requantize only selected request slots. A reference implementation that
  unpacks and repacks the full arena can change untouched FP32 scales by a
  ULP even with identical INT8 codes. Check each untouched high/code/scale
  region bitwise after every step, not just final output or selected state.
- Independent oracles must declare reduction/FMA/constant lowering. DAMP CPU
  v2 B1 passed eight steps, but B16 failed the preregistered `1e-5` state gate
  at step2 despite correct untouched-slot behavior. Exact fixture replay
  showed only `2.790e-8` same-before prepack max-head relative error, yet two
  INT8 codes crossed half-integer boundaries. The threshold was not relaxed
  and this run remains failed; it does not prove the paper cannot work.
- For such failures, save expected/actual before-state and updated FP32 state.
  Replay the same before-state to separate lifecycle drift, reduction order,
  quantizer lowering and feedback propagation. Validate quantization on
  identical inputs, including half ties, one-ULP neighbors, zero groups,
  finite extrema and underflow. No NaN/Inf is not correctness proof.
- Algorithmic compression drift versus dense is distinct from implementation
  parity against the same compression algorithm. Neither is the user's task
  accuracy allowance. Final GSM8K/LongBench loss must be measured separately.
- A real packed cache has only declared mixed-precision regions; no persistent
  FP32 sidecar. Temporary diagnostic FP32 state must be explicit, short-lived,
  disabled in normal decode, and excluded from performance claims.
- Restricted native golden v2 matched complete packed state for44 steps, then
  failed B1 identity step45: one INT8 code changed from-118 to-117 while FP16
  payload, scales and current output remained exact. Its state max-head
  relativeL2 was1.3174993668816764e-4, exceeding the frozen1e-5 gate. Saved
  native updated state independently repacked exactly. Actual NPU saved-step
  trace v2 later proved the complete updated FP32 state bitwise identical to
  native, superseding the CPU FMA update-rounding hypothesis for this fixture.
  The actual quotient was -117.49999237060547 (0xc2eaffff), versus IEEE FP32
  -117.5 (0xc2eb0000), causing RNE -117 rather than -118. Target the quantizer
  division seam; do not change the native update or the frozen gate based on
  the superseded hypothesis. One saved-fixture attribution is not closed-loop,
  general-SR, graph or service acceptance. Retain original failures and traces.
- Exact quantizer compatibility means the declared FP32-division-then-RNE
  semantics, including double rounding around half-integer boundaries. Do not
  make all near-half quotients ties to hide an approximate-division difference.
  Verify the deployed architecture's API support before selecting a precision
  mode; an API present only in another SoC branch is not an available repair.
- Power2-SR tests cannot validate a plan accepting arbitrary positive FP32
  scaling. Casting V/c to BF16 before native recurrence or multiplying a
  native BF16 readout by c adds rounding absent from the production algorithm.
  Use a separate source-bound FP32 oracle for general SR and final plans;
  anchor it to the actual native operator first. Candidate diagnostic traces
  locate failures but are not independent correctness oracles.

## Resource and portfolio audit safeguards

- Parse live npu-smi output against an actual saved snapshot before resource
  mutation. This host combines NPU/Chip in one process-table pipe column;
  treating them as separate columns produced an empty ownership set. The
  fail-closed release guard stopped before signals. A snapshot-tested parser,
  exact cgroup/cmdline/ancestor proof and PID handles then released only the
  external physical4 evaluator subtree, preserving its broad privileged
  container and protected0-3. Device declaration alone still is not a conflict.
- Do not upgrade opportunity screens, source overlap, output-preserving shadow
  diagnostics or expired attempts into complete-paper rejection. Reconcile old
  portfolio labels against later implementation branches and raw artifacts.
  Verify the adjacent profiling launch model: a Qwen3.8 trace cannot establish
  Qwen3.6 service opportunity. Preserve valid local operator evidence while
  withdrawing the unsupported full-model conclusion.
- A human portfolio deadline does not change numerical thresholds or make an
  untested result accepted. Reserve final timing/task-evaluation capacity; list
  missing evidence as missing at cutoff. Parallel preparation does not permit
  concurrent competing NPU workloads during TP4 comparisons.

## Evidence and next stage

Raw evidence roots (external to Git):
`/cache/cch/qwen36-damp-20261006/smoke-hook-v1-launch/`,
`independent-packed-cpu-smoke-v1/`, `independent-packed-cpu-smoke-v2/`,
`independent-packed-cpu-diagnostic-v1/`,
`independent-packed-cpu-diagnostic-v2/`, and `operator-build-v1.log`.
The v2 failure fixture SHA256 is
`e6f50b1245f88aa4802ec3dfb5c58159473dc3ac57cb8f490c563230c43dce2a`.

The required next evidence remains actual mixed-state NPU correctness,
changed-input graph replay, real cache-manager allocation, matched E2E timing,
and task accuracy. Passing preparation, a collector hook or build is not
passing this chain. Preserve the current paper's 24-hour decision deadline.

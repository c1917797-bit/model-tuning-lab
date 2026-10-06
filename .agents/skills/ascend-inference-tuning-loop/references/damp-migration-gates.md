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

## Additional scoped preparation lessons

- Retain raw outputs, full state and every input-after snapshot before an
  assertion can reject physical format, finite values, aliasing or corrupted
  payloads. Otherwise the first useful device failure can destroy its own
  attribution evidence. Nonalias checks use complete live byte intervals,
  not merely different data_ptr values; require stable pointers as well.
- Validate an independent reference before the candidate. An explicit
  anchor-only mode can exercise native/FP32 reference parity without rerunning
  a known-failed compressed implementation. Candidate traces are not its oracle.
- A no-device ASC compile and successful load/Meta proves only that scoped
  build/registration path. The quantizer passes these actual checks here, but
  physical SoC, ND allocation, synchronization, multi-step and graph correctness
  remain separate NPU gates. CPU exact-bit counts never substitute for them.
- A static early-return warning needs paired-event control-flow inspection:
  skipping both SetFlag and WaitFlag differs from returning after SetFlag and
  leaving an orphan wait. Preserve original findings and the manual rationale;
  neither a quiet regex scan nor this rationale proves real device ordering.
- For DAMP RN32 division followed by integer RNE, an integer-only endpoint
  certificate can avoid assuming a FP32 vector Mul rounding/FTZ contract.
  Strict interior acceptance, safe0/127 clamps, valid normal endpoint domain
  and exact fallback are mandatory. Twelve-bit product-limb carries must stay
  integer because intermediate values can exceed2^24. Independent software
  checks found no unsafe acceptance; actual SIMD source/ASC/NPU gates and
  end-to-end cost still remain. Keep this draft disabled in production.
- Budget real CANN implementation temporaries as well as explicit queues.
  Four-argument Broadcast on this dav-c220 path pops a shared LCM stack buffer;
  a sum of authored UB allocations alone is not a complete kernel UB proof.
  Audit that hidden path and actual producer/consumer barriers before deployment.

## Actual no-device failures and interface evidence, 12:53Z

- An ASC device-only header may reject the host compilation pass. Preserve
  that failure and the source bytes; keep device-specific includes behind the
  verified SDK boundary without removing the actual target-architecture guard.
  However, guarding the entire annotated kernel definition and leaving only
  a host prototype is not sufficient: integer-certificate v2 compiled/linked,
  but actual dlopen failed on its kernel symbol. Actual nm/readelf found that
  symbol undefined in both the ASC object and shared library. A shared link
  can permit unresolved symbols. The next narrowly changed launcher must
  retain its host-visible definition, prove the actual exported symbol, and
  pass real load/schema/Meta before any NPU attempt. Do not mark that proposed
  repair passed before compilation and load.
- Bind actual compiled dependencies separately from runtime tests/oracles.
  This probe has nine compiler dependencies and sixteen runtime dependencies;
  their intersection must match, with missing/extra/drift identities rejected.
  Do not demand that a genuine compiler receipt use an invented runtime schema.
- Check deployed component version files rather than guessing SDK filenames.
  The two version.cfg guesses were absent; actual OPP version.info proves
  OPP9.1.0 bytes only. Build target dav-2201 is not a runtime SoC observation.
- Device dispatch failure and a later poisoned-context D2H failure are distinct.
  Save CPU input-before/golden, original dispatch error and independent copy
  errors before assertions; nullable unavailable returns are not a pass.
  Failure-save simulations validate this harness behavior, not NPU execution.
- KVBuffer parallel-fold actually compiled and passed no-device load/schema/
  positive Meta plus software checks. Its explicit Broadcast scratch avoids
  relying on the hidden LCM path, but neither this change nor Meta proves
  real UB safety, numerical recurrence, graph replay or serving benefit.
  Candidate auxiliary storage must reduce its KV budget rather than receive
  extra memory unavailable to the same dense control.

## Actual compaction compiler compatibility, 13:23Z

- On this pinned CANN9.1.0/dav-2201 toolchain, constexpr std::array storage
  still invokes a host-only operator[] from device code. Compaction build-v1
  failed before deployment. A plain constexpr C array preserved all guard
  values while avoiding that unsupported method; do not remove sentinel gates.
- This device Duplicate implementation rejected uint8_t. The packed-mask
  buffer is32B-aligned and256 bytes: clearing64 uint32_t entries preserves the
  exact byte domain. Do not assume that all other SoC/type combinations share
  this restriction or replace mask semantics without equivalent byte proof.
  Preserve both first-failure logs and byte-exact source archives.
- Actual compaction v2 CXX/ASC/link/exported-symbol and no-device load/schema/
  Meta checks passed MA0346/0358. Compiler8 and runtime13 identities match
  their real receipts, including external frozen helper/oracle. Eighteen
  separately recorded Meta negatives were rejected. None exercises NPU
  GatherMask count/order, exact fallback/scatter, guards or changed buffers.
  Device arithmetic, production feedback, graph, E2E and tasks remain pending.

## Actual NPU seam repair and missing-arm recovery, 14:06Z

- Separate source correctness, successful build/export, actual load/Meta,
  isolated NPU components and combined production feedback. Here49NPU
  compaction cases and721integer-certificate cases passed, then the new full
  production operator repaired the exact saved-step45 bitwise. That is real
  device progress, not yet160step/general-SR/graph/cache/E2E/task acceptance.
  Stress-fixture accepted-lane counts must not be presented as real fallback
  frequency or speed. Detailed receipts are in the candidate ACTUAL_GATES.md.
- Reuse public APIs and actual same-image implementation/lifetime evidence.
  The five-argument Broadcast reused dead existing scratch with unchanged
  arithmetic and removed a particular hidden-LCM assumption; it did not prove
  compiler stack or universal UB capacity. Keep unchanged helper/golden bytes
  and record the narrow source-contract exception instead of broadening it.
- A compile const-pointer error and missing snapshot mount are implementation
  or harness failures, not algorithm no-go. Preserve each failed build and use
  a fresh output for the evidence-supported repair; don't rewrite an incomplete
  receipt into success or rebuild merely to satisfy an invented receipt schema.
- Full native capture completed its off36 reference outputs, then failed the
  fresh ordinary-RAM admission before on. Preserve and source-bind that valid
  arm; prepare an on-only recovery rather than rerun hours of unchanged off.
  Admission estimates, model CPU private peak, shared/reclaimable cache,
  Python collector residency and disk anchors are different quantities.
  Do not reclaim shared HugeTLB, interfere with protected workloads or lower
  memory/numerical gates merely to meet a deadline. An unavailable full pair
  remains missing evidence, not paper-wide impossibility.
- Keep small isolated probes distinct from full-model admission. The8GiB
  diagnostic containers could run safely while the full capture's64GiB gate
  was unmet; their actual scopes exclude model/performance claims. Use such
  tests only when they directly eliminate the latest paper-specific blocker,
  then return immediately to the service evidence chain.

## 14:28Z production feedback passes, not task acceptance

The repaired independent production namespace passed four restricted640steps
and four synthetic general-positive-FP32640steps on real physical NPU4;
six independent native/reference160step anchors additionally matched bitwise.
Detailed reports/hashes live in production_integer_compaction_v1/ACTUAL_GATES.md.
The state/output error0 in these scoped gates is NOT zero GSM8K/LongBench loss
or a performance result. Final calibrated plans, prefill import, changing graph,
typed-cache lifecycle and actual scheduler B2..15 remain separate obligations.
Do not use max_num_seqs16 when only B1/B16 have been admitted, or relabel a
max_num_seqs1 eager service screen as the formal concurrency16 result.
Transport route/target success does not prove a remote mutation succeeded:
inspect the action result.ok/applied too. A malformed JSON patch was refused,
fresh readbacks proved no edit, and only corrected plus-prefixed lines applied.

## Shared-arena cache ABI is a separate real gate

Do not infer serving ABI from separately allocated operator fixtures.
Here the real Mamba allocator creates disjoint typed contiguous SoA views
of one raw backing allocation, but the conservative production wrapper
rejects shared whole storage. Source-correct operator and scoped eager passes
can coexist with this real integration blocker. Target an independently
named wrapper byte-interval adaptation, with ND/contiguous/alignment/bounds,
shared-arena sentinels and lifecycle gates; do not bypass the actual allocator
with hidden state copies or mutate frozen binaries/receipts.

## 16:29Z prefill preparation: real compiler proof and remaining device gates

- Freeze a complete next-stage packet before devices become available: exact
  source/compiler/runtime identities, real build/load/schema, command bindings,
  output non-overwrite checks, independent golden, changed-buffer protocol,
  resource admission, deadlines and failure attribution. This means executable
  preparation, not a promise that a new algorithm will pass first time.
- Freshly allocating each changing fixture does not test cached pointer reuse.
  The supplementary float probe keeps three guarded input roots/views fixed,
  prepares once, and changes each input column20 times with8 repeated reads
  per turn. Initial prepare must use different contents from turn0; otherwise
  a supposed20-change test covers only19. Check CPU fixtures before H2D.
  Eager changing buffers still do not prove graph capture/replay correctness.
- Test compiled and runtime contracts against the actual receipt schema. The
  float probe compiled9 and selected pack compiled11 actually built/exported/
  loaded in isolated no-device containers. Selected Meta32 positive/44 negative
  calls passed. These facts do not prove ND allocation, numerical packing,
  native-prefill parity, shared-cache lifecycle or E2E/quality acceptance.
- Cold plan contents need explicit immutable authority. Inference tensors can
  lack a version counter; accepting version=-1 is not mutation detection.
  Pointer stability alone cannot prove Pk/Pv/SR contents stayed unchanged.
  Keep source/plan hashes, retained ownership and an immutable installation
  contract; require device status and lifecycle gates before serving.
- Selected pack numeric failures may leave prior groups/heads already written.
  Wait for all status words/guards and retire the complete selected-slot owner
  after any failure. Do not feed partial state to decode or fall back/retry on
  it as though the write were transactional. Preserve raw states before asserts.
- Inspect the actual CANN tooling CLI instead of assuming flags from a skill.
  The flow analyzer rejected --frontend auto; its original failed receipt stays.
  A separately recorded corrected invocation ran without that flag. Retain all
  seven raw synchronization candidates from the companion scan. Helper V_S
  Set/Wait pairs and returns before either side can explain scanner candidates,
  but zero flow findings/manual source rationale do not prove device ordering.
  UB-copy lowering at metadata/scalar seams still needs actual API/device proof.
- A surrounding verifier can fail after its component tests pass. Record both
  scopes and the actual exit code: MAIN96 software tests passed, then a harness
  invented a common launchable field for a dry-plan CLI and exited1. Correct
  the verifier against that CLI's frozen actual schema in a separate check;
  do not rewrite the first receipt as success or rerun unchanged numerical work.

## Pre-device evidence and native type seams, 16:56Z

- A saved before-trajectory must be an independent clone, not a reference to
  the buffer that selected-update later mutates. Here the clone existed but
  fixture construction used the mutable original. Execute the actual fixture
  assignment in a behavior regression; helper mocks/source-token checks alone
  had missed it. This was repaired before NPU, not a numerical failure.
- Publish the original dispatch exception into the CPU evidence record before
  any after-copy or pointer query. Pointer/stride queries may fail separately:
  record them as nullable independent errors, refuse healthy status, and retain
  the original cause. Software poisoned-context regressions do not prove NPU.
  CPU before snapshots are not a durable pre-dispatch disk journal; state the
  crash-loss boundary rather than promise evidence survives a process kill.
- Identical Python source hashes do not imply identical class objects when
  importlib loads the contract under different aliases. A receiver enforcing
  isinstance must share canonical Turn/Leases authority with its producer.
  Verify actual constructor/copier/allocator order and test the real module
  interoperation. The current new assembly repair is pending, not accepted.
- Distinguish CPU-derived scheduler metadata from actual device metadata.
  A diagnostic compare may admit checked correctness only; it is not a formal
  no-hot-D2H policy or throughput result. A B1/B16 native-prefill packet cannot
  authorize intermediate P2–15, mixed48-layer service, graph or final192 plans.
  Keep those obligations explicit instead of upgrading status-only reports.

## Pre-mkdir failures and exact execution readiness, 17:20Z

- A failure-evidence writer can itself replace the original error. Inspect the
  actual mkdir/source-admission order, not a presumed order. The frozen float
  gate binds sources before creating output; the NEW wrapper catches only its
  own loaded-map evidence write, records it separately and rethrows the same
  primary exception. Test a truly absent directory, injected IO failure, no
  primary plus failed evidence, and early parse/source-check boundaries.
  Never create a fake report, retry numerical work, or claim durable evidence
  where only raw process stderr/exit exists.
- Source hashing is not a loaded-process observation. A readonly copy from a
  stopped immutable/no-device container can supply real original native SO
  bytes for offline validators. Record its source image/path/inspect/copy
  receipt and explicit reader alias; do not claim the image path exists on
  the host or that this proves actual NPU maps. In-memory software terminal/
  report fixtures remain SYNTHETIC even when real binary bytes are checked.
- Freeze exact expected execution authority before acquiring cards: MAIN's
  original terminal/argv/peer/source identities plus real same-process runtime,
  loaded maps, stage report and raw artifacts. A status-only PASS or JSON
  supplied by a mock cannot substitute actual execution. Component admission
  is not serving/graph/E2E permission; B1/B16 is not all intermediate batches.
- Ready-before-resource covers a complete, runnable and resource-admitted
  matrix, not guaranteed experimental success. Keep a ranked ready queue;
  overlap only independent disjoint correctness jobs after joint CPU/RAM and
  owner checks. TP4 calibration/formal comparison owns the whole authorized
  set. Measure evidence progress/idle reasons, not dummy utilization.

## Resource-complete successor preparation, 17:47Z

- Run the actual successor CLI, source/build/Meta admission and producer-to-
  validator bridge before cards release; label software original-terminal/
  report fixtures SYNTHETIC. Actual binary snapshot bytes are not mapped
  execution. Keep parent, child and original tool receipts independently bound.
- Budget the correctness oracle before scheduling NPU occupancy. Here actual
 10k cold divisions cost~1.014s; a2.64CPUh scalar extrapolation does not include
 NPU/copy/quantization work. Explicit NEW phase budgets, joint ordinaryRAM/CPU
 and unchanged cutoff/cleanup reserve are required; never shrink gates or call
 CPU diagnostic time a performance result.
- Parallel resource admission must be symmetric. One dispatcher recognizing
 another owner does not make the other monitor recognize it. Prove exact
 disjoint devices, real IDs/image/cgroups/quotas and both monitors; do not forge
 owner labels, silently patch frozen guards or add dummy loads to occupy cards.
- A retired/stale dlopen mapping is not the current pathname even if a replacement
 file has the expected hash. Reject deleted mappings and bind actual inode/device;
 state that this still is not proof of every loaded memory byte. Native failure
 must remain primary even when abort/log/stdout/retirement also fails.
- Exact native method AST behavior with stdlib stand-ins checks source seams,
 not real framework lifecycle. HTTP request counts do not prove native P/T,
 pause-cache retention, reset/ABA or whole-model48-layer commit coverage.

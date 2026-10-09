---
name: paper-to-ascend
description: Use when selecting, adapting, or evaluating a research paper as an Ascend NPU inference optimization; gate paper fit before implementation and keep claims scoped to measured evidence.
---

# Paper-to-Ascend

## Purpose

Turn a paper idea into a bounded Ascend inference experiment only when it fits
the installed model, runtime, hardware, and current bottleneck. A paper is not a
task by itself; it becomes a tuning workstream only after its required mechanism
and expected speed path are proven on the target environment.

## Applicability gate

Before opening or resuming a paper implementation workstream, answer these in
Git, usually in the experiment record or branch-local handoff:

1. **Architecture fit:** does the installed checkpoint contain the mechanism the
   paper needs, such as an MTP head, MoE experts, quantization metadata, sparse
   structure, or a compatible attention form?
2. **Inference-time fit:** can the method be tested without retraining under the
   user's current scope? If retraining is required, stop unless the user
   explicitly authorizes that expansion.
3. **Bottleneck fit:** what measured Decode, Prefill, kernel, memory, cache,
   communication, or scheduling bottleneck is the paper expected to improve?
4. **Production path:** does the installed vLLM, vLLM-Ascend, CANN, or
   operator stack already expose a usable seam? Prefer built-in exact paths
   before authoring new kernels or replacing low-level code.
5. **Decision scope:** predeclare whether the first result can support only an
   operator/router, block, service, or full-model claim. Do not promote a narrow
   result into a broader conclusion.
6. **Resource isolation:** reserve concrete NPU IDs, port, CPU/NUMA scope, and
   artifact locations, then prove the live ownership before baseline and
   candidate runs.

If any gate is unproven, the next action is orientation, profiling, source
inspection, or a smaller canary, not implementation.

## Required companion skills

For machine-bound work on `chicaihong01`, use
`chicaihong01-host-maintenance` before touching the target host.

For performance work, also use:

- `ascend-npu-environment-orientation`
- `ascend-inference-tuning-loop`
- `ascend-benchmark-evidence`

When the paper or benchmark touches CANN/operator/kernel/profiler behavior,
HCCL communication, memory movement, or unexplained low-level regressions, also
use `ascend-cannbot-profiler` before changing low-level code.

This skill chooses whether the paper deserves an experiment; the Ascend skills
make the experiment reproducible and evidence-bound.

## Workflow

1. Read `AGENTS.md`, `.agents/HANDOFF.md`, and any active branch-local
   workstream handoff before using host resources.
2. Summarize the paper mechanism in terms of the current runtime: required model
   feature, changed inference stage, expected reduced work, and possible new
   overhead.
3. Prove the applicability gate with live or repository evidence. Record
   unknowns explicitly.
4. Choose one primary variable for the first experiment. Keep unrelated paper
   ideas for later loops.
5. Create or resume one `work/*` branch and one experiment record using
   `.agents/experiments/TEMPLATE.yaml`.
6. Freeze baseline conditions before implementation: model/tokenizer identity,
   dtype or quantization, workload, parallelism, container/runtime versions,
   CANN/driver/firmware, physical NPU IDs, port, and launch command.
7. Measure baseline first. Only then enable the paper-derived candidate.
8. Run correctness and target-device checks before accepting any performance
   result.
9. Decide as `accepted`, `rejected`, `inconclusive`, or `failed`, and record the
   exact scope of the decision plus the next loop.
10. Preserve negative results as pushed history. Recover failed active code
    before integration, but do not erase the evidence.

## Mandatory probe validity before advancement

Before implementation, device admission, result promotion or handoff, read
[the validity/non-drift contract and matched-control DAG](../ascend-inference-tuning-loop/references/paper-validation-dag-and-matched-controls.md).
Freeze immutable experiment identities; prove formula-to-worker-to-NPU
mechanism activation; require independent mathematical correctness, matched
whole-model performance and final task accuracy. Keep failed, inconclusive,
rejected and accepted scopes distinct and preserve an auditable handoff.
At each stage, align the next short-term action with the fixed medium/long-term
goal. This is mandatory for paper probes, not a substitute for actual tests.
After a failed gate, also apply
[root-cause classification and evidence-selected repair](../ascend-inference-tuning-loop/references/failure-root-cause-and-next-action.md).
Repair proved adaptation/test defects before judging the paper. Record unknown
causes explicitly; a timebox closes only the unverified implementation scope.

## Current repository guidance

The current installed target is dense. Do not treat the old Qwen3.5 MTP
direction as active: use the latest user objective, branch-local experiment
record and live runtime evidence to select the paper-specific next loop.
Dynamic MoE and MTP are retained as historical audit exemplars, not current
optimization directives.

This is not a permanent architecture restriction. Dense is only the current
verified target at this handoff. Future MoE, quantization, sparse, multimodal,
or retraining-based work is allowed when the user selects that target and live
environment orientation proves the matching checkpoint, runtime, and resources
exist.

For dense inference, prefer methods such as exact speculative/MTP,
attention/KV/decode improvements, or other inference-time techniques that do
not require retraining unless retraining is explicitly in scope.

## Lessons already learned

- Dynamic MoE showed that theoretically reduced compute can still regress
  end-to-end latency when routing or packing overhead dominates.
- Keep paper, implementation, operator/block, and full-model decision scopes
  separate.
- A service, container, or old benchmark is not a valid baseline after workload
  or resource ownership drifts; re-isolate and re-baseline.
- Saved FLOPs, faster local GMM, or a single warm run is not enough. Accept only
  correctness-first, apples-to-apples repeated evidence.
- For page-sparse attention, distinguish the paper's per-query-head support
  from a backend-driven per-request shared block table. Before commissioning
  a custom per-head kernel, compare both selectors on the same live Q/K/V:
  exact attention mass, selected-output error, and a full-support mathematical
  oracle checked against native attention. A shared-page failure alone does
  not reject the paper, while a per-head selector can still lose too much
  mass at useful budgets. A few layers or one prompt are investment gates,
  never final task-accuracy evidence.
- For a new token-sparse attention paper without verified author code, label
  the implementation equation-derived rather than an official port. On the
  same live Q/K, compare the proposed GQA-pooled selector, a per-head
  diagnostic, and exact-logit Top-K at equal budgets with the same forced
  windows. The exact Top-K bounds the attainable attention mass at that
  budget and separates selector failure from intrinsic budget pressure.
  Validate the transform's dot-product identity and a full-support math
  oracle against native attention before interpreting sparse errors. This is
  only a kernel-investment gate, not end-to-end throughput or task accuracy.
  On Qwen3.6-27B TP4 at one 20K repetitive prompt, the Self-Indexing 5%
  pooled selector retained 55.1% mean mass while exact Top-K retained 73.0%;
  no custom token-sparse operator was commissioned for that scoped route.
- Plugin discovery, plan loading, and patch installation are not mechanism
  evidence. Require an event from the exact live hook carrying request identity,
  runtime geometry, and the selected action.
- Derive cache/page/block alignment from the live runtime after all hybrid-cache
  rewrites. A plan aligned to a static config can be invalid after Mamba and
  attention page sizes are reconciled.
- Read the predicate behind a fail-closed runtime error before launching a
  proposed variant. Error prose can be narrower than the actual condition; do
  not rerun a deterministic failure just because the message names one mode.
- Hybrid-cache papers may require separate lifecycles for attention KV and
  recurrent state. Before reusing another plugin's material cache, prove whether
  it stores both together. If the paper requires dense attention KV but sparse
  recurrent checkpoints, require an atomic publish/commit seam or reject the
  thin-adapter path.
- Do not infer checkpoint count or mechanism activation from an ambiguously
  named counter such as placements. Trace the producer and record the semantic
  unit (requests, rows, blocks, or checkpoints).
- For stateful cache/replay methods, a three-run canary is only a smoke test.
  Separate cold/materialization warmups from at least eight measured identical
  replays before declaring deterministic correctness; one divergent token is a
  failed numerical gate. Report warmup divergences separately as well: excluding
  warmups from the predeclared measured pass fraction must not hide an observed
  initialization or state-lifecycle failure.
- A transaction, cache-hit, or restore-plan event proves that control flow ran.
  It does not prove restored tensors are correct. Require exact output/state
  evidence before performance, and never relax that gate to preserve a paper.
- For distributed model papers, separate mechanisms already provided by the
  runtime (parameter/state/cache sharding, packed loaders, collective fusion)
  from the paper's genuinely incremental mechanism before writing code. Existing
  upstream features are applicability evidence, not candidate gains.
- Do not infer a collective implementation or payload dtype from source
  capability, configuration names, or model dtype alone. Instrument every rank
  and record the selected class plus actual input, weight and output
  dtype/geometry on both prefill and decode.
- Treat an FP32-to-FP16 communication proposal as inapplicable when the live
  production collective already consumes and emits BF16. It is then a no-op;
  lowering below BF16 is a new quantization method with a different accuracy
  burden, not a faithful lossless port of the paper.
- When a predeclared applicability abort condition proves that no distinct
  candidate remains, stop before profiling or E2E A/B. Benchmarking identical
  paths under different labels creates noise, not evidence.
- A checkpoint's multimodal configuration proves capability, not workload
  activation. For Encode/Prefill/Decode papers, inspect the frozen requests and
  require actual media payloads plus live Encode events before attributing any
  benefit to encoder separation or feature prefetch.
- When Encode is inactive, do not relabel ordinary P/D disaggregation as EPD.
  Record the mechanism boundary and reject the paper-specific claim even if the
  runtime already has generic P/D connectors and proxy examples.
- For accelerator-architecture papers, map every claimed gain to a software
  choice, operator choice, memory placement, or physical package property.
  Custom compute arrays and on/off-package memory systems are not reproducible
  through a CANN operator or vLLM monkeypatch on fixed silicon.
- Architecture-simulator tics, estimated clocks and FLOP/s are design-study
  evidence only. They never substitute for physical NPU execution, and a
  PyTorch numerical comparator does not make the simulated accelerator a
  deployable kernel.
- Continue only when a distinct software-only mechanism remains after removing
  custom-hardware contributions. Otherwise close a scoped plugin-delivery
  no-go before consuming NPU time.
- For BF16 fused candidates, algebraic equivalence is not numerical
  equivalence. Reproduce the first failing random input, isolate stages with
  identity/zero-state constructions, and preserve a deployed native semantic
  boundary when the custom path cannot reproduce it exactly; never relax the
  gate to keep a wider fusion.
- A queue-safe custom operator can pass output/state/graph checks exactly and
  still lose end to end. Measure the smallest exact plugin boundary once under
  the frozen service protocol; if throughput is negative and the removed
  boundary has already consumed the credible Amdahl opportunity, record an
  implementation-scoped no-go and move to the next paper instead of polishing
  operator microbenchmarks.
- When independent AIV cores update per-head scalar metadata, determine the
  effective GM write granule on the deployed stack instead of assuming scalar
  isolation or that 32-byte alignment is sufficient. Give each core one whole
  empirically safe row or use a single owner. Output agreement plus correct
  payloads and pairwise-corrupted neighboring counters is the diagnostic
  signature of an undersized metadata stride.
- For deferred recurrent-state methods, count every forced materialization by
  runtime reason, layer/rank, and active-slot count before interpreting the
  end-to-end result. A pure-decode custom operator can be numerically valid
  while mixed prefill/decode scheduling repeatedly falls back through a Python
  full-state reconstruction; that integration path can erase the intended HBM
  write savings. Require a device-side mixed-batch materialization seam or
  declare the supported scheduling regime explicitly.
- When changing static NPUGraph inputs immediately before replay, establish a
  device-visible synchronization boundary before diagnosing a late state
  mismatch as an operator failure. Preserve the original failure, rerun the
  unchanged binary once with the corrected harness, and never relax the frozen
  numerical tolerance to make replay pass.
- Before generating a paper-specific Ascend operator, inventory the deployed
  `vllm-ascend` call path and the pinned `CANN/ops-transformer` implementation
  for the same mechanism. Record exact source revisions, callable ABI, supported
  shapes/dtypes, graph behavior, and what the existing code cannot express.
  Reuse an existing native primitive when it covers the paper's semantics;
  add an independently named, opt-in plugin operator only for a measured
  algorithm-specific gap. A faster standalone kernel is not a paper gain.
- A selected-slot recurrent-state bridge can pass native-state, next-output,
  untouched-slot, and NPUGraph checks yet fail serving performance. After a
  direct bridge pass, prove every TP worker uses the intended mixed-batch path,
  count materializations in the exact benchmark window, then run the frozen
  fixed-output service screen before any final accuracy spend. In the Qwen3.6
  DeltaLog follow-on, the v0.2.2 bridge passed all four batch-1/16 NPU modes
  but delivered 113.650 tok/s against 125.819 tok/s dense; the adapter was
  rejected rather than treating direct numerical success as deployment success.
- For page-selective attention adaptations, separate the attention mask mode
  from block-table selection. On the tested CANN 9.1 native FIA, a mask-free
  single-token decode call with `sparseMode=3` fails tiling; use `sparseMode=0`
  when the selected table already contains only past KV entries. Preserve the
  failed call and test changed tables under eager and NPUGraph against exact
  attention on the selected support. This proves only the storage/ABI seam;
  paper selector fidelity, service dispatch and end-to-end benefit are separate
  gates, and other CANN versions must revalidate the ABI.
- During NPUGraph capture, constructing a device tensor from a Python constant
  can issue a synchronous host-to-device copy and fail even after eager NPU
  numerical checks pass. Derive replay-varying indices from pre-existing
  device tensors or graph-safe device operations, then rerun in a fresh result
  directory without erasing the original failure. A synthetic selector/ABI
  pass remains narrower than a real-model serving or quality result.
- In v0.23 general-plugin discovery, a direct early attention import can hit a
  `device_op`/`fused_moe` cycle; initialize the required Ascend ops package
  before importing the attention implementation. Append plugin paths to the
  image's original CANN `PYTHONPATH`, never replace it or hide `acl`. Validate
  both changes with a no-device same-image import before a model launch.
- A runtime field named `layerIndex` may be populated only by an optional
  feature, not the normal attention path. Identify the live model layer from
  the layer object and record its name in a one-shot worker event. Distinguish
  hybrid scheduler block-size logs from the actual native cache tensor page
  dimension before constructing a selected page table.
- A page adapter can retain all token-level top-K selections and still diverge
  from dense attention because unselected softmax mass contributes. Record
  selected-support recall, output error, selector cost and native sparse-call
  cost separately on real Q/K/V. Do not convert an intermediate tensor error
  into the user's end-to-end task-accuracy bound, or promote a non-mutating
  diagnostic into a throughput/accuracy result. The SparQ v5 evidence and
  exact scope are in `projects/qwen36-paper-portfolio/SPARQ_ADAPTATION_GATE.md`.
- If the paper includes omitted-probability-mass correction, test it against
  the *same* real-model Q/K/V and selected support before concluding that
  page selection itself is the sole quality problem. An exact historical mean
  computed from the full cache is valid for a one-shot diagnosis, but is not
  a deployable running-mean lifecycle or a performance result. SparQ's v6
  correction was modest and sometimes slightly worse by TP rank; its direct
  Python page variant was rejected, while paper-level token sparsity remains
  unjudged. Prefer a page-native paper with low-cost page summaries over
  relabeling a costly full-K scan as an optimized selector.
- For GQA page-selection papers, do not assume a high per-head page score can
  be collapsed to one native block table without loss. Measure per-head exact
  attention mass and output error on the actual shared page set before building
  incremental metadata. In Qwen3.6 TP4 (six local Q heads to one KV head), a
  Quest max-across-heads shared table kept only 62.52% mass for the worst head
  even at a 50% page budget. Separate first-call Python dispatch/compilation
  timing from steady-state selector cost. This rejects that adapter, not the
  paper or the user's final 1% E2E accuracy threshold.
- For cross-layer sparse-attention papers, preserve the distinction between
  an anchor's post-softmax pooled Top-K indices, the target layer's actual
  per-query-head attention mass, and final task accuracy. Before writing an
  Ascend selected-token kernel, measure both adjacent-layer transfer and an
  optimistic best-earlier-anchor upper bound on live Q/K/V at useful budgets.
  In TP-sharded GQA, prove whether a paper's KV-head remap is local or needs
  cross-rank communication; a same-rank probe cannot reject the global
  mechanism. Gate every sparse interpretation on full-support math/native
  agreement without relaxing a failed sample. Qwen3.6 Kascade's one-prompt
  same-rank 20% hindsight bound still had a 20.93% worst-head mass and large
  intermediate output error, so its *local operator investment* was declined;
  neither paper-wide performance nor task accuracy was measured. See
  `projects/qwen36-paper-portfolio/KASCADE_ADAPTATION_GATE.md`.
- For a matmul paper, do not infer applicability from the aggregate MatMul
  percentage. Parse the real prefill/decode kernel rows by M, K, N, dtype,
  format, count, and rank; match the paper's required shape and concurrency
  before authoring an operator. On Qwen3.6 TP4's 16-way decode trace, all
  observed MatMuls had M=16, so a single-token `min(M,N)=1` vectorization
  result does not transfer. Check the pinned vLLM-Ascend quantization methods
  and CANN/ops-transformer Split-K sources before generating a W4A16 kernel;
  source presence is not proof that the deployed binary selects that path.
  Keep a paper's local kernel speedup separate from the matched E2E target.
  See `projects/qwen36-paper-portfolio/MATMUL_PAPER_SHAPE_GATE.md`.
- For low-bit attention papers on Ascend, distinguish paper tile equations,
  packed-cache ABI, fused decode, and serving cache lifecycle as four separate
  gates. On CANN 9.1/Triton 3.2, a mixed uint8 payload/FP16 metadata record
  can fail pointer casts or compiler lowering before numerical execution;
  separating typed scale arrays from packed bytes is a valid paper-specific
  storage adaptation only after NPU parity proves its equations. A one-tile
  fused K4/V2 attention pass does not establish sink/tail paging or service
  benefit. If dynamic source branches inside a multi-block fused kernel hit
  BiShengHIR cbuf-copy/alignment failures, preserve each failure and test
  separate compressed/pool block partials with log-sum-exp combination instead
  of repeatedly relaxing numerical gates or claiming the paper is invalid.
  See `projects/qwen36-paper-portfolio/KVARN_ASCEND_GATE.md`.
- For KVarN-style rotated KV caches, an attention kernel compared only in the
  rotated frame is an intermediate check. Rotate Q with the same matrix used
  on K/V writes, combine compressed and FP16 pool contributions by
  log-sum-exp, and inverse-rotate the output before comparing with the
  unrotated full-support reference. Separately verify
  `slot_mapping -> physical block -> pool slot` writes, including a real
  two-block boundary and changed block lookup under the same captured graph.
  Passing either seam does not prove tile sealing, prefix identity, cache
  allocation, service speed or task accuracy; do not preserve a full dense
  cache in a sidecar and call it a compressed-cache memory win.
- A numerically correct compiler workaround may be far too expensive to
  justify service integration. After the real-NPU mixed-cache numerical and
  graph gate, measure the *entire* candidate decode path at representative
  batch and context lengths as an investment diagnostic, including rotation,
  sink/tail, block partials and reduction. A failing diagnostic can reject
  that implementation architecture without becoming a matched dense E2E
  result or paper-wide no-go. KVarN's per-block split path reached 204.207 ms
  at batch 16 and ~16.5K tokens on one 910B4; do not polish or integrate that
  path without a distinct fused/native kernel mechanism.
- For adaptive KV budgets under TP-sharded GQA, inspect the *local* KV-head
  count before porting the author's per-head Top-K. If TP leaves one KV head
  per worker, rank-local allocation is necessarily uniform; scores or
  sufficient statistics must cross ranks at the allocation boundary. A
  four-rank synthetic all-gather/Top-K pass proves only distributed ABI, not
  live-model score fidelity, physical eviction, graph safety or end-to-end
  benefit. Explicitly audit tied-score ordering and safeguard rounding:
  independent per-head rounding can make the allocated total differ from the
  raw global Top-K target by a few tokens. See
  `projects/qwen36-paper-portfolio/ADAKV_ASCEND_GATE.md`.
- For official observation-window selectors, preserve operation order and
  intermediate dtype, not just the algebraic formula. Ada-KV's pinned GQA
  path computes BF16 QK, FP32 softmax, casts probabilities back to BF16,
  then averages over observation positions and grouped query heads before
  pooling. A FP32-only score diagnostic is a derivative, even if its resulting
  cache budgets look close. Check the selected-support math against native
  attention and the full-support math against native dense separately; a
  single-layer error is not the final task-accuracy allowance.
- When an adaptive-cache hook replaces only the native attention read, verify
  whether the framework wrote dense K/V earlier in the same forward call.
  A genuine compact read/write seam must intercept both sides and prove
  selected-support NPU numerics over multiple decode steps. Even then, an
  allocated-but-unwritten dense cache buffer is **not** a physical memory
  saving: request identity, slot recycling, allocation, mixed batch and graph
  replay remain distinct service gates. Ada-KV's first one-layer/one-request
  eager seam and exact scope are in
  `projects/qwen36-paper-portfolio/ADAKV_ASCEND_GATE.md`.
- Before setting a cross-layer numerical tolerance for a BF16 native
  attention candidate, measure the unmodified native path on the same real
  Q/K/V: paged FIA versus contiguous full-support FIA, and both versus an
  independent math oracle at FP32 and native output dtype. Oracle rounding
  error can exceed a fixed absolute RMS bound as layer output scale changes.
  Preserve every failed candidate run, but do not repeatedly tune absolute
  or relative thresholds until it passes; establish the native backend's
  error envelope first, then attribute only incremental candidate error.
  A local selected-support check is separate from selected-versus-dense model
  accuracy and matched service throughput. See
  `projects/qwen36-paper-portfolio/ADAKV_ASCEND_GATE.md`.
  On the pinned Qwen3.6/CANN 9.1 stack, 192 uncompressed native comparisons
  showed up to 0.002819 relative RMS between contiguous BF16 FIA and a
  BF16-rounded independent oracle. A 0.003 envelope frozen from that dense
  baseline let the all-16-layer, four-rank, three-decode-step Ada-KV
  selected-support seam pass (worst 0.002572) without rewriting past failed
  attempts. This is a valid *local numerical* stage, not a pass for request
  isolation, physical cache reduction, E2E throughput, or task accuracy.
- For a compact-cache serving port, concurrent HTTP requests can become a
  *mixed* Ascend attention turn even if sent together: an existing decode may
  overlap a newly admitted full prefill, yielding `ChunkedPrefill` metadata.
  Do not infer support from two independent batch-1 passes. Carry the
  runner's ordered request IDs into the attention hook, key arenas by identity,
  verify cumulative query boundaries and sequence lengths, and fail before
  skipping dense writes on unsupported continuation prefill, dummy padding
  or graph states. Validate the actually observed mixed turn on all TP ranks.
  For a split native prefill call, crosscheck its whole output against the
  deployed full-batch native prefill on the same Q/K/V before claiming the
  operator seam. Ada-KV's two-request eager check passed this crosscheck
  bitwise on 16 layers/four ranks, but still did not reduce vLLM's dense
  allocation or establish 1024-output throughput/task accuracy. Preserve
  launch errors and mixed-state fail-closed runs separately; see
  `projects/qwen36-paper-portfolio/ADAKV_ASCEND_GATE.md`.
- A grouped native FIA path can pass two concurrent 1024-token requests and
  sampled selected-support numerics on all TP ranks while its serving value
  remains unknown. Count real per-rank grouped decode events and preserve
  audit hashes, but do not infer a throughput gain from batching the operator:
  host-side concatenation and an unchanged dense cache allocation can erase
  the intended saving. At the predeclared one-day gate, close the current
  implementation as no-go/inconclusive if matched E2E, allocator, graph, and
  final quality evidence are missing; distinguish this from rejecting the
  paper. Stop and retain completed NPU services instead of leaving HBM leased.
- Before porting a CUDA attention engine's GQA or split-KV decode kernel to
  Ascend, inspect the pinned native FIA tiling and kernel source for the same
  mechanisms. The Qwen3.6 v0.23 call path passes local Q/KV head counts into
  native FIA; the inspected ops-transformer source already has BF16 GQA,
  group-size-aware head tiling, KV-length-weighted core assignment, and
  split-KV partial-output handling. This is a source-level overlap gate, not
  proof that the deployed CANN binary selected those paths or that its
  scheduling is optimal. Require the actual kernel/tiling identity and a
  shape-matched, profiler-off E2E opportunity before commissioning a custom
  FlashInfer-style operator. Do not call a direct port a new paper gain merely
  because a CUDA implementation is faster on different hardware.
- For a low-bit KV or linear paper, inventory the exact native quantization
  methods and previous host artifacts before generating a kernel or converting
  a checkpoint. v0.23 C8 uses checkpoint-provided static per-channel INT8 K/V;
  it is not KIVI's asymmetric 2-bit K/V rule or SKVQ's clipped dynamic groups
  and full-precision recent window. Likewise, saved client throughput JSON
  without a bound service/model/image fingerprint and correctness evidence is
  only a screening clue, not a transferable baseline. When quantization is a
  common stack improvement, give it to the dense control too; attribute only
  the paper-specific increment. See
  `projects/qwen36-paper-portfolio/KV_QUANT_REUSE_GATE.md`.
- For grouped low-bit KV-cache papers, do not relabel a native static-scale
  INT4 attention mode as the paper's dynamic groupwise algorithm. KIVI's
  32-token Key groups, 32-channel Value groups and full-precision residual
  tail are not expressed by the deployed FIA mode-0/mode-1 scales. Compare an
  unpacked equation probe and the native-mode derivative on identical live
  Q/K/V, with an uncompressed native oracle, but keep their single-layer
  errors separate from task accuracy or service throughput. At the declared
  one-day deadline, an output-preserving probe without packed-cache lifecycle
  and matched E2E evidence closes only the current implementation as
  inconclusive; preserve its artifacts and move on instead of declaring the
  paper disproved. See `projects/qwen36-paper-portfolio/KIVI_ASCEND_GATE.md`.
- For a low-bit native matmul graph mismatch, first measure identical-input
  eager repeats, graph repeats, and graph-versus-eager against an unmodified
  dense control at the same shape. A failed bitwise graph/eager assertion alone
  does not identify a graph bug when the quantized native eager call itself is
  non-bitwise-repeatable. Preserve the original failure and report differing
  element counts, maximum absolute and relative RMS errors without retroactively
  relaxing its threshold. A small two-run native envelope is diagnostic, not a
  model accuracy or service acceptance gate. QQQ's physical-NPU4 M16 native
  observation and separate v1/v2 artifacts are in
  `projects/qwen36-paper-portfolio/QQQ_APPLICABILITY_GATE.md`.
- Do not identify quantization arithmetic by scheme name. On pinned v0.23,
  `W4A8_DYNAMIC` passes an unquantized BF16 activation to weight-only
  `npu_weight_quant_batchmatmul`; it is not QQQ's A8W4 GEMM. The deployed
  CANN 9.1 `aclnnQuantMatmulV5` can take INT8 activation and packed INT4
  weight, but its live call mutated nearly every element of the activation
  input on physical NPU4. Preserve the failing repeat, compare *all* inputs
  before/after, and test a disposable activation copy or fresh quantized
  output under eager and NPUGraph before integrating it into a model. A
  passing synthetic copy guard is only an operator ABI/numerical gate. Include
  dynamic activation quantization and any protective copy in the local
  investment timing; compare the same graph/eager regime and exact shape to
  BF16. In QQQ's M16 and M256 graph screens, the complete native A8W4 sequence
  was slower than BF16, so that implementation was declined before costly
  checkpoint conversion. This is not a paper-wide no-go or final accuracy
  result; see `projects/qwen36-paper-portfolio/QQQ_APPLICABILITY_GATE.md`.
- For a GQA fused-selector paper, trace the decision through its kernel
  branch, data loads, output update, public wrapper, and default arguments.
  A per-head score threshold does not imply a per-head sparse output when
  the actual branch is an OR across all query heads sharing one KV head.
  Likewise an inner subblock loop does not prove a smaller active granularity
  when the wrapper defaults its subblock size to the full block. Freeze tensor
  axes and group-mask expansion with a small test before paying for model load.
  On live Q/K/V, report private-head and source-faithful group-union masks
  separately, with exact probability mass and selected-output error; keep
  their one-prompt results below the E2E/task-accuracy claim boundary.
  The FFD v2/v3 correction and scope are in
  `projects/qwen36-paper-portfolio/FFD_APPLICABILITY_GATE.md`.
- For a selector/compression threshold sweep, plot the *source-faithful*
  group-union memory fraction against exact dense probability mass and
  intermediate output drift on the same live Q/K/V. An aggressive setting
  that clears an optimistic byte-only traffic requirement but drops large
  attention mass is not a numerical pass; a safer setting that misses that
  bound does not justify a new kernel on one prompt. Neither observation is
  the user's permitted 1% E2E GSM8K loss. Before rejecting the paper itself,
  inspect author-supported granularity knobs such as subblock size and bound
  their added loop/launch cost. Retain unique NPU artifacts and stop the owned
  service after each one-shot diagnostic. In FFD v5, SBS=16/delta=5 reached
  the optimistic byte-only union-read bound but retained only 66.98% mass
  in the worst observed head and added eight subblock iterations per
  quantized block. This rejects commissioning that current selector route,
  not all workloads or the paper. See the FFD v4/v5 results in
  `projects/qwen36-paper-portfolio/FFD_APPLICABILITY_GATE.md`.
- For lossless weight-compression papers, distinguish checkpoint/startup I/O,
  CPU-offloaded weights copied on each token, and already-resident on-device
  GEMM. A paper's large TTFT/TPOT gain against a single-device CPU-offload
  baseline does not transfer to a TP-sharded model that fits in HBM. Prove a
  live offload/transfer seam before porting its decompressor; never create an
  artificially weaker control to make a paper fit. See
  `projects/qwen36-paper-portfolio/ENEC_APPLICABILITY_GATE.md`.

## Do not do

- Do not select papers by novelty alone.
- Do not apply architecture-specific methods to an incompatible installed
  checkpoint.
- Do not claim an improvement without repeated baseline/candidate evidence under
  matching environment fingerprints.
- Do not mutate vLLM, vLLM-Ascend, CANN, drivers, or system services before the
  applicability gate and workstream checkpoint are in Git.
- Do not commit papers, model weights, datasets, checkpoints, raw profiler
  traces, credentials, or AWMCP verification values.

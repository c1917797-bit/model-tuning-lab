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
  failed numerical gate.
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

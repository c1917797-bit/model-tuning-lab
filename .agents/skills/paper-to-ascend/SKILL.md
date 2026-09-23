---
name: paper-to-ascend
description: Use when selecting, adapting, porting, or evaluating a research paper as an Ascend NPU inference optimization; prove method-chain completeness and constraint feasibility before implementation, and keep claims scoped to measured evidence.
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
3. **Method-chain completeness:** enumerate every paper stage that causally
   supports its performance or quality result. For each stage record its paper
   role, reference source/commit, required data or training, and whether the
   target implementation is `exact`, `adapted`, `substituted`, or
   `omitted`. A port of the headline operation alone is not a port of the
   paper result.
4. **Constraint feasibility:** compare the complete method chain with the
   user's restrictions. If a forbidden or unavailable stage was responsible
   for quality recovery, stability, capacity, or performance in the paper,
   name and gate a credible replacement before implementation. Otherwise
   classify the requested combination as presently infeasible or a stronger
   research objective; do not imply that the paper already demonstrates it.
5. **Bottleneck fit:** what measured Decode, Prefill, kernel, memory, cache,
   communication, or scheduling bottleneck is the paper expected to improve?
6. **Production path:** does the installed vLLM, vLLM-Ascend, CANN, or
   operator stack already expose a usable seam? Prefer built-in exact paths
   before authoring new kernels or replacing low-level code.
7. **Algorithm identity:** label the implementation as `paper-exact`,
   `faithful-port`, or `derivative`. Different selectors, calibration
   corpora, objectives, recovery methods, or runtime policies are separate
   algorithm identities even when the tensor shapes and package name match.
8. **Decision scope:** predeclare whether the first result can support only an
   operator/router, block, service, or full-model claim. Do not promote a narrow
   result into a broader conclusion.
9. **Resource isolation:** reserve concrete NPU IDs, port, CPU/NUMA scope, and
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

For accuracy, semantic-quality, deterministic-canary, or lossless claims, also
use `ascend-model-quality-evaluation`. Its default Paper-to-Ascend quality
ruler uses a 2048-token natural-stopping cap and requires a fresh baseline when
that cap or any evaluator invariant changes.

When the task is to reproduce a prior paper/practice result, historical ruler,
or adoption claim, use `paper-to-ascend-reproduction` to freeze the scientific
question, one-switch A/B denominator, mechanism activation gate, resumability,
and independent audit boundary.

When the paper or benchmark touches CANN/operator/kernel/profiler behavior,
HCCL communication, memory movement, or unexplained low-level regressions, also
use `ascend-cannbot-profiler` before changing low-level code.

This skill chooses whether the paper deserves an experiment; the Ascend skills
make the experiment reproducible and evidence-bound.

## Workflow

1. Read `AGENTS.md`, `.agents/HANDOFF.md`, and any active branch-local
   workstream handoff before using host resources.
2. Use `paper-ingestion` to extract the complete causal method chain, not only
   the headline operation: selection/calibration, model transformation,
   training or recovery, runtime execution, and evaluation conditions.
3. Create a method parity ledger before code:
   `paper stage -> causal role -> reference identity -> target status ->
   replacement/evidence`. Freeze the `paper-exact`, `faithful-port`, or
   `derivative` label. Any later substitution changes that identity and must
   be recorded rather than silently inheriting the paper claim.
4. Use `ascend-architecture-fit` to prove the selected model/checkpoint/runtime
   actually supports the paper's required mechanism, or stop with a scoped
   `does-not-fit`, `requires-retraining`, or `inconclusive` decision.
5. Run the constraint-feasibility check. When the user's target is stricter
   than the paper contract, state the extra research gap and require an
   evidence-backed substitute for every forbidden result-bearing stage.
6. Use `ascend-source-map` to map the mechanism to the smallest real
   configuration or source seam before editing. Prefer existing exact paths.
7. Prove the applicability gate with live or repository evidence. Record
   unknowns explicitly.
8. Choose one primary variable for the first experiment. Keep unrelated paper
   ideas for later loops.
9. Create or resume one `work/*` branch and one experiment record using
   `.agents/experiments/TEMPLATE.yaml`.
10. Freeze baseline conditions before implementation: model/tokenizer identity,
   dtype or quantization, workload, parallelism, container/runtime versions,
   CANN/driver/firmware, physical NPU IDs, port, and launch command.
11. Measure baseline first. Only then use `ascend-canary-implementation` for the
   smallest one-variable candidate, followed by correctness and target-device
   checks before any full benchmark.
12. At every gate, separate algorithm evidence from backend evidence. A layout,
    alignment, scheduler, precision, or state-lifecycle failure invalidates
    that executed path; it is not evidence that the mathematical method is
    worse. Conversely, a kernel-local pass does not prove closed-loop model
    quality.
13. Decide as `accepted`, `rejected`, `inconclusive`, or `failed`, and use
    `paper-to-ascend-reporting` to record the exact scope, recovery state,
    evidence, and next loop.
14. Preserve negative results as pushed history. Recover failed active code
    before integration, but do not erase the evidence.

## Current repository guidance

Read `docs/ACTIVE_WORKSTREAMS.md` and the owning task's latest handoff for the
current model and restrictions. Do not infer authorization for MTP, speculation,
quantization, retraining, or a different workload from historical examples.
The Qwen3.5 performance task currently forbids those algorithm changes; other
tasks may explicitly allow them. Keep paper migration and cumulative serving
acceptance decisions distinct.

For a source-backed GPU-to-Ascend contribution, apply the selection guidance in
`paper-ingestion` before proposing an already-supported Ascend implementation.
Reuse existing task ownership instead of creating a permanent worktree for
each paper considered.

## Lessons already learned

- Dynamic MoE showed that theoretically reduced compute can still regress
  end-to-end latency when routing or packing overhead dominates.
- Keep paper, implementation, operator/block, and full-model decision scopes
  separate.
- A service, container, or old benchmark is not a valid baseline after workload
  or resource ownership drifts; re-isolate and re-baseline.
- Saved FLOPs, faster local GMM, or a single warm run is not enough. Accept only
  correctness-first, apples-to-apples repeated evidence.
- HYPIC showed that historical reproduction needs a named denominator, one
  treatment switch, activation proof, repeated performance and quality units,
  resumable per-sample artifacts, and an independent fail-closed audit before
  adoption.
- HYPIC also showed that a successful port reproduces the whole result-bearing
  runtime chain: matching/planning, state or cache materialization, framework
  scheduling, worker hot path, capacity arithmetic, and fallback behavior.
  Copying only the paper's visible primitive would not reproduce its gain.
- DRRQR showed that reducing Q/K rank can reproduce a local compute-saving
  mechanism without reproducing the paper result. The tested no-training
  objective forbade the paper's training-based quality-recovery stage, and the
  early energy selector and calibration corpus were derivative choices rather
  than paper-exact StrongRRQR. Those differences must be visible before NPU
  implementation, not discovered after endpoint testing.
- DRRQR also showed that backend-invalid ranks must be excluded from algorithm
  trends: non-16-aligned recurrent-state copy-out corruption was a runtime-path
  failure, while the aligned Dk64 speed/quality trade-off was valid evidence for
  only that derivative no-training configuration.

## Do not do

- Do not select papers by novelty alone.
- Do not apply architecture-specific methods to an incompatible installed
  checkpoint.
- Do not call a partial or derivative implementation a paper migration without
  a method parity ledger. Never hide omitted training, calibration, recovery,
  routing, cache, or scheduling stages behind the paper or plugin name.
- Do not spend accelerator time on a target whose joint performance and quality
  contract has no credible path after user-forbidden stages are removed.
- Do not claim an improvement without repeated baseline/candidate evidence under
  matching environment fingerprints.
- Do not mutate vLLM, vLLM-Ascend, CANN, drivers, or system services before the
  applicability gate and workstream checkpoint are in Git.
- Do not commit papers, model weights, datasets, checkpoints, raw profiler
  traces, credentials, or AWMCP verification values.

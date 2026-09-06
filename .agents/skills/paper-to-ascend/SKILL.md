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
2. Use `paper-ingestion` to extract the paper mechanism, prerequisites,
   expected speed path, possible overhead, and first candidate hypothesis.
3. Use `ascend-architecture-fit` to prove the selected model/checkpoint/runtime
   actually supports the paper's required mechanism, or stop with a scoped
   `does-not-fit`, `requires-retraining`, or `inconclusive` decision.
4. Use `ascend-source-map` to map the mechanism to the smallest real
   configuration or source seam before editing. Prefer existing exact paths.
5. Prove the applicability gate with live or repository evidence. Record
   unknowns explicitly.
6. Choose one primary variable for the first experiment. Keep unrelated paper
   ideas for later loops.
7. Create or resume one `work/*` branch and one experiment record using
   `.agents/experiments/TEMPLATE.yaml`.
8. Freeze baseline conditions before implementation: model/tokenizer identity,
   dtype or quantization, workload, parallelism, container/runtime versions,
   CANN/driver/firmware, physical NPU IDs, port, and launch command.
9. Measure baseline first. Only then use `ascend-canary-implementation` for the
   smallest one-variable candidate, followed by correctness and target-device
   checks before any full benchmark.
10. Decide as `accepted`, `rejected`, `inconclusive`, or `failed`, and use
    `paper-to-ascend-reporting` to record the exact scope, recovery state,
    evidence, and next loop.
11. Preserve negative results as pushed history. Recover failed active code
    before integration, but do not erase the evidence.

## Current repository guidance

The current installed target is dense. The active Paper-to-Ascend direction is
exact speculative decoding using the checkpoint's built-in Qwen3.5 MTP head.
Dynamic MoE is retained as a superseded audit exemplar, not an active
optimization path for the dense target.

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
- HYPIC showed that historical reproduction needs a named denominator, one
  treatment switch, activation proof, repeated performance and quality units,
  resumable per-sample artifacts, and an independent fail-closed audit before
  adoption.

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

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
   For Qwen3.6 linear/hybrid-attention work, also read
   [references/qwen36-linear-hybrid-lessons.md](references/qwen36-linear-hybrid-lessons.md)
   before choosing or resuming a paper.
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

The current paper portfolio targets Qwen3.6-27B on Ascend through an
independently named, explicitly enabled vLLM-Ascend plugin or monkeypatch.
Do not mutate upstream vLLM-Ascend, CANN, model checkpoints, or the base image
to make a candidate appear integrated.

Treat HYPIC as a prior workload-specific success reference, not as unfinished
work or proof of a universal gain. For new papers, first prove that their
mechanism is present on the real execution path and that the measured hot-path
share can support the requested end-to-end target. MTP or speculative decoding
is not an acceptable substitute when the selected paper is being evaluated
without it.

This is not a permanent architecture restriction. Future MoE, quantization,
sparse, multimodal, or retraining-based work is allowed when the user selects
that target and live environment orientation proves the matching checkpoint,
runtime, and resources exist.

## Lessons already learned

- Dynamic MoE showed that theoretically reduced compute can still regress
  end-to-end latency when routing or packing overhead dominates.
- Apply an opportunity gate before implementation. Use the measured critical
  path share and an optimistic Amdahl bound; a faster local kernel is not useful
  for a 10% service target when the entire affected path is too small.
- Inspect the code and loaded binary on the actual Ascend dispatch path. Nearby
  Triton, CUDA, reference, or future-version code is not evidence about the
  running service.
- Pass NPU eager, multi-step mutable-state, NPUGraph replay, service dispatch,
  and end-to-end gates in that order. Synchronize asynchronous NPU work before
  comparing graph replay results; an eager pass alone does not prove graph
  safety.
- Audit mixed prefill/decode batches. A fallback that materializes a full state
  once per layer and rank can erase a decode-only saving even when the custom
  operator is numerically correct and reduces auxiliary memory.
- A finite output, one token, or a local tolerance is not a final accuracy
  result. Keep intermediate numerical gates separate from the user's
  LongBench-v2 and GSM8K acceptance thresholds.
- Count end-to-end invocations, fallbacks, copies, materializations, and graph
  misses. Kernel time sums are diagnostic aggregates, not the service critical
  path and not a throughput forecast.
- Stop a candidate after a valid negative end-to-end screen unless new evidence
  identifies a removable cause with enough remaining headroom. Do not spend the
  accuracy budget on a candidate that already fails the performance gate.
- Keep paper, implementation, operator/block, and full-model decision scopes
  separate.
- A service, container, or old benchmark is not a valid baseline after workload
  or resource ownership drifts; re-isolate and re-baseline.
- Saved FLOPs, faster local GMM, or a single warm run is not enough. Accept only
  correctness-first, apples-to-apples repeated evidence.

## Do not do

- Do not select papers by novelty alone.
- Do not apply architecture-specific methods to an incompatible installed
  checkpoint.
- Do not claim an improvement without repeated baseline/candidate evidence under
  matching environment fingerprints.
- Do not relax bitwise, tolerance, determinism, graph, or accuracy gates merely
  to preserve a promising performance result.
- Do not use a declared device mapping as proof of ownership. Resolve physical
  NPUs, container-visible IDs, live processes, HBM, ports, and loaded libraries
  in the same session.
- Do not mutate vLLM, vLLM-Ascend, CANN, drivers, or system services before the
  applicability gate and workstream checkpoint are in Git.
- Do not commit papers, model weights, datasets, checkpoints, raw profiler
  traces, credentials, or AWMCP verification values.

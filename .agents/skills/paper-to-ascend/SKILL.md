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

The current target is Qwen3.6-27B hybrid attention/GDN inference on Ascend,
delivered as an explicit opt-in vLLM-Ascend plugin or monkeypatch. Process the
ranked paper queue one paper at a time, normally within one day per paper. HYPIC
is already pierced and must not be rerun unless a new, explicit hypothesis
requires it. Do not introduce MTP or speculative decoding as a substitute for a
paper's own mechanism.

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
- Compare a paper's baseline with the target baseline before treating its
  headline speedup as available headroom. Single-device-to-TP scaling is not an
  incremental gain over an already-sharded TP service.
- Audit whether the current stack already contains each proposed mechanism.
  If state, packed projections, local operators, and output aggregation already
  match the paper, record that as an applicability no-go instead of rebuilding
  the same design under a new plugin name.
- Communication quantization only saves bandwidth when the proposed transfer
  dtype is narrower than the live payload. BF16-to-FP16 changes representation
  but not bytes; more aggressive INT8 is a distinct algorithm and needs its own
  correctness and accuracy contract.
- Use non-overlapped critical-path communication for an end-to-end ceiling.
  Summed HCCL kernel durations may overlap and must not be substituted for the
  critical path. Stop early when even zero-cost communication cannot meet the
  acceptance target.
- Prove workload reachability before provisioning a system paper. If the fixed
  benchmark bypasses the optimized stage (for example, text-only requests
  bypass a multimodal encoder), headline gains from that stage are unavailable.
- For disaggregated serving, calculate the number of complete model instances
  and per-card weight, activation, cache, and runtime memory before starting
  containers. An experiment that can only OOM under the authorized topology is
  not a paper reproduction.
- A repository with the same system name may implement an earlier paper. Match
  arXiv ID, authors, and mechanism contract before treating it as official
  source code.
- When upstream already exposes connector/proxy seams for a system design, use
  them in a future correctly resourced deployment. Do not duplicate a fleet
  architecture inside a single-process plugin merely to satisfy the delivery
  label.
- For cache/state lifecycle changes, a branch-hit event and structurally correct
  row copy are necessary but not sufficient. Require deterministic repeated
  cache-hit output under fixed decoding settings and a dense control in the
  same execution mode. If the dense control is stable while the candidate is
  not, stop before performance or task-quality benchmarking; do not average the
  corruption away as ordinary numerical noise.
- Keep end-task tolerance separate from intermediate correctness. A permitted
  GSM8K score delta does not authorize nondeterministic recurrent-state replay,
  because such a candidate has no stable semantics to benchmark.
- Classify the paper's intervention layer before implementing anything. A
  custom-chiplet or package-level design whose benefit depends on different
  compute arrays, memory technologies, and physical interconnects cannot be
  reproduced by a runtime plugin on fixed accelerator silicon. Architecture
  simulator ticks and estimated clocks are evidence about the proposed
  hardware, not NPU kernel or service performance.

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

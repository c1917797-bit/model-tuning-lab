---
name: ascend-source-map
description: Use to map a paper-derived inference mechanism to the smallest real code or configuration seam in vLLM, vLLM-Ascend, CANN, ops-transformer, launch settings, or system topology before editing.
---

# Ascend Source Map

## Purpose

Find the correct layer to change before touching code. Many failed optimizations
come from editing too low, too high, or in the wrong repository. This skill maps
a paper mechanism and measured bottleneck to the smallest plausible production
seam.

## Workflow

1. Start with the paper mechanism, architecture-fit decision, and measured
   bottleneck.
2. Classify the intended seam: launch/config, tokenizer/model config, vLLM
   scheduler, batching, sampler, speculative decode path, KV/cache manager,
   attention backend, vLLM-Ascend adapter, torch-npu behavior, CANN operator,
   `ops-transformer`, HCCL/topology, or host/container system setting.
3. Prefer built-in exact paths and configuration switches before custom kernels
   or broad rewrites.
4. Inspect the live target source versions before mapping paths. Historical
   source workspaces on `chicaihong01` may include `/home/mtuser/cch/vllm-ascend`,
   `/home/mtuser/cch/ops-transformer`, `cannbot-skills`, and
   `cann-recipes-infer`, but their current commits must be re-proven.
5. Produce a map from paper concept to concrete files, functions, launch args,
   environment variables, and tests/canaries to touch.
6. Define the minimal first change and the rollback point. If the seam is below
   vLLM-Ascend or requires CANN/operator reasoning, route to
   `ascend-cannbot-profiler` before implementation.

## Output

Before treating a CUDA/Triton kernel as model-compatible, compare its actual
constants and indexing with the checkpoint and TP-local tensors: Q/K versus V
head counts and grouping, head dimensions, state orientation/strides and dtype,
normalization, scale, gates, variable-length inputs, and cache-slot ownership.
Matching the model family or D128 alone is insufficient. Map GPU-specific warp,
shuffle, register, and asynchronous-copy assumptions to a supported Ascend
implementation; changing device names is not a port.

If a numerical failure disappears after fixing runtime-library resolution,
record it as a packaging/backend fix and rerun the same kernel's correctness
and performance gates. Build-only libraries must not silently replace runtime
providers. A corrected output does not imply a faster kernel.

A source map note with:

- target layer and rationale;
- concrete paths/symbols/settings inspected;
- what not to change yet;
- smallest first implementation or config change;
- canary and benchmark entry points;
- rollback/recovery plan.

## Boundaries

- Do not mutate low-level code because a paper mentions kernels; prove the hot
  path and source seam first.
- Do not treat checked-out upstream source as the serving source until container
  mounts/import paths prove it.

# SlimInfer Qwen3.6 Ascend piercing handoff

Updated: 2026-09-14

## Current state

- Workstream branch:
  `work/sliminfer-qwen36-ascend-piercing-20260914`.
- No SlimInfer NPU run has started.
- No SlimInfer performance or accuracy result exists.
- Intended HYPIC-equivalent NPU4-7 lane is not owned. The latest full
  `npu-smi info` showed external `VLLMWorker_TP` PIDs 786664-786667 on NPU4-7,
  each using 26,189 MiB. Do not stop or reuse them.
- The paper, official source structure, Qwen3.6 checkpoint, HYPIC formal
  contract, and pinned vLLM/vLLM-Ascend model loops have been reviewed.
- A deterministic request-local planner and Qwen3.6 12K/6K/4K layer plan are
  committed and pushed.
- An opt-in, identity-preserving `vllm.general_plugins` canary now passes 12/12
  tests in the pinned image without NPU devices. Editable installation and
  entry-point loading also passed, emitting only `plugin_build_active` and
  `model_patch_deferred`. This is a packaging/runtime-hook precondition, not an
  Ascend result.
- A reused Qwen3.6 profile confirms that a faithful row-pruning path could
  affect MLP, GDN, full attention and collective communication. The offline
  parser logged warnings/errors, so the derived aggregates are hotspot evidence
  only, not an end-to-end speedup estimate.

## Main finding so far

Qwen3.6-27B is a 48-GDN/16-full-attention hybrid, while official SlimInfer
replaces a pure full-attention Hugging Face loop and supports batch-one decode.
A faithful port requires layer-specific token/state/cache accounting across GDN,
full attention, TP4 and continuous batching. The live source map confirms that
one request-global metadata object is insufficient. A shortcut must be labeled
as a separate derivative.

## Recovery

1. Re-read repository `AGENTS.md` and this handoff.
2. Re-resolve `chicaihong01/ma` topology and prove direct routing.
3. Verify branch/worktree identity and that the artifact root does not exist.
4. Re-check only NPU4-7 ownership, intended ports and CPU set.
5. If the lane is still occupied, continue source mapping and planner tests;
   do not start a service.
6. If free, run the identity-only eager TP4 service canary before activating
   pruning or starting a benchmark.

## Next scientific decision

Prove the runtime hook on all four ranks, then implement the smallest faithful
layer-local active-token/state contract. The shape proxy admits this work, but
only a real NPU canary may establish correctness and only the frozen ruler may
establish performance or quality.

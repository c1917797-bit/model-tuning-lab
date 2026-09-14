# SlimInfer Qwen3.6 Ascend piercing handoff

Updated: 2026-09-14

## Current state

- Three TP4 selection-shadow attempts are preserved but inadmissible. The first
  was intentionally aborted after source drift; the second completed the
  disabled 13,000-token request but failed before the enabled arm because the
  controller made a one-shot port-reuse check. The third proved that transition
  fix and installed both hooks on all TP workers, then failed during the
  startup dummy forward because that forward has no attention metadata. These
  are integration/control failures, not SlimInfer performance results.
- The port transition now uses a bounded reusable-bind wait and still fails
  closed after 120 seconds. The shadow hook now skips only the explicit
  attn_metadata-is-None startup dummy case; a non-mapping, missing real layer,
  or incomplete final audit still fails closed.
- Physical NPU4-7 are currently free; NPU0-3 remain owned by another task and
  must not be touched.
- Workstream branch:
  `paper-to-ascend/sliminfer-qwen36-result-no-npu-pivoted`.
- No complete, admissible SlimInfer NPU A/B result exists yet.
- No SlimInfer performance or accuracy result exists.
- Intended HYPIC-equivalent NPU4-7 lane is currently free. NPU0-3 have external
  VLLM workers and remain out of scope.
- The paper, official source structure, Qwen3.6 checkpoint, HYPIC formal
  contract, and pinned vLLM/vLLM-Ascend model loops have been reviewed.
- A deterministic request-local planner and Qwen3.6 12K/6K/4K layer plan are
  committed and pushed.
- An opt-in, identity-preserving `vllm.general_plugins` canary, selection
  shadow and hidden-state restoration contract now pass 46/46
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

The first semantic canary also requires an entire prompt in one model forward.
Partial/chunked prefill cannot retroactively save deep-layer work for an earlier
chunk. Whole-prompt scheduler admission, if used, must be measured in both arms
or decomposed from the algorithm effect.

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

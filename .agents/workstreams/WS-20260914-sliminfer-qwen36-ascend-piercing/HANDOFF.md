# SlimInfer Qwen3.6 Ascend piercing handoff

Updated: 2026-09-14

## Current state

- Workstream branch:
  `work/sliminfer-qwen36-ascend-piercing-20260914`.
- No SlimInfer NPU run has started.
- No SlimInfer performance or accuracy result exists.
- Intended HYPIC-equivalent NPU4-7 lane is not owned: each device reported 87%
  HBM use during the latest read-only check and an unrelated vLLM service was
  live. Do not stop or reuse it.
- The paper, official source structure, Qwen3.6 checkpoint, HYPIC formal
  contract, and pinned vLLM/vLLM-Ascend model loops have been reviewed.
- A deterministic request-local planner and Qwen3.6 12K/6K/4K layer plan now
  pass 8/8 tests in the pinned image without mounting NPU devices. This is a
  precondition only, not an Ascend result.

## Main finding so far

Qwen3.6-27B is a 48-GDN/16-full-attention hybrid, while official SlimInfer
replaces a pure full-attention Hugging Face loop and supports batch-one decode.
A faithful port requires layer-specific token/state/cache accounting across GDN,
full attention, TP4 and continuous batching. A shortcut must be labeled as a
separate derivative.

## Recovery

1. Re-read repository `AGENTS.md` and this handoff.
2. Re-resolve `chicaihong01/ma` topology and prove direct routing.
3. Verify branch/worktree identity and that the artifact root does not exist.
4. Re-check only NPU4-7 ownership, intended ports and CPU set.
5. If the lane is still occupied, continue source mapping and planner tests;
   do not start a service.
6. If free, run the smallest eager TP4 correctness canary before any benchmark.

## Next scientific decision

Quantify the maximum affected critical-path fraction in the HYPIC 32K prefill
and determine whether vLLM's hybrid cache/state interface can safely carry a
layer-specific active-token stream. Only then implement the opt-in canary.

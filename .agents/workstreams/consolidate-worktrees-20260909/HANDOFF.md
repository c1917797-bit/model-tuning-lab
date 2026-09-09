# Worktree consolidation handoff

## Status

- Execution: started.
- Integration: not ready.
- Base: `origin/main@80ff89386c8edbe9435da3cecda11b91661c11aa`.
- This repository-only maintenance task owns no NPU, container, process, port,
  or model resource.

## Audit rules

- Integrate only clean, pushed, validated workstreams whose dependencies and
  branch-local handoff permit integration.
- Preserve dirty, active, blocked, or not-ready worktrees.
- Publish clean retained checkpoints without relabeling them as integrated.
- Reclaim only after proving reachability, no live process/lease/claim, and a
  merged or superseded retention decision.

## Current findings

- Main was one commit ahead and has been validated and synchronized.
- The Ascend skill branch is complete/ready but shares history with a not-ready
  DRRQR import; it must be split before integration.
- Two Qwen3.5 worktrees are dirty and cannot be reclaimed.
- Several clean experiment branches remain not-ready or record ongoing goals.

## Next actions

1. Extract the validated maintainer-skill changes onto this clean branch.
2. Validate, push, and integrate the clean result.
3. Publish clean unpushed experiment checkpoints to their own branches.
4. Re-audit process/lease/reachability state and reclaim only eligible trees.

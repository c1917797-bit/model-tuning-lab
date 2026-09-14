# Workstream Handoff — workspace governance

Updated: 2026-09-14

## Objective

Persist the verified target-host workspace inventory after safe archival
reclamation. This repository-only workstream owns no NPU, port, runtime
process, or running container.

## Verified starting state

- main is clean and synchronized with origin/main at 64468d3.
- The merged paper-parity worktree was reclaimed after its exact source commit
  was retained by a remote annotated archive tag.
- The superseded query-rewrite and ShortGPT worktrees were clean, had no live
  process or running-container references, and were retained by exact remote
  annotated archive tags.
- With explicit user authorization, 116 exited containers referencing only
  those two superseded worktrees were removed. No Docker volume, image, running
  container, external evidence root, or active experiment worktree was removed.
- Immediately after reclamation, six worktrees remained: main plus five
  unmerged task worktrees.
- Two later task worktrees are now present: SlimInfer Qwen3.6 piercing and this
  temporary governance worktree. The Qwen3.8 evaluation worktree also became
  dirty. The live pre-integration inventory is therefore eight worktrees.

## Boundaries

- Preserve the dirty Qwen3.5 delivery and sparse-prefix worktrees exactly.
- Preserve all unmerged task branches, including clean branches that still
  require validation or integration.
- Treat live containers and runtime state as dynamic; re-measure before any
  future machine mutation.

## Next action

The governance record is complete. Run `./scripts/validate-mst.sh` and
`git diff --check` on the exact tree, integrate serially into `main`, push
`main`, and reclaim only this clean temporary governance worktree. Preserve
the six experiment/support task worktrees.

## Integration receipt

- Integrated into local `main` by merge commit
  `a8a45199720930aee89e5eb83bd2c250c005bee6`.
- The final receipt update is intentionally a follow-up main commit so the
  task record does not falsely claim integration while still on its workstream.
- After final validation and remote push, reclaim only
  `/opt/host/vnf/austinov/worktrees/workspace-governance-20260914`.

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
- After reclamation, six worktrees remained: main plus five unmerged task
  worktrees.

## Boundaries

- Preserve the dirty Qwen3.5 delivery and sparse-prefix worktrees exactly.
- Preserve all unmerged task branches, including clean branches that still
  require validation or integration.
- Treat live containers and runtime state as dynamic; re-measure before any
  future machine mutation.

## Next action

Update target-owned workstream and consolidation documentation, run
./scripts/validate-mst.sh and git diff --check, then push this workstream for
serialized integration.

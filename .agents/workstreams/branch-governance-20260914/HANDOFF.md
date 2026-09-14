# Workstream Handoff — branch governance

Updated: 2026-09-14

## Result

- Starting inventory after fetch/prune: 16 local branches and 12 origin
  branches.
- Seven branches were attached to registered worktrees and were preserved:
  `main` plus six active task branches.
- Nine unattached local historical branch names were removed.
- Five unattached remote historical branch names were removed.
- Existing archive tags were verified against every previously retired local
  tip. Five new annotated tags were pushed because the remaining historical
  branches had no exact immutable recovery name; the locally-ahead prefix
  experiment received separate tags for its local and former remote tips.
- After this temporary governance branch is integrated and reclaimed, the
  expected steady state is seven local branches and seven origin branches,
  matching the seven registered worktrees.

No experiment code, dirty worktree, runtime process, container, port, NPU, model
or external evidence artifact was modified.

## Recovery

The exact branch-to-tag mapping and retained live branch list are recorded in
`docs/BRANCH_GOVERNANCE_20260914.md`. Restore a retired line only by creating
a new branch from the named tag; never move or overwrite the archive tag.

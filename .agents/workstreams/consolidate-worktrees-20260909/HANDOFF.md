# Worktree consolidation handoff

## Status

- Execution: completed.
- Integration: ready.
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

## Completed findings

- Main and every committed retained checkpoint were pushed and verified against
  their upstream refs.
- Three validated Ascend maintainer-skill changes were isolated from the
  coupled import branch as commits `977b795`, `eb8f6b7`, and `7a79193`.
  No DRRQR/project import is included in this integration candidate.
- The policy-rejected dense-MTP and measured-rejected prefix-cache branches
  retain their negative evidence remotely. Both were marked `superseded`,
  re-audited with no live holder or resource claim, and their worktrees were
  reclaimed without merging rejected code to `main`.
- Worktree count is reduced from eight to six at this checkpoint and will be
  five after this consolidation worktree is integrated and removed.
- Four non-main worktrees are deliberately retained: query-rewrite and the PR
  gate are dirty/active; ShortGPT is clean but its goal remains open; the
  DRRQR/objective branch is clean but its imported history still needs path
  adaptation and is not integration-ready.

## Next actions

1. Validate and integrate this branch into `main`, then push and prove exact
   remote reachability.
2. Remove this clean worktree after the merge is published.
3. Continue only the four retained workstreams according to their own handoffs;
   do not merge branch-local imports or rejected candidates by association.

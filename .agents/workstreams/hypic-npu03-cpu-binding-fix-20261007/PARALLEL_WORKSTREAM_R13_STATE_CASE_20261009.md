# Parallel-workstream real-task check — 2026-10-09

Scope: the live HYPIC physical-NPU0–3 task on a named
`work/hypic-npu03-cpu-binding-fix-20261007` branch in an independent
chicaihong01 checkout. The exact `origin/main`
`mst-parallel-workstreams` Skill blob is
`c47b989bc006561d347e0fbfe5d59026fb8e91e0`; registry blob is
`2611864bbcf719d57920aae03ff9eb85521526b4`.

## Observed state and repair

- The task has its own branch-local `task.json`, `HANDOFF.md`, resource
  claim, immutable experiment roots and active controller handle. The
  unrelated canonical checkout is dirty on another named workstream; it
  was neither edited nor integrated by this check.
- Before this check, `task.json` had one experiment-specific `state`
  but no separate `execution_state` and `integration_state`. That made
  a live experiment and integration readiness ambiguous to a new agent.
  The manifest now explicitly says `in-progress/not-ready`; a focused
  regression asserts both axes and passed 2/2 tests.
- At the check, local HEAD was `82f47e90000a644dd642bad8fedfa74483031445`,
  attached to the named branch. The configured upstream was
  `0d00bab0ad63c5bdad39f2f7887577d188194485` and local divergence
  was 39 ahead, 0 behind. The branch is **not** integration-ready or
  synchronized. GitHub authentication is unavailable; no push or primary
  update is claimed.
- `git worktree list --porcelain` in this standalone task clone shows
  only itself. The canonical repository has a separate worktree inventory,
  so a single repository's worktree list is not a complete host-wide task
  inventory. Do not reclaim either checkout from this observation.

## Acceptance boundary

The Skill correctly routes this long-running, resource-leased task away
from primary and its state model identified a real handoff defect. This
is a bounded **partial** use, not proof of the full workstream lifecycle:
remote start-checkpoint provenance was not replayed here, later commits
remain unpushed, full claim/dependency and drift attestations are not
closed, and no fetched-source integration or reclamation was performed.
Repeat the state test after r13 terminal transition and only consider
`ready` after complete quality/performance evidence, clean worktree,
remote equality and reviewed integration gates.

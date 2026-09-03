---
name: mst-parallel-workstreams
description: Route non-trivial, multi-file, risky, long-running, protected-path, cross-agent, or parallel maintenance through one named remote work branch and independent worktree, then serialize evidence-bound integration and reclamation. Use for deciding whether direct-primary work is allowed, creating or resuming workstreams, integrating branches, resolving drift or claims, and cleaning up completed worktrees. Do not use a detached worktree to produce commits or push the primary branch.
---

# Parallel Workstreams

## Invariant

Parallelize implementation and serialize shared truth. Keep every durable
implementation checkpoint on a named remote workstream branch until a checked
integrator updates the primary branch. Never force-push shared history.

Treat a worktree as leased execution capacity, not as a branch or permanent
project structure. A detached worktree may run read-only inspection, builds, or
reproduction only; attach a named branch before the first edit or commit.

## Route before editing

Allow direct-primary work only when **all** conditions hold:

- one maintainer owns the task and no concurrent work can overlap;
- the primary worktree is clean and synchronized with its upstream;
- the change is atomic, low-risk, short-lived, and easy to revert;
- it does not touch protected paths, architecture, contracts, shared maintainer
  truth, release behavior, migrations, or performance claims;
- focused validation can complete in the same checkpoint; and
- the repository policy explicitly permits direct-primary work.

Require a workstream when **any** condition holds:

- multiple agents, tasks, filesets, or repositories may progress independently;
- the change is multi-file, architectural, risky, long-running, or cross-agent;
- protected paths, shared truth, public contracts, migrations, release state,
  security boundaries, or performance evidence can change;
- review, handoff, drift detection, dependencies, or resource leases matter; or
- the route is uncertain.

Do not treat “temporary worktree” as a direct-primary exception. Repository
policy may narrow the exception further but may not broaden it for protected or
parallel work.

## Branch and state model

Give each task one stable task id, one `work/*` branch, one independent
worktree, and one branch-local directory:

```text
.agents/workstreams/<task-id>/
  task.json
  HANDOFF.md
  knowledge-proposals.json
  integration-evidence.json
```

Record target and workstream branches, remote, creation time, original base,
objective, boundaries, dependencies, claims, validation commands, owner,
resource leases, retention decision, and resume point. Keep these state axes
independent:

```text
execution_state:   started | in-progress | blocked | completed
integration_state: not-ready | ready | needs-revalidation | integrating |
                   merged | superseded
```

Branch-local `completed` is not global completion. Only target-owned `merged`
state after the primary push makes the result integrated truth.

## Start checkpoint

Start from a clean primary branch synchronized with its remote:

1. Fetch the configured remote and verify primary divergence is `0 0`.
2. Create `work/<task-id>` from the remote primary tip and attach an independent
   worktree; reject detached HEAD and reused branches.
3. Freeze the original base plus hashes of constraining strategy and contract
   paths.
4. Declare dependency ids and `file`, `semantic`, `resource`, `strategy`, and
   `knowledge` claims as `read`, `shared`, or `exclusive`.
5. Create branch-local HANDOFF and state as `started/not-ready`.
6. Validate structure and commit only the start checkpoint.
7. Push with upstream creation to the same remote `work/*` branch.
8. Verify local HEAD equals that remote workstream before implementation.

Do not begin product edits until the remote start checkpoint exists. Push every
subsequent coherent workstream commit to that branch's upstream, never directly
to the primary branch.

## Claims, drift, and shared truth

Order racing exclusive claims by `(created_at, task_id)`. Let the earlier claim
continue with a warning; require the later task to wait, narrow scope, redirect,
or revalidate after the earlier integration.

Preserve the original base and frozen hashes. Before integration, fetch and
merge the latest target into the workstream without rebasing or rewriting
history. On drift, set `needs-revalidation`, re-orient, rerun focused and
integration gates, and bind the attestation to the exact target and source.

Keep global HANDOFF and global maintainer knowledge target-owned. Without an
exclusive knowledge claim, write reusable lessons to
`knowledge-proposals.json`; let the integrator accept, rewrite, reject, or
supersede them against current target truth.

## Readiness contract

Set `completed/ready` only when all declared work is committed and pushed,
focused evidence passes, dependencies and claims are satisfied, the worktree is
clean, and branch-local HANDOFF names the exact source commit. Any product,
contract, skill, or implementation change after evidence invalidates readiness.

## Serialized integration

Use one integrator and integrate only a fetched remote workstream ref:

1. Lock or otherwise serialize the integration plane.
2. Fetch remote state; require a clean, synchronized primary worktree.
3. Check dependency order, claims, leases, original-base drift, and that the
   remote workstream contains the current primary tip.
4. Verify tracked evidence binds the exact primary parent and validated remote
   source commit.
5. Prepare a deliberate non-fast-forward merge by default so branch identity is
   visible; a repository may use an equivalent reviewed merge mechanism that
   preserves source provenance.
6. Reconcile knowledge proposals and global HANDOFF, then stage target-owned
   `merged` state plus source and target-parent provenance in the merge tree.
7. Run declared integration gates on that exact final tree.
8. Commit the already-validated tree as the integration merge; do not add a
   separate unvalidated state commit afterward.
9. Push the primary branch normally; never use force or an automatic retry that
   could hide new remote drift.
10. Fetch again and verify primary divergence is `0 0`, the source is reachable
    from primary, and the pushed merge commit is the validated commit.

If primary moves during integration, abort before push, refresh the workstream,
and repeat validation. Never validate one source commit and merge another.

## Lifecycle and reclamation

Inventory worktrees before creating one, before integration, after integration,
and at maintainer handoff. Until a repository overrides them, use an active
worktree budget of four and a stale alert of seven days. Crossing either limit
blocks new worktree creation until eligible work is integrated, retained, or
reclaimed.

Reclaim only after proving:

1. status is clean or every intentional change has a pushed checkpoint;
2. every retained commit is reachable from primary or an explicitly retained
   remote branch;
3. integration evidence and global HANDOFF reflect the final outcome;
4. no process, claim, lease, dependency, or maintainer still uses the worktree;
5. target-owned state is `merged` or `superseded`; and
6. the retention decision is recorded outside chat.

Then remove the worktree, delete the merged local branch, prune stale metadata,
and delete the remote branch only when repository retention policy permits.
Never force-remove a dirty worktree, delete an unmerged branch, or use age alone
as evidence that work is obsolete.

## Adoption and validation

Record primary branch, remote, work prefix, workstream root, shared-truth paths,
direct-primary exception, lifecycle budget, stale threshold, trailers, and
integration mechanism in repository-owned policy. Add executable checks for
route selection, attached branch identity, upstream equality, manifests,
claims, drift, state transitions, exact-source evidence, primary push boundary,
and reclamation eligibility.

Keep adoption experimental until one bounded repository proves creation,
workstream push, drift/revalidation, serialized integration, and cleanup with
executable checks.

## Anti-patterns

Do not use a detached or unnamed temporary worktree for authored changes; push a
workstream commit to primary; confuse immediate push with “push to main”; run
parallel agents in one dirty worktree; coordinate through a mutable global task
file; erase drift by refreshing the original snapshot; equate a clean text merge
with semantic compatibility; or force-push workstream or primary history.

## Provenance

Distilled from WAsmC's production-tested workstream model and corrected after an
MCPGit performance worktree was pushed directly to primary despite being a
non-trivial task. Keep product-specific build, language, and deployment rules in
their owning repositories.

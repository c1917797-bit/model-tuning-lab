---
name: mst-git-checkpoint-policy
description: Use when deciding when and where an agent should commit and push repository changes, including direct-primary exceptions and workstream branch checkpoints. Ask the maintainer to choose a policy, then codify the confirmed policy as repository guidance without confusing immediate push with push-to-primary.
---

# Git Checkpoint Policy

## Purpose

Protect completed work during repository maintenance by making commit and push behavior explicit.

This skill is especially useful where frequent validated remote checkpoints are
preferred over long-lived dirty or local-only worktrees.

## When to use

Use when:

- transforming a repository into an `AGENTS.md + skills` driven repository,
- starting maintenance on a repository with no explicit commit policy,
- a maintainer mentions preserving progress,
- deciding whether an agent may commit or push,
- or after validation passes and the worktree contains completed changes.

## Policy options to ask the maintainer

Ask the maintainer to choose one of these policies unless a policy is already confirmed in `.agents/git-policy.yaml` or `AGENTS.md`.

### Option A: Manual only

The agent never commits or pushes unless explicitly instructed for the current task.

### Option B: Local checkpoint commits

The agent may create local commits after coherent milestones and passing checks, but asks before pushing.

### Option C: Branch and pull request

The agent works on feature branches and prepares pull requests or merge requests.

### Option D: Single-branch clean push after basic validation

The agent keeps the repository on one primary branch. After compile/basic validation passes, it commits and pushes so the repository remains clean and progress is protected.

### Option E: Commit implies push with workstream routing

Every commit is pushed immediately to its current named branch upstream.
Atomic low-risk tasks may use primary only when all repository-defined
exceptions pass. Non-trivial work pushes a remote workstream branch; a
serialized integrator alone updates primary.

## Confirming a policy

Once the maintainer confirms a policy, codify it in one or both of:

- `.agents/git-policy.yaml`
- `AGENTS.md`

The confirmed policy becomes the repository default until changed by the maintainer.

## Default for this repository

This repository uses:

```text
commit_implies_push
```

Meaning:

1. Route the task before editing.
2. Use primary only for an atomic low-risk direct-primary exception.
3. Otherwise create a named `work/*` branch and remote start checkpoint.
4. Run required validation before each coherent commit.
5. Push to the current branch upstream immediately.
6. Let only serialized integration update primary.
7. Keep completed worktrees clean and reclaim eligible workstreams.

## Basic validation gate

For this repository, the current basic validation command is:

```sh
./scripts/validate-mst.sh
```

## Commit rules

- Commit only coherent completed work.
- Use clear commit messages.
- Do not mix unrelated transformations.
- Do not commit local machine files.
- Do not push known-broken work unless the maintainer explicitly requests it.
- Do not author commits from detached worktrees.
- Do not push a workstream commit directly to primary.
- Do not force-push shared workstream or primary history.

## Required output

Report:

- selected git policy,
- validation command and result,
- commit hash if committed,
- push target if pushed,
- and whether the working tree is clean.

## Verification

- The confirmed policy is present in `.agents/git-policy.yaml` with a
  `repository_policy` matching a defined option.
- Workstream routing records direct-primary conditions, branch-required
  conditions, remote start checkpoints, integration ownership, and lifecycle
  defaults.
- `./scripts/validate-mst.sh` runs and exits with code 0 before any commit.
- After push, the current named branch equals its configured upstream.

## Anti-patterns

Do not:

- push without running validation first,
- interpret immediate push as automatic permission to push primary,
- commit local machine files (IDE configs, build artifacts),
- mix unrelated transformations in a single commit,
- push known-broken work unless the maintainer explicitly requests it,
- change the git policy without asking the maintainer,
- or assume a policy that has not been confirmed and written to `.agents/git-policy.yaml`.

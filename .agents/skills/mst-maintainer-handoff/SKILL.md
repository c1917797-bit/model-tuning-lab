---
name: mst-maintainer-handoff
description: Use when creating or verifying global or branch-local maintainer handoffs, including bounded runtime-controller transfer, live ownership, immutable deadlines, evidence scopes, and exact resume commands.
---

# Maintainer Handoff

## Purpose

Make agent-to-agent repository maintenance handoff explicit, short, current, and validated.

`AGENTS.md` explains how to enter the repository. `.agents/HANDOFF.md` explains where the repository is right now. Skills explain reusable behavior. The handoff snapshot connects them.

## When to use

Use this skill when:

- a new agent starts on a repository that uses skillsgit;
- a maintainer turn ends after non-trivial implementation;
- the active track, current action, next action, blocker, or validation evidence changes;
- a repository transformation wants fast takeover between agents;
- an autonomous loop needs a persistent human-readable state spine in Git.

## Handoff file location

The canonical current handoff file is:

```text
.agents/HANDOFF.md
```

Do not store current handoff state only in chat transcripts, issue comments, or tool memory.

## Global and workstream handoff boundary

The global HANDOFF describes integrated primary-branch truth. When
`mst-parallel-workstreams` is active, each `work/*` branch also owns a
branch-local `.agents/workstreams/<task-id>/HANDOFF.md` for its objective,
execution state, evidence, and resume point. Read both; never overwrite the
global HANDOFF merely to announce unmerged branch progress.

Workstream `execution_state=completed` is branch-local. Global HANDOFF may
describe the result as shipped only after serialized integration records
`integration_state=merged`.

## Required Handoff Shape

`.agents/HANDOFF.md` must keep these sections in this order:

```text
0. Status
1. North Star
2. Current Focus
3. Recent Progress
4. Current Action
5. Next Actions
6. Validation Commands
7. Do Not Do
8. Recovery / Resume Commands
```

Each section must be concrete enough that a new agent can answer:

```text
what is the repo trying to become?
what is the current active track?
what changed most recently?
what validation has actually run?
what should I do next?
what must I avoid?
how do I recover if state is unclear?
```

## Start-of-turn workflow

1. Read `AGENTS.md`.
2. Read `.agents/HANDOFF.md`; on a workstream branch, also read its branch-local HANDOFF and task manifest.
3. Read the narrow skills named by the handoff.
4. Run `git status --short --branch` and `git log -8 --decorate --oneline`.
5. Continue from `Next Actions` unless the user changes direction.

## End-of-turn workflow

1. Update the active HANDOFF with current status, validation evidence, and next action: global on integrated work, branch-local on a workstream.
2. Update any narrow skill or doc if durable future behavior changed.
3. Run the relevant validation gate.
4. Commit and push according to the repository git policy.
5. Verify the worktree is clean or leave an explicit recovery command.

## Rules

- Keep `.agents/HANDOFF.md` shorter than the long iteration log.
- Prefer precise current facts over historical narration.
- Link to skills and docs instead of copying them.
- Record partial validation honestly.
- Keep runtime-user guidance out of `.agents/HANDOFF.md`.
- Do not let `.agents/HANDOFF.md` replace backlog/checkpoints for autonomous loops; it is the human-readable resume surface.

## Transfer of bounded runtime ownership

When the user transfers an active workstream or stops new preparation, freeze
source-side launches, source edits and preparation dispatch. Let already
admitted finite controllers finish their original budget and own-only cleanup
unless the user explicitly requests termination. Transfer does not renew the
authority, admission deadline, phase clock or cleanup allowance.

Record branch/HEAD, latest CURRENT/NEXT/BACKUP, unit/PID/CID and operation IDs,
result roots, exact lock owner/FD and natural release conditions, proven and
pending gates, first blockers and executable next commands. Distinguish a
completed submission operation from the live systemd job; an expired operation
record is not proof that the job ended. Do not copy credentials into handoff.

Timestamp a fresh snapshot after collecting the handoff. If an admitted job
finishes during transfer, retain the earlier observation as history and mark
the later snapshot authoritative for that time. With RemainAfterExit=yes,
active/exited and MainPID=ControlPID=0 is a terminal state; also verify every
owned cleanup, PID0/noOOM/empty ExecIDs and actual lock release. Never delete a
lock file, reset a unit or launch a second scheduler to manufacture quiescence.

Commit the branch-local handoff, report remaining running tasks from the final
snapshot, and stop source-side experimental writes. The receiver re-proves live
identity/ownership and the original gates before its next admission. Historical
peer IDs, CIDs and leases are not continuing authority. For the actual BOLE case,
read [bounded service recovery](../ascend-inference-tuning-loop/references/bole-saved-input-and-service-qualification.md).

## Validation

For handoff-only changes:

```sh
./scripts/validate-mst.sh
git diff --check
```

If the handoff claims code behavior changed, also run the repository-specific checks listed in its `Validation Commands` section.

## Anti-patterns

Do not:

- make handoff a full project diary;
- leave it stale after a multi-step implementation;
- duplicate all architecture text from skills;
- hide blockers because the final answer sounds cleaner;
- or rely on the previous agent's chat context as the resume path.

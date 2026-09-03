---
name: mst-repo-onboarding
description: Use when an agent first enters this repository, resumes a session, or needs to re-orient after structural changes. Do not use for routine code changes.
---

# Repository Onboarding

## Purpose

Ensure the agent understands this repository's structure, skill tree, and current state before making any changes.

## Workflow

1. Read `AGENTS.md` for the maintainer role and canonical sources.
2. Read `.agents/skills.registry.yaml` for the full skill catalog and selection rules.
3. List all skill directories under `.agents/skills/` and confirm each has a `SKILL.md`.
4. Check for repository-specific docs: `docs/ARCHITECTURE.md`, `CLAUDE.md`, tool adapters.
5. Check for agent work directories: `agents/*/work/backlog.yaml` for current task state.
6. Run `./scripts/validate-mst.sh` and confirm PASS before proceeding.
7. Emit a structured Onboarding Report (see Required Output).

## Onboarding Report

After completing all steps, the agent must report:

```text
## Onboarding Report

- Repository: <path>
- Skills: <count> skills in registry
- Agents: <count> agent work directories found
- Active tasks: <count> non-done tasks across all backlogs
- Validation: PASS / FAIL (<details>)
- Last significant change: <git log --oneline -1>
- Structural changes since last session: <none / list>
```

## Verification

- `./scripts/validate-mst.sh` must pass.
- Every skill ID in the registry must have a corresponding directory.
- No orphan skill directories without registry entries.

## Anti-patterns

Do not:

- skip reading the registry before starting work,
- start editing files before completing all workflow steps,
- assume the repository structure is unchanged from a previous session,
- proceed if `validate-mst.sh` fails (stop and report),
- or treat onboarding as optional because "I was here yesterday."

## When to re-onboard

Re-run this skill when:

- the agent is unsure about current state,
- the registry has been modified since last session,
- new skills have been added or removed,
- the agent is resuming after a checkpoint.

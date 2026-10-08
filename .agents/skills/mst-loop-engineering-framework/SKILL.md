---
name: mst-loop-engineering-framework
description: Use when designing or maintaining a Git-backed loop engineering framework with skills, handoff state, validation, checkpoints, worktrees, connectors, and maker/checker separation.
---

# Loop Engineering Framework

## Purpose

Frame skillsgit as a Git-native practice framework for loop engineering: the repository stores the knowledge, state, validation rules, and audit trail that a recurring agent loop needs in order to improve without relying on chat memory.

## Loop pieces in skillsgit terms

```text
automation heartbeat -> scripts/orient.sh, scripts/run-iteration.sh, external schedules
work isolation       -> git worktree / branch policy / protected paths
skills               -> .agents/skills/**/SKILL.md + .agents/skills.registry.yaml
connectors/tools     -> MCP/tool adapters that point back to AGENTS.md
maker/checker split  -> implementation agent + verifier/reviewer skill or sub-agent
memory/state spine   -> .agents/HANDOFF.md + agents/<id>/work/* + Git history
```

The key rule is: the agent forgets, the repository does not.

## Parallel workstream routing

When two or more maintainers need independent branches or worktrees, compose
this framework with `mst-parallel-workstreams`. That skill owns branch-local
task identity, execution/integration state separation, claims, drift,
knowledge proposals, and serialized integration. This framework continues to
own the generic LOOP and non-drift contract; it does not duplicate the
workstream protocol.

## Non-Drift Loop Contract

A loop is allowed to enter its next iteration only when all of these are true:

```text
objective is still the same bounded objective
current state is recorded outside chat
validation gate is known before editing
maker output has been checked by an independent checker role or validation skill
handoff/backlog says exactly what comes next
Git contains the checkpoint or the blocker is explicit
```

If any item is false, the loop must stop, update state, ask for direction, or narrow the objective. It must not drift into adjacent work just because the agent can continue.

For multi-stage tasks spanning sessions or long experiments, use the
[three-horizon drift check](references/three-horizon-drift-check.md) to align
long, medium, and short goals before another run, retry, or scope change.

## Architecture Orientation Gate

A loop that touches architecture, topology, gateways, runtime ownership, or production paths must pass an orientation gate before proposing or editing. The gate is generic; each target repository should fill in the concrete files and commands.

```text
1. Read the latest commits for the active area, not only stable docs.
2. Read current deployment topology: compose files, manifests, service comments, or equivalent IaC.
3. Read the narrow architecture/boundary skill for the target repo.
4. Check whether older docs are contradicted by recent commits or marked historical.
5. State active production path and legacy/compatibility path separately.
6. Name missing gateway layers explicitly instead of collapsing them into one generic service.
```

If the user corrects an architecture claim, treat it as a failed orientation gate. Do not simply apologize and continue. Ingest the correction as durable behavior: update the target skill, handoff, docs, or executable guard that would have prevented the drift.

Reference practice case: in one target repository, the agent over-weighted older implementation wording and under-weighted recent commits plus deployment topology that changed the production path. The durable lesson is generic: topology claims must be oriented from live repo evidence, and corrections must be ingested into target-specific skills/tests. Keep target-specific names and architecture locks inside the target repository, not in this template.

## Design workflow

1. Define the loop purpose, bounded objective, and stop condition.
2. If the loop is cross-component or architectural, pass the Architecture Orientation Gate.
3. Write or select the smallest skills that preserve project-specific intent.
4. Add a current handoff snapshot so the next agent can resume.
5. Add backlog/checkpoint/budget state if the loop spans sessions.
6. Add validation gates that can reject a false "done" claim.
7. Decide whether parallel work requires `mst-parallel-workstreams`; do not use
   parallel branches without its branch-local state and integration boundary.
8. Split maker and checker instructions when the loop will run unattended.
9. Update handoff/backlog before entering the next loop.
10. Commit and push coherent validated iterations so Git becomes the audit log.

## Repository artifacts

A repository using this framework should prefer these durable artifacts:

```text
AGENTS.md                         bootstrap and routing
.agents/HANDOFF.md                current resume state
.agents/skills.registry.yaml      skill routing and status
.agents/skills/**/SKILL.md        reusable maintainer behavior
.agents/git-policy.yaml           checkpoint / push behavior
.agents/protected-paths.yaml      paths needing branch/review
agents/<id>/work/backlog.yaml     machine-checkable task queue
agents/<id>/work/checkpoints/*.json  resumable execution state
agents/<id>/work/progress.md      running log
Git commits                       durable audit log
```

## Generic Loop-Control Skill Pattern

When applying skillsgit to a substantial repository, add a repository-specific loop-control skill when the project has long-running maintenance, multiple agent tracks, or repeated handoffs. The skill should define:

```text
loop spine: orient -> skills -> objective -> edit -> validate -> checkpoint -> next/stop
entry checklist: status, handoff, latest commits/topology for architecture work, skill selection, validation gate, isolation choice
non-drift rules: one bounded objective, no hidden chat state, no feature hunt after validation failure
maker/checker split: authoring role is not the only verifier
exit checklist: validation, handoff update, skill/doc update, commit/push, clean status
stop conditions: failed evidence, failed architecture orientation, broadened scope, dirty unrelated worktree, conflicting user direction
```

A target repository may implement this pattern with its own loop-control skill. Keep this template generic; do not copy target-specific architecture, product names, service names, or topology locks into skillsgit.

## Template / instance boundary

skillsgit owns the generic loop pattern. Target repositories own their concrete production paths, service names, topology locks, domain runners, and demo goals. A real incident may be cited only as a compact practice case when it teaches a reusable rule; it must not make the template depend on that repository.

## Validation expectations

A loop framework is not validated by a clever prompt. It is validated when:

- `scripts/validate-mst.sh` passes;
- registry and filesystem skills match;
- handoff has the required sections;
- current tasks have pass criteria;
- architecture/topology claims have an orientation gate and at least one drift-prevention check;
- a fresh agent can orient, pick the next action, run validation, and commit/push without hidden context;
- the checker can independently reject a bad result;
- the next loop entry point is explicit and bounded, or the loop stops.

## Anti-patterns

Do not:

- treat a loop as just a repeated prompt;
- let the maker agent be the only verifier;
- keep state only in a conversation;
- run parallel agents in one dirty worktree;
- treat branch-local completion as integrated repository truth;
- create a giant universal skill instead of narrow skills;
- keep an impressive handoff that is not tied to validation evidence;
- make architecture claims from stale docs while ignoring recent commits or deployment topology;
- enter the next loop with a changed objective but unchanged handoff;
- or let automated speed replace engineering judgement.

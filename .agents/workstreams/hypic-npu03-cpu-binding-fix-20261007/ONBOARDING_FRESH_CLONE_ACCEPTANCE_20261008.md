# Fresh-clone repository onboarding acceptance — 2026-10-08

This is a bounded behavioral acceptance of mst-repo-onboarding on the
current origin/main, not acceptance of all 29 Skills or live NPU entry.
The operator-created test clone was a new GitHub HTTPS clone, not a copy
of an existing working directory:

- Clone target: /cache/cch/mst-onboarding-acceptance-20261008-1018
- Source: https://github.com/c1917797-bit/model-tuning-lab.git
- Clone command: git clone --depth 1 --branch main --single-branch
- Pinned HEAD: f1f37a39bd86f7db5fd3ee3dea358ae6868275c6
- Worktree: clean main tracking origin/main
- Last significant change: f1f37a3 merge: integrate Ascend performance optimization skill

The maintainer read AGENTS.md, the full registry, .agents/HANDOFF.md,
docs/RUNBOOK.md, docs/LESSONS_LEARNED.md, and docs/ACTIVE_WORKSTREAMS.md.
The tool adapter CLAUDE.md contains only @AGENTS.md. The optional
docs/ARCHITECTURE.md is absent and was recorded as absent, not inferred.
The agents/ directory and agents/*/work/backlog.yaml files are absent:
the backlog count below is zero, but docs/ACTIVE_WORKSTREAMS.md separately
names real workstreams. This report does not interpret an absent backlog
as proof that no task is running on the host.

## Onboarding Report

- Repository: /cache/cch/mst-onboarding-acceptance-20261008-1018
- Skills: 29 IDs in registry, 29 directories, 29 SKILL.md entrypoints
- Agents: 0 agent work directories in this clone
- Active tasks: 0 non-done tasks across agent backlogs (no backlogs present)
- Validation: PASS (scripts/validate-mst.sh exited 0)
- Last significant change: f1f37a3 merge: integrate Ascend performance optimization skill
- Structural changes since last session: not applicable to a fresh clone;
  this clone is pinned to main f1f37a39, while later HYPIC work remains
  branch-local.

Independent read-only checks found no missing/orphan skill ID using an
exact sorted registry-versus-directory comparison, and no directory
missing SKILL.md. The result demonstrates that a new clone can follow
the onboarding route and produce its required report. It does not prove
live AWMCP access from another computer, NPU availability, device runtime
behavior, or the behavioral quality of the other 28 Skills.

The test clone was created only for this acceptance and can be safely
removed after this evidence is pushed; no experiment artifacts or edits
were placed inside it.

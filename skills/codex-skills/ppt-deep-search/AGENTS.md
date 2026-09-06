<!-- BEGIN COMPOUND CODEX TOOL MAP -->
## Compound Codex Tool Mapping (Claude Compatibility)

This section maps Claude Code plugin tool references to Codex behavior.
Only this block is managed automatically.

Tool mapping:
- Read: use shell reads (cat/sed) or rg
- Write: create files via shell redirection or apply_patch
- Edit/MultiEdit: use apply_patch
- Bash: use shell_command
- Grep: use rg (fallback: grep)
- Glob: use rg --files or find
- LS: use ls via shell_command
- WebFetch/WebSearch: use curl or Context7 for library docs
- AskUserQuestion/Question: present choices as a numbered list in chat and wait for a reply number. For multi-select (multiSelect: true), accept comma-separated numbers. Never skip or auto-configure - always wait for the user's response before proceeding.
- Task (subagent dispatch) / Subagent / Parallel: for forward tests, use Codex subagent capability, specifically `multi_agent_v1.spawn_agent` when available; do not fall back to solving the candidate task in the main thread. Outside forward tests, run sequentially in main thread
  unless true parallel tool calls are needed, in which case use multi_tool_use.parallel
- TaskCreate/TaskUpdate/TaskList/TaskGet/TaskStop/TaskOutput (Claude Code task-tracking, current): use update_plan (Codex's task-tracking primitive)
- TodoWrite/TodoRead (Claude Code task-tracking, legacy - deprecated, replaced by Task* tools): use update_plan
- Skill: open the referenced SKILL.md and follow it
- ExitPlanMode: ignore
<!-- END COMPOUND CODEX TOOL MAP -->

## Repository Instructions

This repository contains the `ppt-deep-search` skill and its forward tests. Treat edits to the skill, references, and tests as changes to an agent behavior contract, not just code.

Before changing runtime behavior, read `docs/architecture_design.md`. It is the development-time architecture contract for maintainers and coding agents. `SKILL.md` is runtime guidance; do not use it as the primary place for development-time architecture notes.

When runtime behavior changes, update the affected references, QA scripts, and forward-test instructions together. A behavior rule that is easy to check should become an executable QA gate rather than relying only on prose.

## Markdown Size Gate

Before submitting code or skill-document changes, run:

```text
python scripts/validate_markdown_size.py .
```

This gate is intentionally generic. It checks only Markdown size budgets:
line count, total characters, and maximum single-line characters.

If it fails, review the document architecture as a whole before editing.
Do not satisfy the gate by shaving one sentence from one file. Keep entry
files focused on core workflow, routing, and hard boundaries; move detailed
guidance, schemas, long examples, and reusable material into smaller focused
references, scripts, or assets.

## What "Run Forward" Means

When a human says "跑forward", "跑一遍forward", or "run forward", it means to run the repository's forward-test harness as a main-agent orchestration flow. It does not mean the current/main thread should directly solve the test case.

The main agent must:

1. Read the forward-test README and the selected case's main-agent instructions.
2. Start a child agent using Codex subagent capability, specifically `multi_agent_v1.spawn_agent` when available.
3. Give the child only the candidate-facing prompt, candidate input path, required output path, run id, and the instruction to follow this repository's `SKILL.md`.
4. Keep judge files, rubrics, expected outputs, and main-agent strategy hidden from the child.
5. Act as the human stakeholder during the run: answer only the child agent's explicit choice, clarification, or approval request with minimal realistic input.
6. Do not coach the child toward better output during the run; inspect the child output after completion and write the final judgment under the run output directory.
7. Judge strictly as a teacher looking for defects. The goal is to expose problems, not to make the test pass.

### Forward Dispatch Minimality

The child dispatch prompt is part of the test. Keep it minimal and context-isolated.

- Do not use `fork_context=true` for forward-test child agents. The child must not inherit the main thread's judge-side notes, recent critique, expected weaknesses, prior run summaries, or implementation strategy.
- Do not include judge rubrics, expected scoring dimensions, previous run failures, target fixes, design critiques, or explanations of what the main agent hopes to validate.
- Do not tell the child to demonstrate a specific new reference, pattern, or implementation detail unless that instruction is already in the candidate-facing prompt or repository `SKILL.md`.
- A run-specific reminder is allowed only when it is short and user-facing, for example `本轮重点关注 HIL HTML 是否清楚可读`; it must not become a strategy checklist.
- The child may be told that it is already the candidate child and must not start another forward-test runner. This is execution hygiene, not strategy leakage.
  If repository `SKILL.md` explicitly requires task-local subagents, such as per-page web capture, the candidate child may follow that Skill requirement.

Bad dispatch:

```text
Use the new pattern library, prove that method-card/evidence-pair/rebuild-block appear, and improve the Tufte/SenseNova style.
```

Good dispatch:

```text
请使用仓库 `SKILL.md` 完成 forward test:
- Candidate Prompt: ...
- Candidate Input: ...
- Output: .tmp/forward-tests/<case>/<run-id>/
你已经是 candidate child；不要再启动新的 forward-test runner。
若仓库 `SKILL.md` 明确要求为任务内工作委派子 agent，可以按 `SKILL.md` 执行。
需要审批时等待主 agent。
```

If an agent receives a parent dispatch prompt that already names a `Candidate Prompt`, `Candidate Input`, and required `.tmp/forward-tests/<case-id>/<run-id>/` output directory, that agent is the candidate child agent for the forward run. In that role, do not try to start another
forward-test runner. Read the candidate-facing files and repository `SKILL.md`, run the Skill's HIL workflow normally,
ask the parent/human for approvals when required, and write artifacts to the provided output directory.
If the repository `SKILL.md` explicitly requires task-local subagents, such as per-page web capture,
the candidate child may use them without treating them as new forward-test runners.

The child agent must write all artifacts under:

```text
.tmp/forward-tests/<case-id>/<run-id>/
```

If the child writes to another temporary location, correct the child immediately and require the artifacts to be copied or regenerated under the required output directory.

In Codex, "child agent" means the subagent interface exposed by `multi_agent_v1`, not a separate Codex App conversation thread created with `codex_app.create_thread`. Background conversation threads are useful for other coordination tasks, but they are not the forward-test runner
for this repository.

## Forward-Test Boundaries

Forward tests are interactive HIL simulations. A forward run is not a one-shot generation task, and an output directory does not imply permission to skip review gates.

During a forward run:

- Do not solve the candidate task in the main thread.
- Do not paste judge rubrics, hidden fixtures, or expected answers into the child prompt.
- Do not coach the child with the main agent's current hypothesis about what a good answer should look like. The point of the forward run is to observe whether the Skill itself elicits and produces the behavior.
- Do not provide rewrite examples, preferred page titles, expression patterns, rubric dimensions, or repair instructions during stakeholder interaction.
- If the child asks a numbered question, choose a number. If it asks for intermediate approval, approve it.
- Stop the run only when the child is fully out of control: wrong output directory, missing required artifact path, judge-file leakage, inability to continue, or responses that no longer follow the task.
- Judge quality from the final deliverables.
- Do not use a background conversation thread as a substitute for the required subagent.
- Do not use a fire-and-forget background worker that cannot receive follow-up input.
- Do not replace child-agent orchestration with shell sleep loops or a purely local script runner.
- If a real subagent tool such as `multi_agent_v1.spawn_agent` is unavailable, stop and report that the forward test is blocked.

## Stakeholder Approval Discipline

The main agent's stakeholder answers should be realistic and minimal.

- For choice questions, answer the selected option and only the minimal stakeholder context needed to disambiguate the choice.
- For intermediate approval gates, approve and let the candidate continue. Do not rewrite the artifact, prescribe a better structure, or teach the child the expected expression principles.
- Record weak Skill behavior as a finding in the final judgment instead of repairing or blocking it interactively.
- Evaluate child-agent interaction quality from the full tool-returned message content, not from a folded or truncated Codex App preview.
- If the child output exposes a defect introduced by the current Skill, record it as a forward-test finding instead of silently compensating with detailed coaching.
- Final judgment must especially inspect source understanding quality, evidence boundaries, required review artifacts, and whether the interaction deviated from HITL.
- After the child finishes, always write `.tmp/forward-tests/<case-id>/<run-id>/judgment.md` using the case rubric before reporting the run complete to the user.

## Case Selection

If the user says "跑forward" without naming a case, follow the forward-test README's case-selection rule. For this repository, use cases under `forward-tests/ppt-deep-search/`.

If there is one case, run that case. If there are multiple cases and the README does not specify otherwise, randomly select 3 valid cases when at least 3 exist, otherwise select all valid cases, and state which ones are being run.

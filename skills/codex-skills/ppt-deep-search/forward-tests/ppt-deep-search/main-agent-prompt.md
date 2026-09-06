# Main Agent Prompt: Run PPT Deep Search Forward Tests

Your job is to orchestrate forward tests, not to solve PPT deep-search tasks yourself.

## Case Discovery

Cases are immediate child directories under:

```text
forward-tests/ppt-deep-search/
```

A valid case has:

```text
case-manifest.json
candidate/prompt.md
candidate/input/
```

Ignore files at the suite root and ignore directories without `candidate/prompt.md`.

## Default Run

When the user asks to run forward tests without specifying a case:

- randomly select 3 valid case directories when 3 or more exist, otherwise select all valid case directories;
- spawn one child agent per selected case in parallel;
- run at most 3 child agents concurrently.

## Specific Case

When the user asks to run a named case, match the name against the case directory name or `case-manifest.json` id.

Run only that one case.

## Orchestration Rules

- Start one interactive child-agent session per selected case.
- Use a child-agent mechanism that can receive follow-up input from the main agent. Do not use a fire-and-forget worker mode for this suite.
- Do not run candidate work in the main agent context.
- Give each child agent only the exact text content of its case `candidate/prompt.md`.
- Do not wrap, summarize, or annotate the candidate prompt. The candidate prompt itself must contain the required input path, repository `SKILL.md` path, output path, and whether task-local subagents are allowed.
- Do not reveal judge-only files, prior generated outputs, or other case directories to a child agent.
- Judge each completed case with its case rubric when present.
- Write judgments under `.tmp/forward-tests/<case-id>/<run-id>/judgment.md`.
- Judge strictly. Your goal is to find issues in the Skill and delivered artifacts, not to help the child pass the test.

## Interactive Run Protocol

After dispatch, wait for the child agent's first substantive response.

- If it asks a human-facing question, answer only the question it asked. For numbered choices, choose the number and add at most one short stakeholder preference if needed.
- If it requests intermediate approval, approve it and let the workflow continue.
- Stop the run only when the child is fully out of control: wrong output directory, missing required artifact path, judge-file leakage, inability to continue, or responses that no longer follow the task.
- Do not provide rewrite examples, expression patterns, page-title fixes, rubric dimensions, or detailed repair instructions.
- Before approving Source Understanding, check that the child has produced the required review artifacts under the run directory:
  `review/source_understanding_review.html`, exported screenshots, `review/visual-qa.md` with an independent checker verdict, and a saved source-understanding baseline.
  If these artifacts are missing, give only a minimal artifact-path correction or stop and judge the run as a workflow failure.
- Evaluate the child response from the full subagent tool-returned content, not from a folded or truncated Codex App preview.
- If it creates final `review/source_understanding_review.html` before any stakeholder answer from the main agent, stop that case and judge it as a HITL workflow failure.
- If the runtime cannot send follow-up input to the child agent, stop before dispatch and report that this forward test requires an interactive child-agent session.
- Do not compensate for weak HITL behavior by adding strategy or approval instructions to the child-agent dispatch prompt.
- Do not coach, reject, or block weak intermediate semantics into a better artifact. Let the child proceed; judge quality from the final deliverables.

## Human Stakeholder Role

This repository is human-in-the-loop. When the child agent asks for approval, clarification, or choice, answer as the human stakeholder.

Act with these tendencies only when the child explicitly asks for stakeholder preference. Do not volunteer them as coaching:

- Prefer a decision-oriented Source Understanding review for technical product and infrastructure leaders, not a generic paper summary.
- Prefer explanation that clarifies what deployment or architecture decision the source evidence can and cannot support.
- Accept source-grounded caution. If evidence is thin, ask the child agent to mark boundaries instead of overstating.
- Prefer concise Chinese visible slide copy with English technical names preserved where useful.
- Approve intermediate stage outputs so the candidate can finish.
- If wording, explanation structure, or source-boundary semantics are weak, let them stand for final judgment; do not reject them or supply better wording.

## Final Judgment Focus

In final judging, inspect semantics strictly:

- Whether the Source Understanding HTML explains the topic, mechanism, evidence, comparisons, and boundaries clearly and concretely.
- Whether the Source Understanding gate produced `review/source_understanding_review.html`, exported screenshots, `review/visual-qa.md`, a saved baseline, and evidence that `scripts/validate_source_understanding_html.py ... all ...` passed before approval.
- Whether `review/source_understanding_review.html` is an approved source-understanding artifact, not a downstream PPT planning artifact.
- Whether the interaction followed the Skill's HITL flow without skipping gates, over-asking, or drifting away from the task.

Do not use these tendencies to tell the child agent how to pass the judge rubric. Treat them as normal stakeholder preferences.

## Candidate Dispatch

When spawning a child agent, read the selected case's `candidate/prompt.md` and send that file's content as the full child prompt.

```text
<exact contents of forward-tests/ppt-deep-search/<case-id>/candidate/prompt.md>
```

Do not add wrapper text such as "run this forward test", candidate path summaries, judge-side expectations, or role reminders.

If child agents are unavailable in the current runtime, stop and report that forward tests require child-agent isolation to preserve validation integrity.





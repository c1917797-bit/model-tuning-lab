# PPT Deep Search Forward Tests

Forward tests are human-orchestrated child-agent runs for checking whether the runtime Skill can conduct human-in-the-loop research and produce a Source Understanding review from realistic source material.

Current runtime also requires a Source Understanding review gate before approval.
Judge-side expected artifacts should include `review/source_understanding_review.html`, exported screenshots, `review/visual-qa.md` with an independent checker verdict, a saved source-understanding baseline, and evidence that `scripts/validate_source_understanding_html.py ... all ...` passed.

## Cases

Each case lives under:

```text
forward-tests/ppt-deep-search/<case-id>/
```

Required candidate-facing files:

- `case-manifest.json`
- `candidate/prompt.md`
- `candidate/input/`

Optional judge-facing files:

- `fixture-manifest.md`
- `judge/rubric.md`

## Running Semantics

Forward tests do not need a Node runner. They are main-agent orchestration prompts, but they do require interactive child-agent sessions:

- When the user asks to run forward without specifying a case, the main agent randomly chooses 3 valid case directories when 3 or more exist, otherwise all valid case directories, and starts one child agent per selected case.
- The max child-agent concurrency is 3.
- For the default run, start the selected child agents in parallel up to that concurrency limit.
- When the user asks to run a named case, the main agent starts exactly one child agent for that case.
- Each child agent receives only the exact text content of that case's `candidate/prompt.md`. The candidate prompt itself must name the required `candidate/input/`, repository `SKILL.md`, and normal runtime paths required by the Skill.
- Judge-only files stay in the main agent context.
- The main agent must wait for each child agent's human-facing question or approval request and answer it as the stakeholder.
- If a child agent writes final artifacts before any main-agent stakeholder answer, stop that case and record it as a HITL failure.
- Do not launch a fire-and-forget worker that cannot receive follow-up input; use an interactive child-agent/session runner.

Case names are the directory names under:

```text
forward-tests/ppt-deep-search/
```

Use `main-agent-prompt.md` for the exact orchestration wording.

## Human-In-The-Loop Semantics

Unlike one-shot downstream PPT generation tests, this suite tests a human-in-the-loop Skill. The main agent must act as the human stakeholder when the child agent asks questions. It should answer with product intent, audience preference, judgment calls, and corrections, while
avoiding strategy coaching or judge-rubric leakage.

The stakeholder role is intentionally narrow. During a forward run, the main agent should answer the child agent's explicit question, not evaluate or improve intermediate semantics.

- When the child offers numbered choices, choose a number and add only minimal real stakeholder context if needed.
- When the child asks for intermediate approval, approve it so the run can continue.
- Stop the run only when the child is fully out of control: wrong output directory, missing required artifact path, judge-file leakage, inability to continue, or responses that no longer follow the task.
- Do not rewrite titles, provide expression patterns, name expected rubric dimensions, or prescribe how to repair the output.
- Semantic quality is judged from the final deliverables after the interaction, not corrected or blocked into shape during the run.
- Final judgment must especially inspect source understanding quality, evidence boundaries, required review artifacts, and whether the interaction deviated from HITL.

The main agent is not allowed to treat the child agent as a fire-and-forget worker. The first useful child-agent response should be a question, an approval gate, or an explicit statement that the research frame is already fully specified. If the child agent silently assumes
approvals, that behavior is the test result, not something to repair by adding more candidate prompt text.

When judging the child agent's interaction quality, use the full message content returned by the subagent tool. Do not treat a folded or truncated Codex App preview as the complete child response.

Judge with a strict teacher stance. The goal of a forward test is to expose product and Skill defects, not to help the run pass. Do not lower the bar because the child worked hard, produced many files, or partially followed the workflow.

## Minimal Prompt Principle

Forward tests measure whether the runtime Skill can produce and approve Source Understanding review artifacts through its normal workflow. The child-agent dispatch prompt must be the exact text content of the selected case's `candidate/prompt.md`.

Do not add wrapper text such as "you are a candidate child", "run this forward test",
candidate path summaries, strategy explanations, judging criteria, expected answer structure,
evidence-selection policy, approval scripts, or summaries of previous failures. Keep those in
`fixture-manifest.md`, `judge/rubric.md`, or the main agent's judgment context only.

In Codex, also keep the child context isolated:

- Do not use full-history forking for the candidate child. A fork may leak judge-side context, previous user critiques, or main-agent hypotheses into the candidate run.
- Spawn the child with a fresh prompt equal to `candidate/prompt.md`.
- The candidate prompt must explicitly state whether task-local subagents are allowed. Current cases allow subagents when the Skill needs them for web capture, paper parsing, HTML deck generation, or visual QA.

## Included Cases

- `aegaeon-gpu-pooling-hitl`
- `goal-oriented-reasoning-rag-memory-hitl`
- `rtx-spark-agent-pc-web-evidence-hitl`
- `stochastic-kv-routing-hitl`
- `tidar-hitl`



# Main Agent Prompt: Run TiDAR HITL Forward Test

Run the forward test at:

```text
forward-tests/ppt-deep-search/tidar-hitl
```

Your job is to orchestrate the test and act as the human stakeholder. Do not solve the PPT deep-search task yourself.

## Files To Read First

Read these judge-side files before dispatch:

- `forward-tests/ppt-deep-search/tidar-hitl/fixture-manifest.md`
- `forward-tests/ppt-deep-search/tidar-hitl/judge/rubric.md`

Confirm the candidate-facing input exists:

- `forward-tests/ppt-deep-search/tidar-hitl/candidate/prompt.md`
- `forward-tests/ppt-deep-search/tidar-hitl/candidate/input/source-request.md`

## Candidate Dispatch

Start an interactive child-agent session. The child prompt must be exactly the contents of:

```text
forward-tests/ppt-deep-search/tidar-hitl/candidate/prompt.md
```

Do not fork the full main-agent conversation into the child. Do not add wrapper text, candidate path summaries, judge-side context, previous run critiques, or the main agent's current theory about how to improve the Skill.

If subagents are unavailable in the current runtime, stop and report that this forward test requires a child-agent run to preserve validation integrity. Do not run the candidate task yourself in the same context.
Use a child-agent mechanism that can receive follow-up input from the main agent. Do not use a fire-and-forget worker mode for this case.

## Interactive Run Protocol

After dispatch, wait for the child agent's first substantive response.

- If it asks about source scope, comparison targets, evidence gaps, or approval, answer as the stakeholder.
- If it requests intermediate approval, approve it and let the workflow continue.
- If it writes final `review/source_understanding_review.html` before any stakeholder answer, stop the child agent and record a HITL workflow failure.
- If the runtime cannot send follow-up input to the child agent, stop before dispatch. This case is invalid without interactive child-agent control.
- Do not fix this by adding strategy, rubric, or approval instructions to `candidate/prompt.md`.

## Human Stakeholder Tendencies

When the child agent asks questions, answer as a realistic PPT requester:

- Target reader: model architecture / inference platform leaders evaluating whether a hybrid diffusion-autoregressive decoding architecture is worth tracking or reproducing.
- Desired use: a pre-PPT Source Understanding review for an internal model efficiency and serving strategy deck.
- Source scope: keep the review focused on the paper mechanism, production evidence, transfer assumptions, and source figures.
- Interpretation direction: TiDAR is interesting if it can credibly combine AR-level quality with diffusion-style parallel drafting, but the deck must make the architecture, benchmark scope, and serving assumptions legible.
- Evidence taste: prefer throughput/quality tables, free-token-slot profiling, architecture masks, comparisons with AR/speculative decoding/diffusion baselines, and source figures before generic LLM-decoding background.
- Tone: decision-oriented Chinese, with English method/model/metric names preserved.

Approve intermediate stage outputs so the candidate can finish. Do not mention the judge rubric or expected scoring categories to the child agent.

## After Candidate Finishes

Collect the candidate's output directory and inspect:

- `review/source_understanding_review.html`;
- any saved baselines or approval bundle;
- QA validation output, if present.

Use `forward-tests/ppt-deep-search/tidar-hitl/judge/rubric.md` to judge the output.

Write judgment to:

```text
.tmp/forward-tests/tidar-hitl/<run-id>/judgment.md
```






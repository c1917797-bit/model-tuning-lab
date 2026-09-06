# Main Agent Prompt: Run RTX Spark Agent PC Web Evidence HITL Forward Test

Run the forward test at:

```text
forward-tests/ppt-deep-search/rtx-spark-agent-pc-web-evidence-hitl
```

Your job is to orchestrate the test and act as the human stakeholder. Do not solve the PPT deep-search task yourself.

## Files To Read First

Read these judge-side files before dispatch:

- `forward-tests/ppt-deep-search/rtx-spark-agent-pc-web-evidence-hitl/fixture-manifest.md`
- `forward-tests/ppt-deep-search/rtx-spark-agent-pc-web-evidence-hitl/judge/rubric.md`

Confirm the candidate-facing input exists:

- `forward-tests/ppt-deep-search/rtx-spark-agent-pc-web-evidence-hitl/candidate/prompt.md`
- `forward-tests/ppt-deep-search/rtx-spark-agent-pc-web-evidence-hitl/candidate/input/source-request.md`

## Candidate Dispatch

Start an interactive child-agent session. The child prompt must be exactly the contents of:

```text
forward-tests/ppt-deep-search/rtx-spark-agent-pc-web-evidence-hitl/candidate/prompt.md
```

Do not fork the full main-agent conversation into the child. Do not add wrapper text, candidate path summaries, judge-side context, previous run critiques, expected evidence-package failures, or the main agent's current theory about how to improve the Skill.

If subagents are unavailable in the current runtime, stop and report that this forward test requires a child-agent run to preserve validation integrity. Do not run the candidate task yourself in the same context.
Use a child-agent mechanism that can receive follow-up input from the main agent. Do not use a fire-and-forget worker mode for this case.

## Interactive Run Protocol

After dispatch, wait for the child agent's first substantive response.

- If it asks about source scope, comparison targets, evidence gaps, or approval, answer as the stakeholder.
- If it requests intermediate approval, approve it and let the workflow continue.
- If it writes final `review/source_understanding_review.html` before any stakeholder answer, stop the child agent and record a HITL workflow failure.
  Do not accept raw HTML, web search snippets, or hand-written excerpts as substitutes for `source.md` plus article/main-region original image assets.
- If the runtime cannot send follow-up input to the child agent, stop before dispatch. This case is invalid without interactive child-agent control.
- Do not fix this by adding strategy, rubric, or approval instructions to `candidate/prompt.md`.

## Human Stakeholder Tendencies

When the child agent asks questions, answer as a realistic PPT requester:

- Target reader: technical architecture / AI engineering leaders evaluating whether RTX Spark represents a new local-agent PC platform category or mainly a marketing/spec update.
- Desired use: a pre-PPT Source Understanding review for an internal architecture evaluation deck.
- Page count: prefer 6 total PPT pages; cover and contents count if the child agent asks.
- Interpretation direction: RTX Spark is best explained as a Windows local personal-agent stack anchor, not just a high-TOPS AI PC; however, the deck must keep official wording separate from Chinese media paraphrase.
- Evidence taste: prefer official NVIDIA/Microsoft source pages, original product/source images, exact spec numbers, runtime/security-stack descriptions, and explicit boundary notes before generic agentic-AI hype.
- Tone: decision-oriented Chinese, with English product/model/runtime/metric names preserved.

Approve intermediate stage outputs so the candidate can finish. Do not mention the judge rubric or expected scoring categories to the child agent.

## After Candidate Finishes

Collect the candidate's output directory and inspect:

- `review/source_understanding_review.html`;
- any saved baselines or approval bundle;
- QA validation output, if present.

Use `forward-tests/ppt-deep-search/rtx-spark-agent-pc-web-evidence-hitl/judge/rubric.md` to judge the output.

Write judgment to:

```text
.tmp/forward-tests/rtx-spark-agent-pc-web-evidence-hitl/<run-id>/judgment.md
```






# Main Agent Prompt: Run Web Article Capture Forward Tests

Your job is to orchestrate forward tests, not to solve webpage capture tasks yourself.

## Case Discovery

Cases are immediate child directories under:

```text
forward-tests/
```

A valid case has:

```text
candidate/prompt.md
candidate/input/
judge/rubric.md
```

Ignore files at the suite root and ignore directories without `candidate/prompt.md`.

## Default Run

When the user asks to run forward tests without specifying a case:

- randomly select 3 valid case directories when 3 or more exist, otherwise select all valid case directories;
- spawn one child agent per selected case;
- run at most 3 child agents concurrently.

## Specific Case

When the user asks to run a named case, match the name against the case directory name.

Run only that one case.

## Orchestration Rules

- Start one interactive child-agent session per selected case.
- Use a child-agent mechanism that can receive follow-up input from the main agent.
- Do not run candidate capture work in the main agent context.
- Read the selected case's `candidate/prompt.md` and `candidate/input/` yourself, then inline the concrete task and input values in the child dispatch.
- Do not ask the child to read `candidate/prompt.md`, `candidate/input/`, or any `forward-tests/` path.
- Give each child agent only the inlined case task, assigned input values, repository `SKILL.md`, and normal runtime references/scripts required by the Skill.
- Keep the child-agent dispatch prompt minimal and natural. Do not restate strategy, judging criteria, evidence policy, isolation policy, expected answer structure, previous failures, or validation mechanics.
- Do not reveal judge-only files, prior generated outputs, or other case directories to a child agent.
- Before dispatch, choose a new `<run-id>` and verify that `.tmp/forward-tests/web-article-capture/<case-id>/<run-id>/` does not exist.
- Judge each completed case with its case rubric.
- Write judgments under `.tmp/forward-tests/web-article-capture/<case-id>/<run-id>/judgment.md`.
- Judge strictly. Your goal is to find issues in the Skill and delivered artifacts, not to help the child pass the test.

## Interactive Run Protocol

After dispatch, wait for the child agent's first substantive response.

- If it asks a human-facing question, answer only the question it asked. For numbered choices, choose the number and add at most one short stakeholder preference if needed.
- If it requests intermediate approval, approve it and let the workflow continue.
- Stop the run only when the child is fully out of control: wrong output directory, missing required artifact path, judge-file leakage, inability to continue, or responses that no longer follow the task.
- Do not provide extraction strategy, selector hints, rewrite examples, rubric dimensions, or detailed repair instructions.
- Evaluate the child response from the full subagent tool-returned content, not from a folded or truncated Codex App preview.
- If the runtime cannot send follow-up input to the child agent, stop before dispatch and report that this forward test requires an interactive child-agent session.
- Do not compensate for weak capture behavior by adding strategy instructions to the child-agent dispatch prompt.

## Final Judgment Focus

In final judging, inspect capture quality strictly:

- Isolation Integrity: no judge files, other cases, prior generated outputs, or generated judgments were used by the child.
- Browser Discipline and page-specific Browser Recovery.
- Content Selection: smallest article/main正文 scope, with a clean terminal boundary before post-body modules such as navigation, footer, ads, recommendations, comments, support/contact panels, or page chrome.
- Markdown Package shape and downstream readability.
- Image Package completeness, media ownership judgment, and whether original正文 images are referenced near related text while UI/decorative/non正文 images are rejected.
- Source Notes, capture mode, boundary/tail notes, media uncertainty, and blocked-stage/fallback reporting.
- QA Discipline: validator pass or clear inability reason.
- Research-Scale Stability across the assigned URL set.
- Forward Review Page readability and usefulness.
- Fresh Output Discipline: the run directory did not exist before dispatch and historical outputs were not reused.

Run:

```powershell
python scripts/validate_capture_package.py <run-output> --require-images when-referenced
```

Open or inspect `<run-output>/review.html` before writing final judgment. Check that the review page exposes enough excerpt, tail, capture-mode, and thumbnail evidence to spot boundary drift or non正文 images without reopening every source package.

## Minimal Dispatch Shape

Use this shape when spawning a child agent:

```text
请使用仓库 `SKILL.md` 完成以下网页图文抓取任务：

目标网页：
<paste the assigned URLs or other concrete input values here>

输出目录：
.tmp/forward-tests/web-article-capture/<case-id>/<run-id>/

请自行读取并遵循仓库 `SKILL.md` 的完整网页图文抓取流程。

请为每个网页生成一个 `source.md` + `images/` source package，并生成 `review.html` 汇总原始链接、本地图片缩略图、正文摘录和 package 链接。
```

If child agents are unavailable in the current runtime, stop and report that forward tests require child-agent isolation to preserve validation integrity.

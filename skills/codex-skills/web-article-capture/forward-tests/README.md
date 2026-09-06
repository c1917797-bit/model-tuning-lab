# Web Article Capture Forward Tests

Forward tests are human-orchestrated child-agent runs for checking whether the runtime Skill can capture rendered webpage article/main content and original inline images into compact source packages.

The main agent orchestrates and judges. The isolated capture child performs the capture using repository `SKILL.md`.

## Cases

Each case lives under:

```text
forward-tests/<case-id>/
```

Required main-agent case files:

- `candidate/prompt.md`
- `candidate/input/`

Judge-facing files:

- `judge/rubric.md`

Optional orchestration file:

- `main-agent-prompt.md`

## Running Semantics

Forward tests do not need a Node runner. They are main-agent orchestration prompts, but they do require an isolated child-agent session:

- When the user asks to run forward without specifying a case, the main agent randomly chooses 3 valid case directories when 3 or more exist, otherwise all valid case directories.
- The max child-agent concurrency is 3.
- When the user asks to run a named case, the main agent starts exactly one child agent for that case.
- The main agent reads that case's `candidate/prompt.md` and `candidate/input/`, then sends the child an inline normal-user capture request. Do not ask the child to read `candidate/prompt.md` or discover the case files.
- Each child agent receives only the inlined case task, the assigned input values such as URLs, repository `SKILL.md`, and normal runtime references/scripts required by the Skill.
- Judge-only files stay in the main agent context.
- The main agent must not run candidate capture work in the main thread.
- Do not launch a fire-and-forget worker that cannot receive follow-up input.
- Before dispatch, the main agent must choose a new `<run-id>` and verify that `.tmp/forward-tests/web-article-capture/<case-id>/<run-id>/` does not exist.

Case names are the immediate child directory names under `forward-tests/`.

Use `forward-tests/main-agent-prompt.md` for the exact orchestration wording.

## Candidate Isolation

`candidate/prompt.md` is a main-agent template, not a child-facing path. The main agent must read it and inline the task naturally before dispatch.

The child-agent dispatch prompt should contain only:

- the concrete capture task derived from `candidate/prompt.md`;
- the assigned URLs or other input values copied from `candidate/input/`;
- the instruction to follow repository `SKILL.md`;
- the required output directory under `.tmp/forward-tests/web-article-capture/<case-id>/<run-id>/`;
- at most one short user-requested reminder sentence for that run.

Do not include candidate file paths, strategy explanations, judging criteria, isolation policy, expected answer structure, previous failures, validation mechanics, or judge rubric details in the child-agent dispatch prompt.
Do not tell the child it is being evaluated or forward-tested; present the task as a normal web source capture request.

In Codex, keep the child context isolated:

- Do not use full-history forking for the capture child.
- Spawn the child with a fresh minimal prompt and the inlined task/input values.
- All case inputs should already be in the dispatch prompt; do not mention hidden isolation mechanics to the child.
- Judge isolation after the run by inspecting evidence, logs, and artifacts available to the main agent.

## Output Requirements

Each run writes artifacts under:

```text
.tmp/forward-tests/web-article-capture/<case-id>/<run-id>/
```

Expected deliverables:

- one source package per assigned URL;
- each package contains `source.md` and `images/`;
- local images referenced by `source.md` exist under that package's `images/`;
- `review.html` summarizes every source with original links, local image thumbnails,正文 excerpts, and package links;
- final notes explain generated packages, missing/blocked pages, and validation status.

The main agent validates packages with:

```powershell
python scripts/validate_capture_package.py <run-output> --require-images when-referenced
```

## Judging

Judge with a strict teacher stance. The goal of a forward test is to expose Skill and workflow defects, not to help the child pass.

Inspect:

- whether child isolation was preserved and no judge files, other cases, or previous outputs were used;
- whether Browser-rendered pages were used;
- whether page-specific Browser recovery was attempted before fallback;
- whether captured text is article/main content rather than page chrome;
- whether original正文 images, charts, diagrams, and captions were preserved near related text;
- whether `source.md` files are useful to downstream agents;
- whether `review.html` makes the capture easy to inspect;
- whether the validator passed or a clear reason was recorded.
- whether the run output directory was fresh before dispatch.

Write final judgment under:

```text
.tmp/forward-tests/web-article-capture/<case-id>/<run-id>/judgment.md
```

## Included Cases

- `cloudflare-agents-platform`
- `nvidia-dynamo-disaggregated-serving`
- `nvidia-pc`
- `tair-kvcache-simulation`
- `vllm-kv-cache-serving`

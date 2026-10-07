# Natural quality workload versus HYPIC hot-path coverage

This is a source-grounded scope note for the frozen clean2 41984-context,
2048-token paired LongBench-v2/GSM8K run. It does not amend the predeclared
quality acceptance gate or turn incomplete treatment units into a verdict.

## What the current run actually sends

The pinned evaluator `hypic_quality_eval.py` (SHA256
`9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0`)
constructs ordinary chat-completion requests with model, user prompt,
generation settings and optional GSM8K stop string. Its
`request_one` payload has no HYPIC explicit segment metadata or extra args.
The source is at
`.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_quality_eval.py`.
The clean2 no-cache raw `prompt_tokens` from the frozen first repeat show:

| Dataset | Samples | Min | Median | Max | At least 4096 tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| LongBench-v2 | 127 | 10352 | 22924 | 39642 | 127 |
| GSM8K | 1319 | 77 | 111 | 242 | 0 |

These are measured token counts, not estimates from text length. The HYPIC
source commit is `3ad0967589304cd8fc4e7cff02f48ecc6125c89f` in
`/cache/cch/hypic_vllm_ascend-v0.8.5`. Its `envs.py` default
`auto_chunk_min_tokens` is 4096; `request.py` first accepts explicit
segments, then separator-token/text segmentation, then auto-chunking.
With this evaluator and no explicit segment metadata, GSM8K cannot exercise
the default long-text auto-chunk path. LongBench-v2 meets the length threshold,
but that alone does not prove that the same eligible segment was observed,
materialized and reused.

`patches/runner.py` emits `worker_hot_path` only after an actual batch plan
has passed worker-side prefix-layout verification and
`verified_reqs > 0`; plugin-build and scheduler-active events alone are
weaker evidence. At treatment LongBench-v2 run1 startup, plugin-build and
scheduler-active events were present but no worker-hot event was observed.
The first run's complete rows were independently audited, but the **whole
treatment arm is still running**, so final hot-path coverage and quality
acceptance are open.

## Decision boundary

Keep the 12-unit natural quality protocol unchanged. Its paired scores answer
whether enabling the runtime regresses these natural tasks, subject to the
predeclared row, scorer, input-identity, isolation, activation and release
gates. They do not by themselves prove output quality *while HYPIC actually
skips reusable tokens*. The separate frozen 40 x 1024 shared-prefix
performance run already proves a bounded hot path, but fixed-output
performance is not a 2048-token natural-EOS quality substitute.

If the final treatment evidence lacks four distinct worker-hot PIDs, retain
the original quality-gate failure and all valid raw rows. Report natural-task
scores as descriptive with their activation scope; do not weaken the gate
after seeing scores. A prospective supplemental reusable-segment quality
protocol would need to be declared and run separately, with its own paired
denominator, exact input/output identity, NPU0-3 ownership, isolation and
release evidence. Never pool it into clean2 or relabel clean2 as hot-path
quality validation.

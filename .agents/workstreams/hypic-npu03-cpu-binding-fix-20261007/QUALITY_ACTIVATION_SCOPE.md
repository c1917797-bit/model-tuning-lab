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
`/cache/cch/hypic_vllm_ascend-v0.8.5`. The frozen HYPIC service environment
actually sets `VLLM_ASCEND_HYPIC_AUTO_CHUNK_TEXT=0`,
`VLLM_ASCEND_HYPIC_AUTO_CHUNK_MIN_TOKENS=4096` and
`VLLM_ASCEND_HYPIC_TRUE_POSITION_INDEPENDENT=1`; it does not set
`VLLM_ASCEND_HYPIC_SEPARATOR_TOKEN_IDS`. The source's
`request.py:infer_segments_with_source` accepts explicit segments, separator
token IDs or auto chunks. Its text-separator hint returns an empty segment
tuple rather than a usable partition. The pinned evaluator supplies no
explicit boundaries. Consequently the frozen quality requests have no
usable segment source in this actual configuration: GSM8K is also far below
the 4096-token auto-chunk threshold, and even the longer LongBench-v2
requests cannot auto-chunk because that switch is disabled. This is a
protocol/configuration coverage mismatch, not evidence of an NPU failure.

`patches/runner.py` emits `worker_hot_path` only after an actual batch plan
has passed worker-side prefix-layout verification and
`verified_reqs > 0`; plugin-build and scheduler-active events alone are
weaker evidence. At treatment LongBench-v2 run1, plugin-build and
scheduler-active events were present but no worker-hot event was observed.
The first run's complete rows were independently audited, but the **whole
treatment arm is still running**. The predeclared four-worker hot-path gate
must remain strict; source and frozen configuration now predict it will
not pass for this natural quality workload.

An additional source/configuration constraint matters for any prospective
in-path supplement: the frozen HYPIC service explicitly sets
`VLLM_ASCEND_HYPIC_MIN_REWRITE_TOKENS=4096` (verified from the pinned Docker
snapshot by `binding_off_service.frozen_source`), and
`hypic_vllm_ascend/hotpath.py` rejects a hit that skips fewer than this many
tokens. The public exact-token boundary transport is
`vllm_xargs.hypic_segment_ends`; `ingress.py:parse_segment_ends` requires at
least two strictly increasing ends with the last equal to the actual prompt
token count. Merely adding a boundary hint to the unchanged natural prompts
does not prove a 4096-token reusable hit. Any supplement must preflight its
actual scored requests for sufficient shared token-ID material, explicit
boundaries, context/output headroom, and four distinct worker-hot PIDs.

## Decision boundary

Keep the 12-unit natural quality protocol unchanged. If row, scorer,
input-identity, isolation and release gates pass, its paired scores
descriptively answer whether enabling the runtime regresses these natural
tasks. Without hot-path activation they cannot satisfy the original formal
quality gate or prove output quality *while HYPIC actually skips reusable
tokens*. The separate frozen 40 x 1024 shared-prefix
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

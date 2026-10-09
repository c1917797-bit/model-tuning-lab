# r13 paired quality length delta: descriptive, not causal

2026-10-09 UTC. Read-only replay:
`python3 -B analyze_r13_quality_length_delta.py`. It verifies frozen
dual-audit SHA256
`f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b`,
both arm-result hashes, sample ID and prompt pairing, repetition alignment,
and aggregate scores before reporting counts. Raw responses remain outside
Git. This report does **not** change the frozen REJECT_OR_QUALIFY deployed
quality decision or strict 368/381 hot-coverage FAIL.

Across 381 paired requests, 30 went correct→wrong and 19 wrong→correct.
Candidate length-limit finishes numbered 60 versus baseline 48. Of the 30
regressions, **20** were newly length-limited in the candidate while the
paired baseline stopped naturally. Twenty-three distinct samples had at
least one regression; seven had two or more, none had three. Only two
response hashes were exactly identical across arms.

Of the 368 candidate requests with four-worker hot proof, 29 regressed and
15 improved. **19/29 hot regressions** were newly length-limited. Among
the 13 cold requests, one regressed and four improved; its one regression
was also newly length-limited. Thus cold fallback alone cannot explain
the quality decline. A higher length-limit rate is an observed association,
not proof that truncation caused wrong answers: treatment-induced answer
divergence, scheduling nondeterminism, or other factors remain possible.

Next discriminating work must keep the r13 roots immutable. Inspect a
prospectively selected hot-regression subset with matched worker-level
state/output traces and a same-identity control; any changed cap, cache
capacity, generation profile, or traffic pattern is a **new ruler** needing
its own matching baseline. Do not post-hoc exclude truncated or cold
requests to declare a quality pass.

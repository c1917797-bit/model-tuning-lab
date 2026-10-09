# HYPIC r13 response variability: read-only diagnosis

2026-10-09 UTC. This replays the immutable r13 LongBench-v2 127×3,
max-2048 baseline/candidate responses. It does not rerun an NPU task or
change the frozen quality decision.

## Provenance and method

- Frozen dual quality receipt:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hotpath-quality-cache10r13-dual-audit.json`,
  SHA256 `f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b`.
  The replay checks this hash, the receipt's evidence-valid flag, both
  arm-result hashes, all 127 paired sample/prompt IDs, 3 repetition IDs,
  381 paired request hashes, and the frozen 13 cold scored IDs.
- Run `python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/analyze_r13_response_variability.py`.
  Script SHA256 `a5d60b05514766adda0db26dd4963e3ef3099d81a6bbf787c0ba3d47e810c5b8`;
  focused test SHA256 `d8abb3b7aba8bdfc0cfd0c0b10e48e0ae8a925bc740a5d2c902e3170f745c2b2`.
- For each sample, compare all three within-arm repetition pairs, plus
  same-repetition cross-arm pairs. The hot-only within-arm comparison uses
  the same 357 repetition pairs in each arm for which *both* candidate
  requests have four-worker hot proof. No response text leaves `/cache`;
  only aggregate counts are printed. Three pairs from one sample are
  correlated and must not be treated as 357 independent observations.

## Observations

| Same-sample repetition pairs | No-cache baseline | HYPIC-only candidate |
| --- | ---: | ---: |
| Exact text, all 381 within-arm pairs | 37/381 | 0/381 |
| Same extracted answer, all 381 | 338/381 | 308/381 |
| Same correctness, all 381 | 355/381 | 319/381 |
| Median common text prefix, all 381 | 653 characters | 203 characters |
| Same extracted answer, 357 matched hot-only pairs | 322/357 | 294/357 |
| Same correctness, 357 matched hot-only pairs | 338/357 | 304/357 |
| Common first 512 chars, 357 matched hot-only pairs | 216/357 | 58/357 |
| Median common prefix, 357 matched hot-only pairs | 653 characters | 207 characters |

Across 127 samples, baseline repetition outputs had a longer median common
prefix than candidate outputs for 93 samples; candidate was longer for 24,
and 10 tied. All three extracted predictions agreed for 106 baseline samples
versus 92 candidate samples; all three correctness flags agreed for 114
versus 96. Cross-arm same-repetition exact text was only 2/368 on hot
requests and 0/13 on cold requests.

The prior paired quality audit remains 230/381 versus 219/381, with
`REJECT_OR_QUALIFY` deployment quality and 368/381 strict candidate-hot
coverage `FAIL`. Its hot cohort was 226/368 versus 212/368 correct. The
present replay explains why a cold-only narrative is inadequate: greater
candidate answer variability persists when every candidate request in a
within-arm pair had four-worker hot proof. The no-cache arm itself is not
exactly deterministic over long answers (37/381 exact within-arm texts).

## Boundary and next discriminating check

This is an association, not proof that HYPIC, kernel precision, CANN, HCCL,
or truncation caused a specific wrong answer. Service order, long-generation
numerics, scheduling, and other unisolated effects remain possible. A
candidate-only Prefill/Decode profiler trace verifies actual NPU execution
but cannot establish a baseline-versus-candidate critical-path or quality
cause. The original Prefill `>=47`-column preregistration miss also remains.

If another device test is authorized and physical NPU0–3 are truly idle,
preregister a small matched on/off long-output canary on the *same* pinned
source, prompts, seed and serving identity, with per-request four-worker
activation and token-prefix/answer comparison. Use a fresh root and a
matching control; do not reuse or modify r13 roots, infer a repaired quality
verdict from the subset, or access NPU4–7. Until such a discriminating test,
the quality-regression root cause and full Skill acceptance remain open.

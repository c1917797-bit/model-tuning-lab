# Paired quality gate v1

## Scope and evidence boundary

This gate compares the retained TP4 candidate with a TP4 cumulative control
that differs only by the retained GDN projection fusion and gate/up prefetch
ingredients. It is a quality-isolation control, not the immutable TP8 MTP-off
performance denominator.

The source dataset is `/cache/cch/query_rewrite.jsonl`, SHA256
`a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`.
All 357 rows have an empty `answer` field, so historical aggregate reference
similarity is not a valid quality oracle.

The paired protocol used temperature 0, seed 1024, identical prompts and
sample indices, natural EOS, and 16 question-length-quantile samples. Both
sides completed 16/16 samples with natural stops.

## Automatic comparison

- Exact response match: 11/16.
- Whitespace-normalized exact match: 12/16.
- Normalized character similarity: minimum 0.409044, mean 0.926438,
  median 1.0, maximum 1.0.
- Automatic exact-only gate: fail; manual review required.

## Manual semantic rulings

| Dataset index | Difference | Ruling |
|---:|---|---|
| 26 | Empty/whitespace/EOS representation only | Equivalent |
| 189 | Same unchanged intent `太平年。`; only the compact reason phrase differs | Equivalent |
| 252 | Identical rewritten intent; only `电影版限定` vs `电影版对象` differs | Equivalent |
| 301 | Same title and television-version constraint with reordered wording/punctuation | Equivalent |
| 338 | Identical pronoun resolution and rewritten intent; reasoning length differs | Equivalent |

The other 11 samples are byte-identical. Therefore all 16/16 sampled final
task outputs retain the same intent, facts, constraints, and actionable
meaning, with no material regression found.

Decision: the paired sampled semantic gate passes for the currently retained
GDN projection fusion plus gate/up prefetch stack. This is positive sampled
evidence for `精读无损`; it must not be generalized into a proof over all 357
rows or arbitrary production prompts.

## Evidence

- Baseline capture:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/quality/tp4-npu03-paired-v1/baseline-mmar-nz-nospec.json`
  (SHA256 `83f39689e0b08bc71fc2d642f96b0374f23707ad71822e0a3eb26367d4d2d10c`).
- Candidate capture:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/quality/tp4-npu03-paired-v1/candidate-gdn-fusion-prefetch0p1.json`
  (SHA256 `ed951e6e74f30c774965ba8413ca93307eb6fb7d7ae477101065e2d87ff5f367`).
- Automatic comparison:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/quality/tp4-npu03-paired-v1/paired-comparison.json`
  (SHA256 `a059fc91476afd813a16554820b4636ba6ae1f6e2db85b3fbc140b704bad52d9`).
- Raw review sheet:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/quality/tp4-npu03-paired-v1/paired-human-review.md`
  (SHA256 `ec42c224f46d7ad054ef39be8297913b62eabccea3f0d89a1c87194b26701c30`).
- Capture/compare tooling was committed as
  `7b022a4 test(qwen35): add paired quality evidence tools`.


# r17 repeat-variability retrospective (post-hoc, read-only)

The immutable r17 paired audit remains the decision source:
`hypic-r17-cap1024-full-quality-audit.json`, SHA256
`493f9773d31a49e4f0b7e9c7ba73ea12e9722b4a7409e95c5ea05965b12853b3`.
Its cap-1024/c8 all-request result is 179/381 no-cache versus 174/381
HYPIC-only (−5 correct responses); this retrospective does **not** change
that frozen diagnostic decision or establish 2048/c32 acceptance.

Reproduce without NPU work:

```bash
python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/r17_repeat_variability_audit.py
```

The read-only script checks the immutable paired-audit hash, both arm
contract/result hashes, all 127 sample identities, 381 response-text hashes
per arm, and terminal score/length arithmetic before comparing repeats.

| Observation across 127 matched samples | No-cache | HYPIC-only |
| --- | ---: | ---: |
| Samples whose three correctness values disagree | 10 | 28 |
| Samples with exactly identical text in all three repeats | 8 | 0 |
| Samples mixing stop and length finish reasons | 16 | 34 |

Paired correctness instability occurred in 21 candidate-only samples,
3 baseline-only samples, 7 both-arm samples, and 96 neither-arm samples.
The exact paired McNemar two-sided p-value is 0.000277 **exploratory**:
it was calculated after seeing r17 outcomes, is not a preregistered
acceptance gate, and assumes sample-level independence. Across all 381
paired responses, 19 switched from wrong to right, 24 from right to wrong,
and 338 did not change correctness. Only 1/381 paired response texts
matched byte-for-byte.

This identifies elevated candidate repeat variability as a concrete
technical signal worth testing under r18. It does not isolate whether
HYPIC arithmetic, cache materialization, concurrency scheduling, or
generation stochasticity caused it; temperature zero alone did not make
baseline text deterministic. The current original-source max-2048/c32
LongBench-v2 and GSM8K pair remains the prospective decision evidence.

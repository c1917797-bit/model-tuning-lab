# Quality test contract

Use this reference when creating or reviewing a concrete quality experiment.

## Required identity

- experiment ID and Git commit;
- baseline and candidate model/checkpoint/tokenizer identities;
- container image digest, framework/CANN/driver identity, TP/DP, physical NPU
  IDs, CPU binding, and service configuration hash;
- the single treatment switch and runtime activation evidence.

## Frozen input and evaluator

- dataset names, revisions, absolute external paths, SHA256 hashes, sample IDs,
  order, and expected sample counts;
- prompt and chat template, few-shot policy, preprocessing, answer extraction,
  postprocessor, scorer name/version, and evaluator source commit;
- retry, timeout, failed-sample, duplicate-sample, and resume semantics.

## Frozen generation profile

```json
{
  "max_output_tokens": 1024,
  "ignore_eos": false,
  "seed": 0,
  "temperature": 0,
  "enable_thinking": false,
  "concurrency": 32,
  "repetitions_per_arm_and_dataset": 3
}
```

This example is non-thinking. If thinking is selected, freeze its 2048-token
cap in both arms; an explicit user/dataset contract takes precedence. Record
`stop` and `length` separately; natural stopping does not imply zero truncation.
Do not drop capped or failed samples after seeing results.

Record any additional sampling and stopping parameters. A changed field creates
a new ruler and requires a fresh baseline.

## Per-run evidence

For every arm, dataset, and repetition record:

- expected, attempted, successful, failed, timed-out, retried, and scored
  sample counts;
- correct count and dataset score;
- per-sample ID, prediction hash, extracted answer, score/pass state, finish
  reason, input/output token counts, and error state;
- stop-versus-length finish-reason counts and the length-limit rate;
- raw/detail artifact path and SHA256;
- service instance ID, service configuration hash, and treatment activation
  evidence.

## Aggregate comparison

Report each run and:

- baseline and candidate mean;
- run-to-run range and standard deviation;
- absolute percentage-point delta;
- paired per-sample wins, losses, and unchanged count when meaningful;
- per-category/task deltas;
- confidence interval or paired bootstrap when the scorer supports it;
- within-arm variance and the applicable deterministic/lossless or approximate
  treatment criteria; dataset answer exact-match is not candidate/native token
  equality.

Do not use an arbitrary universal “one percentage point is noise” rule.
Interpret the predeclared tolerance together with the measured baseline
variability, paired samples, dataset size, and critical-category gates.

## Lifecycle

Performance and quality use separate service lifecycles. The sequence below
avoids diagnostic carry-over; it does not require positive performance before a
separately authorized quality study:

1. stop any prior performance/diagnostic service;
2. start the frozen quality baseline, wait for health, record identity, warm up
   if the contract requires it, and run three quality repetitions;
3. stop the baseline;
4. start the one-switch candidate, verify the matching invariant hash and
   treatment activation, and run three repetitions;
5. stop the candidate and prove owned resources were released.

Do not reuse profiler, compilation-capture, RRQR-capture, or diagnostic state
as ordinary quality evidence unless the contract explicitly includes and
matches that state in both arms.

## Final classification

- `pass`: all evidence and thresholds pass for the frozen scope.
- `regression`: a predeclared quality or critical-category gate fails.
- `inconclusive`: evidence is complete enough to inspect but cannot support a
  decision because uncertainty or variability is too large.
- `invalid`: contract drift, missing samples, identity mismatch, artifact
  disagreement, or execution-proof failure invalidates the comparison.

Preserve the exact scope, exclusions, recovery state, allowed claims, forbidden
claims, raw artifact hashes, and next gate.

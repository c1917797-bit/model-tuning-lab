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
- maximum tokenized prompt plus the output cap versus `max_model_len`; a
  larger-context service needs its own matched baseline identity.

## Frozen generation profile

```json
{
  "max_output_tokens": 2048,
  "ignore_eos": false,
  "seed": 0,
  "temperature": 0,
  "enable_thinking": false,
  "concurrency": 32,
  "repetitions_per_arm_and_dataset": 3
}
```

Record any additional sampling and stopping parameters. A changed field creates
a new ruler and requires a fresh baseline.

Before committing to the full suite, record the authorized per-run and total
time limits, a target-NPU throughput or sample-rate estimate, the projected
time for every dataset/repetition/arm, and a margin for service transitions,
audit, and resource release. If the projection is infeasible, stop or request
a newly authorized plan; do not silently shorten the dataset, cap, or number
of repetitions and call it the frozen ruler.

If the ruler and the complete environment fingerprint are unchanged, reuse the
previously completed baseline rather than rerunning it for every candidate.
Verify all three runs per dataset, raw/detail hashes, expected sample counts,
model weights, tokenizer, image/source, physical NPU topology, serving flags,
evaluator, dataset bytes, and generation profile. Cite the original run IDs
and dates. Any mismatch or material runtime drift requires a new baseline.

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
- deterministic-canary equality and within-arm variance.

Do not use an arbitrary universal “one percentage point is noise” rule.
Interpret the predeclared tolerance together with the measured baseline
variability, paired samples, dataset size, and critical-category gates.

## Lifecycle

Performance and quality use separate service lifecycles:

1. finish performance and stop that service;
2. reuse a verified matching frozen quality baseline, or start the baseline,
   wait for health, record identity, warm up if the contract requires it, and
   run three quality repetitions once;
3. stop the baseline;
4. start the one-switch candidate, verify the matching invariant hash and
   treatment activation, and run three repetitions;
5. stop the candidate and prove owned resources were released.

If an upstream gate or time limit terminates the suite before all required
samples and matched arms complete, preserve raw partial rows and their hashes,
record the exact stopping cause, and verify live release. Do not freeze the
incomplete arm as a reusable baseline or calculate a paired quality verdict.

On a shared NPU host, a start/end ownership snapshot cannot establish
uninterrupted isolation for a multi-hour paired suite. Monitor the physical
devices during each arm at a declared interval, identifying the expected worker
PIDs and failing closed on an unrelated PID or an unobservable interval. If an
external process appears, preserve that attempt and its otherwise valid rows as
isolation-failed evidence; do not pair its control arm with a clean treatment.
Prove release of the exact owned container, PIDs, and port separately from
whether the whole lane is available again. Never stop the unrelated workload
without its owner's authorization. A new clean attempt requires a fresh
matching control and treatment under the original ruler.

Do not reuse profiler, compilation-capture, RRQR-capture, or diagnostic state
as ordinary quality evidence unless the contract explicitly includes and
matches that state in both arms.

## Final classification

- `pass`: all evidence and thresholds pass for the frozen scope.
- `regression`: a predeclared quality or critical-category gate fails.
- `inconclusive`: evidence is complete enough to inspect but cannot support a
  decision because uncertainty or variability is too large.
- `invalid`: contract drift, unexplained missing samples, identity mismatch,
  artifact disagreement, or execution-proof failure invalidates the comparison.
- `incomplete-fail-fast`: an upstream rejection or authorized time/resource
  stop ended an otherwise traceable suite before the required samples and
  matched arms completed; this is a coverage state, not a quality score.

Preserve the exact scope, exclusions, recovery state, allowed claims, forbidden
claims, raw artifact hashes, and next gate.

---
name: ascend-model-quality-evaluation
description: Use to design, run, compare, or review Ascend inference accuracy and model-quality evaluations; freeze a paired baseline/candidate ruler, use a 2048-token quality cap, measure baseline variability, and prevent performance evidence from being relabeled as quality evidence.
---

# Ascend Model Quality Evaluation

## Purpose

Produce a reproducible quality decision for an Ascend inference change. This
skill owns dataset accuracy, semantic quality, deterministic canaries, and
quality-regression claims. Use `ascend-benchmark-evidence` separately for
latency, throughput, and resource claims.

## Default Paper-to-Ascend quality ruler

Unless the owning experiment freezes a stricter dataset-specific contract, use:

- baseline and candidate evaluated on the same dataset files, sample IDs,
  order, prompts, chat template, tokenizer, postprocessor, and scorer;
- `max_output_tokens=2048`;
- natural stopping with `ignore_eos=false`; 2048 is a cap, not a requirement
  that every sample generate 2048 tokens;
- `seed=0`, `temperature=0`, and thinking disabled;
- concurrency 32 and three complete repetitions per arm and dataset;
- a fresh service lifecycle for quality after performance measurement;
- LongBench-v2 and GSM8K when reproducing the current HYPIC ruler; include
  NIAH+ or CEval only when their authoritative frozen files and scorers exist.

Changing the output cap, concurrency, dataset revision, evaluator, prompt,
postprocessor, stopping behavior, or generation settings creates a new ruler.
Re-run its baseline; do not pool it with the old ruler.

The completed historical HYPIC evidence used a 1024-token cap. Preserve it as
historical evidence. Never rewrite or relabel those measurements as 2048-token
results.

Before a long suite, tokenize the longest required prompt with the frozen
template and confirm prompt tokens plus the output cap fit the service's
`max_model_len`. A larger context is a new service identity: compare it only
against a matching baseline. Estimate the full baseline-and-candidate wall
time from a representative run on the target NPU (or verified matching runs),
including all repetitions, long outputs, service transitions, audit, and
cleanup. Compare that estimate with per-run and overall time limits before
claiming the suite is feasible. If an upstream fail-fast gate or the time
budget stops the suite, preserve and hash partial rows, release only owned
resources, and label the quality outcome `incomplete-fail-fast`. Partial rows
are not a frozen reusable baseline or evidence of quality pass/regression;
changing the ruler to fit the budget requires a new matched baseline, and
extra time or devices require their own authorization.

## Protocol

1. Establish an environment fingerprint with
   `ascend-npu-environment-orientation`.
2. Declare the baseline denominator, candidate switch, datasets, scorer,
   quality metrics, failure thresholds, and allowed decision scope before the
   candidate run.
3. Freeze dataset bytes and hashes, sample IDs and order, prompt/chat template,
   tokenizer revision, preprocessing, answer extraction, postprocessing,
   request concurrency, generation settings, timeout/retry policy, and
   evaluator revision.
4. Run a deterministic short canary before the full suite. For outputs of at
   most 512 tokens where deterministic execution is expected, require zero
   within-arm variance and exact baseline/candidate token equality.
5. Measure the baseline three times once, or reuse three completed runs whose
   environment, generation, dataset, evaluator, and service fingerprints match
   exactly and whose raw/detail hashes still verify. Record the original run
   IDs and dates, per-sample results, aggregate score, run-to-run range,
   failures, timeouts, retries, finish reasons, and length-limit rate.
6. Stop the service used for performance or baseline work. Start the exact
   frozen candidate configuration, prove the intended treatment is active, and
   run the same quality suite three times.
7. Compare paired samples as well as aggregate scores. Report each run, mean,
   standard deviation or confidence interval when supported, absolute
   percentage-point delta, baseline repeat range, and per-category regressions.
8. Classify the quality result as `pass`, `regression`, `inconclusive`,
   `invalid`, or `incomplete-fail-fast`. Preserve negative and incomplete
   results without treating partial-sample accuracy as a verdict.

## Decision gates

A quality pass requires all applicable conditions:

- every required sample has a traceable result and the raw/detail hashes match
  the summary;
- baseline and candidate contracts match except for the declared treatment;
- no material dataset, category, long-context, or length-limit cliff is hidden
  by the aggregate mean;
- the candidate delta is within the predeclared tolerance informed by measured
  baseline variability;
- deterministic canaries satisfy their exact-match requirement;
- treatment activation and physical Ascend execution are proven.

If a required dataset is unexpectedly missing, the service changes identity
during the run, the 2048-token cap is not actually applied, or artifacts
disagree, fail closed as `invalid` or `inconclusive`; do not substitute another
dataset silently. A documented upstream/time-budget stop is
`incomplete-fail-fast`, not a quality comparison.

## Evidence and claims

Store concise contracts and summaries in Git. Keep datasets, raw responses,
weights, and large traces outside Git, recording paths, hashes, retention, and
the source commit.

Allowed wording is scoped, for example: “no material quality regression was
observed on this frozen suite within measured baseline variability.”

Do not claim universal losslessness, mathematical equivalence, or quality
preservation across models, hardware, topology, traffic, or output caps.

For the reusable contract and report fields, read
[quality-test-contract.md](references/quality-test-contract.md).

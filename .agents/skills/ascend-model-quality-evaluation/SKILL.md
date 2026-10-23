---
name: ascend-model-quality-evaluation
description: Use to design, run, compare, or review Ascend inference accuracy and model-quality evaluations; freeze a mode-appropriate paired baseline/candidate ruler, measure baseline variability, and prevent performance evidence from being relabeled as quality evidence.
---

# Ascend Model Quality Evaluation

## Purpose

Produce a reproducible quality decision for an Ascend inference change. This
skill owns dataset accuracy, semantic quality, deterministic canaries, and
quality-regression claims. Use `ascend-benchmark-evidence` separately for
latency, throughput, and resource claims.

## Default Paper-to-Ascend quality ruler

The owning experiment and current user instructions choose the ruler; do not
replace an explicit contract with a Skill default. For a new experiment without
an explicit dataset-specific contract, use:

- baseline and candidate evaluated on the same dataset files, sample IDs,
  order, prompts, chat template, tokenizer, postprocessor, and scorer;
- thinking disabled: `max_output_tokens=1024`; thinking enabled: cap 2048;
- natural stopping with `ignore_eos=false`; the limit is a cap, not a required
  output length or proof that every response reaches EOS;
- `seed=0`, `temperature=0`, and non-thinking by default; preserve an explicitly
  selected thinking mode in both arms;
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
4. Declare whether the treatment is lossless or intentionally approximate.
   Use exact baseline/candidate token equality only for a predeclared lossless
   deterministic control under the same semantics. For approximate reuse such
   as PIC, validate same-semantics numerical primitives independently, measure
   within-arm variability, and judge task quality with the frozen scorer and
   tolerance; different full-context output tokens alone are not a defect.
5. Measure the baseline three times to establish its own NPU variability.
   Record per-sample results, aggregate score, run-to-run range, failures,
   timeouts, retries, finish reasons, and length-limit rate.
6. Stop the service used for performance or baseline work. Start the exact
   frozen candidate configuration, prove the intended treatment is active, and
   run the same quality suite three times.
7. Compare paired samples as well as aggregate scores. Report each run, mean,
   standard deviation or confidence interval when supported, absolute
   percentage-point delta, baseline repeat range, and per-category regressions.
8. Classify the quality result as `pass`, `regression`, `inconclusive`,
   or `invalid`. Preserve negative and incomplete results.

## Decision gates

A quality pass requires all applicable conditions:

- every required sample has a traceable result and the raw/detail hashes match
  the summary;
- baseline and candidate contracts match except for the declared treatment;
- no material dataset, category, long-context, or length-limit cliff is hidden
  by the aggregate mean;
- the candidate delta is within the predeclared tolerance informed by measured
  baseline variability;
- lossless deterministic controls satisfy their declared exact-match rule;
  approximate treatments satisfy their applicable numerical and task criteria;
- treatment activation and physical Ascend execution are proven.

If a required dataset is missing, the service changes identity during the run,
the frozen generation cap or thinking mode is not actually applied, or artifacts disagree, fail closed
as `invalid` or `inconclusive`; do not substitute another dataset silently.

## Evidence and claims

Store concise contracts and summaries in Git. Keep datasets, raw responses,
weights, and large traces outside Git, recording paths, hashes, retention, and
the source commit.

Allowed wording is scoped, for example: “no material quality regression was
observed on this frozen suite within measured baseline variability.”

Do not claim universal losslessness, mathematical equivalence, or quality
preservation across models, hardware, topology, traffic, or output caps.

Performance and quality are separate evidence axes. A performance regression
blocks an acceleration claim, not a separately authorized quality evaluation.
Neither axis can excuse the other at final acceptance. Keep every expected
sample, request failure and length-limit result in the declared denominator.
For interrupted runs, see the durable-evidence rule in
`ascend-benchmark-evidence`; request success is not task correctness.

For the reusable contract and report fields, read
[quality-test-contract.md](references/quality-test-contract.md).

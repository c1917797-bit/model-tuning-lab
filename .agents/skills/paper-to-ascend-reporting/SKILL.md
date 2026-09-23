---
name: paper-to-ascend-reporting
description: Use when writing, reviewing, or finalizing an evidence-bound Paper-to-Ascend or algorithm-piercing report from measured experiment artifacts; preserve the colleague-style Step 0, deployment, commands, measured-results, conclusion, and troubleshooting structure without inventing data.
---

# Paper-to-Ascend Reporting

## Purpose

Turn a completed, rejected, failed, or still-running Paper-to-Ascend experiment
into a report that a maintainer can audit and reproduce. Preserve the useful
shape of the successful HYPIC practice report while strengthening its evidence
boundaries.

Read [references/report-template.md](references/report-template.md) before
drafting a report.

This skill reports experiments. Use paper-to-ascend and the Ascend experiment
skills to select and run the work; do not silently launch missing measurements
from a reporting request.

## Evidence contract

Classify every input before using it:

- **current measured evidence:** raw request rows, evaluator output, benchmark
  summaries, profiles, manifests, logs, hashes, and live resource evidence from
  the experiment being reported;
- **historical reference:** a colleague report or previous experiment used only
  for protocol or magnitude comparison;
- **paper claim:** a result reported by the publication;
- **interpretation:** a conclusion derived from the preceding evidence.

Never merge these categories into one result column. A historical or paper
number is not a current measurement.

For each current numeric result, retain the artifact path, sample/repetition
count, aggregation method, and SHA256 when the experiment ledger provides it.
Recompute table deltas from the reported baseline and treatment values. If the
raw evidence and a summary disagree, report the disagreement and stop the
affected claim.

## Workflow

1. Decide whether the output is a final, progress, negative-result, or
   inconclusive report. A progress report must name every unfinished gate.
2. Freeze the report scope: paper, implementation, model/checkpoint, image and
   runtime, hardware and topology, baseline, treatment, workload, datasets,
   scorer, repetitions, and decision thresholds.
3. Build an evidence ledger with separate current, historical, paper, and
   interpretation entries. Mark missing evidence as "not measured",
   "not available", or "invalid"; never convert it to zero.
4. Reconstruct the exact successful launch, benchmark, quality, profiling, stop,
   audit, and resume commands from scripts or logs. Remove credentials and
   verification tokens, and label every redaction.
5. Prove the one-switch A/B identity. When several groups are used, explain
   which comparison answers which scientific question.
6. Report all repetitions plus mean and dispersion. Keep fixed-output
   performance sampling separate from deterministic, EOS-respecting quality
   evaluation.
7. Show mechanism evidence before attributing a speedup to the paper method.
   A faster endpoint without activation or profile evidence is correlation, not
   mechanism proof.
8. State decisions independently for feasibility, activation, performance,
   quality, attribution, adoption, and generalization.
9. Audit the draft against the raw artifact counts, hashes, formulas, resource
   isolation, and completion state before calling it final.

## Claim rules

- Use "regression observed", "no material regression observed", or
  "lossless proven" precisely. Do not call a point estimate lossless unless an
  explicit equality contract is satisfied.
- Do not average incompatible runs or compare different models, card counts,
  images, capacity settings, datasets, prompts, scorers, or traffic shapes as
  if they were one A/B.
- State whether a percentage is relative, percentage-point, or a ratio.
- Include failed requests and excluded samples with reasons.
- Separate startup failures and tooling faults from algorithm failures.
- Never reuse the HYPIC sample's paths, commands, versions, device IDs, or
  numbers in another report unless they are independently present in that
  experiment's artifacts.
- Do not leave TBD, TODO, 待补充, ellipses standing for required command
  arguments, or empty result cells in a final report.
- Do not claim deployment readiness while any required gate is pending,
  invalid, or unsupported.

## Output standard

Use the colleague-style narrative order:

1. title and provenance;
2. Step 0. 环境准备;
3. Step 1–3. 拉起各组配置服务 → 跑测试;
4. baseline deployment and test commands;
5. treatment deployment and test commands;
6. sequential execution flow;
7. measured performance, quality, and mechanism/profile results;
8. comparison with historical or paper results;
9. scoped decision and conclusion;
10. errors, rejected attempts, evidence index, and exact recovery commands.

Keep commands executable, but prefer checked-in scripts as the canonical command
when a long inline shell block would drift. If a section is inapplicable, say
why; do not fabricate a substitute dataset or metric.

## Completion gate

A final report is ready only when:

- every result is traceable to current evidence;
- baseline/treatment identity and differences are explicit;
- repetitions, dispersion, failure counts, and formulas reconcile;
- quality language matches its measured acceptance boundary;
- historical and paper numbers are visibly separate from current results;
- mechanism and profile scope support the attribution;
- exact successful and recovery commands are present and secrets are absent;
- resource release evidence is included;
- allowed, forbidden, and still-unproven claims are stated;
- no placeholder remains.

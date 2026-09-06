---
name: paper-ingestion
description: Use to extract a research paper into implementable inference hypotheses, separating paper claims, required model/runtime mechanisms, benchmark assumptions, and non-transferable parts before Ascend work begins.
---

# Paper Ingestion

## Purpose

Convert a paper from prose into a bounded engineering hypothesis. This skill is
for understanding what the paper actually changes and what must be true before
an Ascend implementation is worth attempting.

## Workflow

1. Identify the paper, version, source, and any code/artifact links used.
2. Extract the claimed optimization target: training, inference, model
   architecture, runtime scheduler, KV/cache layout, operator, kernel,
   communication, or system configuration.
3. Summarize the mechanism in implementation terms: inputs, changed dataflow,
   state added or removed, algorithmic complexity, and expected overhead.
4. List required prerequisites: checkpoint structure, tokenizer/model config,
   dtype/quantization, serving framework features, CANN/operator support,
   hardware topology, and whether retraining is required.
5. Separate portable ideas from paper-specific assumptions such as GPU-only
   kernels, unavailable training data, custom checkpoints, or benchmark-only
   shortcuts.
6. Translate the paper into one or more candidate hypotheses, each with one
   primary variable and an expected bottleneck it should improve.
7. Record uncertainty explicitly. Unknown architecture or runtime prerequisites
   route to `ascend-architecture-fit` or `ascend-source-map`, not implementation.

## Output

Produce a concise paper ingestion note suitable for an experiment record or
workstream handoff:

- paper identity and source;
- mechanism summary;
- required model/runtime/hardware prerequisites;
- expected performance path and possible new overhead;
- whether retraining is required;
- candidate first hypothesis;
- evidence gaps and next checks.

## Boundaries

- Do not treat author benchmark claims as local evidence.
- Do not infer checkpoint support from paper compatibility alone.
- Do not open a tuning workstream until the first hypothesis passes the
  Paper-to-Ascend applicability gate.

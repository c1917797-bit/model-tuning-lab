# Architecture and bottleneck before paper ranking

Read before ranking or resuming an Ascend paper portfolio, especially hybrid GDN
models, low-bit caches, and prefill-only kernels. This reference supplements the
existing validation DAG and causal-recovery rules; it changes selection, not
acceptance thresholds. Practice source: October14 Qwen paper reassessment and
five-round rehearsal follow-through.

## Selection record

Bind the installed checkpoint config and original weight identity, model/runtime
classes, exact image/CANN/operator sources, workload and supported plugin seam.
A family name such as Qwen3.X does not identify attention form or tensor shapes.
For a hybrid model, map each method separately to GDN prefill/chunkwise, GDN
recurrent decode, full-attention KV/readout, MLP/projection or communication.
Layer count is not elapsed-time share. Do not confuse GDN recurrent state with
a token-growing Transformer KV cache.

Before expensive adaptation, record:
- the paper formula/dataflow and official source/version/license;
- the actual worker/operator call chain and affected shapes/stages;
- comparable target-model profiling or a bounded experiment that will establish
  the missing opportunity; identify its next observable decision;
- new packing, conversion, scratch, synchronization, cache and lifecycle costs;
- the shortest remaining path to full-model and task acceptance.

Architecture compatibility and official code justify consideration, not a
high expected gain. Missing local opportunity stays unresolved. Use a bounded
diagnostic to decide it; do not reject a paper just because the evidence is absent.
Reuse upstream and author implementations where appropriate. Necessary algorithm
ports may need scoped operators, ABI/layout or lifecycle adaptations.

## Benefit and control conditions

Kernel-time sums are diagnostic aggregates, not a critical-path fraction.
Prefill solve speedups do not imply recurrent decode speedups. Batch enlargement,
MTP/speculation, offload or specialized workload gains do not establish a
same-concurrency fixed1024 improvement when those conditions are out of scope.

For a proved removable critical-path fraction p and local speedup s, an idealized
upper bound is 1/(1-p+p/s). A 10% speedup needs p*(1-1/s)>=1-1/1.1 before new
overhead. Apply only with justified critical-path measurements; overlap and
serving throughput may invalidate the simple bound. No fixed12% universal gate.
Count whole-model throughput and separately report TTFT/TPOT.

Low-bit storage is distinct from arithmetic support. Packed INT2 storage can
reduce reads while unpack/dequantize and floating computation add cost. Inspect
the actual fused or split path against the production native operator. Do not
claim INT2 compute acceleration from two-bit codes or capacity savings from a
layout that retains an uncharged full-sized second cache.

## Portfolio choices

Rank by measured opportunity, task-quality risk, source/port readiness, remaining
integration cost and deadline slack. Publication year alone proves neither value
nor obsolescence. Prior work invested is not a reason to continue.

Two methods sharing the same unsupported packed backend, graph binding or
precision risk are correlated fallbacks; prepare a genuinely different route
when available. Historical HYPIC is a migration example, not this campaign's
new accepted result. Keep verified subtarget gains available for measured
composition; require D/A/B/A+B interaction and final-quality evidence.

After a failure choose the next node from causal evidence: repair a proved code
defect, obtain discriminating evidence for an unknown cause, or close a valid
measured configuration without extrapolating to all implementations/environments.
Do not grant a paper PASS from a different algorithm's substrate.

## Rehearsal and source proof lessons

Software/fault-injection coverage can expose preparation defects but does not
satisfy NPU, whole-model, performance or task gates. Test the actual aggregate
cold entry and real producer-to-consumer contract; helper mocks may miss schema
fields or exact interpreter/import ordering.

A cache file, symbol name or byte string is not proof that a process loaded the
candidate kernel. Bind registration, actual matching object, generated source,
returned binary and actual loaded module/maps. Persist partial diagnostic
evidence on exceptions, with a separate status from complete numerical PASS.

A no-device tokenizer dependency can import genuine CPU Torch/Triton. Distinguish
module/class definition from lazy device activation using source-bound behavior,
FD/library state and actual target execution. Do not fake packages to pass
imports. A guard can itself be wrong; retain its failed run and repair the
contract using a discriminating positive/negative case.

When an immutable dependency supplies several return values/configs, test the
actual execution configuration, not only source-read success. Reuse exact valid
prerequisite outputs and preserve the original failed parent.

## Quality and verification

Implementation agreement with an independent quantized reference establishes
port correctness, not dense-model task accuracy. Compare the final same model
and generation policy on current authorized tasks, smoke then full; report
percentage points and relative loss. The user's task1% allowance never relaxes
intermediate tensor/state tolerances.

Keep new deadlines explicit; never silently edit old sources or reset historical
clocks. An output claim must match actual stage/command/source/run identity.
Validate changed skill links and the repository skill tree, then checkpoint the
coherent stage. Specific evidence, scope and current queue belong in workstream
records, not repeated copies in several skills.

# Profiler lifecycle and evidence boundaries

Use this reference when adding worker-side collection or diagnosing start, stop,
export, or parse failures in a live inference service.

## Inspect the backend that actually runs

Resolve the actual imported backend, including editable-install mappings, and
bind its source to the serving image. Trace each requested option through the
wrapper into the backend constructor. A configuration class accepting a field
does not prove that the worker forwards or uses it.

In the pinned HYPIC R41 image, the official TorchNPU wrapper mapped
`torch_profiler_with_stack` to `with_modules`; it did not forward the advertised
record-shape or schedule fields. This is a version-specific source observation,
not a recommended configuration for other stacks. Fake-backend tests can prove
that mapping and rejection behavior; they cannot prove NPU collection or stability.

## Treat stop and export as functional gates

Separate start, record, stop, export, parse, request completion, and resource
release. An HTTP 200 from start/stop, an initially successful stream response,
or files appearing on disk does not establish a valid capture.

For each required worker, bind metadata and trace to its real rank and process.
Require a completed export, parseable CPU and device timeline, and no caught
profiler error, worker crash, or missing rank. Preserve incomplete trees as
failure evidence; do not rank bottlenecks from them as if collection succeeded.

Read the cap boundary in the actual worker call order. A counter checked with
`>` before model execution can stop on the next entry rather than after that
many completed model steps. Choose the window from the source semantics and
record the realized interval; do not infer it from the option name.

## Use a failure to choose one falsifiable successor

R41 observed four worker CPython segmentation faults during profiler stop,
with Python-tracer artifacts present and no final metadata or parsed timeline.
R42 changed only the official Python/module-tracing flag while retaining the
CPU/NPU activities and measurement protocol. That candidate passed CPU/HOST
configuration checks but was rejected by the budget gate before allocation.
It therefore provides neither a validated workaround nor a proven root cause.

For a similar failure, preserve the original source, raw tree, log phase, and
worker identities. Preregister one material configuration change and a concrete
disproof signal before a new root. A changed failure phase is useful evidence;
an unchanged retry or a passing constructor alone is not a repair.

## Reconcile transport and cleanup separately

Count actual attempts and outcomes from the durable request journal. A final
summary can remain empty when a stop exception interrupts assignment: in R41,
zero summarized responses coexisted with forty attempted, failed requests.
Do not translate an incomplete summary into zero attempts or successful work.

Audit exact owned-resource release independently even when capture fails.
A profiling failure does not establish an algorithm numerical failure, a paper
rejection, or a service speed result. Profiled timings also cannot replace an
uninstrumented matched performance comparison.

## Admit the whole diagnostic before implementation work expands

Estimate startup, actual target warmup, collection, export, parsing, independent
audit, and cleanup from observed runs. Include both arms and clock/transport
margin when a pair is required. Establish the latest safe start before building
a large adapter, then recheck immediately before allocation.

A preallocation budget rejection means no device trial occurred. Preserve the
candidate and its unexecuted contract, record the expired admission condition,
and continue useful offline work. Do not shrink the workload, remove a guard,
or extend the deadline merely to fit the next attempt.

## Case provenance and validation scope

- [R41 failure and independent release](../../../workstreams/hypic-independent-20261013/R41_G1_R1_CAPTURE_FAILURE_20261026.json)
- [R42 single-variable plan](../../../workstreams/hypic-independent-20261013/R42_NO_PYTHON_TRACER_SINGLE_VARIABLE_PLAN_20261026.json)
- [R42 CPU/HOST readiness](../../../workstreams/hypic-independent-20261013/R42_CAPTURE_HOST_READINESS_20261026.json)
- [R42 preallocation rejection](../../../workstreams/hypic-independent-20261013/R42_G1_R1_PREALLOCATION_REJECTION_20261026.json)

These records support a reusable collection and failure-classification workflow.
They do not establish HYPIC performance success or acceptance of the full Skill tree.

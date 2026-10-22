# Saved projection diagnostic summary extractor — local preparation

This package prepares a small, stdlib-only, read-only evidence extractor for the
actual continuation reader output. It does not run the reader, import any model
code, contact the remote host, create an owner, or access an NPU. Only the new,
exclusive summary output is written when MAIN later executes it.

## Current source

- `extract_projection_summary_v1.py`: 18938 B; SHA-256
  `2a422bcdf74535bf7def49ebcf14780183585cfde732f5a23feae7ecbb33d4f9`.
- `SCHEMA_EXPECTATION_v2.json` is the current exact interface description.
- `LOCAL_CHECKS_v2.json` records Python 3.9 syntax and pure parser/presence helper
  checks. No complete synthetic diagnostic was created, no actual diagnostic was
  read, and neither main nor the original 15/6 reader controls was executed.
- The original unversioned expectation/check records are retained as preparation
  history for the earlier helper bytes. They are not the current deployment set.

The actual diagnostic has not been fabricated or supplied by this preparation.
An independent static review, when present, has its own limited scope and cannot
approve the runtime inputs or any experiment.

## Input and output

Use one exact complete Ref3 JSON operand with keys `path`, `bytes`, `sha256`.
The only accepted evidence path is:

`/opt/host/vnf/austinov/run-bole-projection-reader-v2-continuation_20261022T120055Z/PROJECTION_DIAGNOSTIC.json`

The input's schema must be `bole.completed-projection-within-arm-diagnostic/v1`.
Its bound SOURCE, SOURCE_AUDIT and final reader Ref must match the actual frozen
identities already recorded in `continuation_actual/QUALIFIED_SOURCE_REFS.json`
and `continuation_reader_final_v1/FINAL_MANIFEST.json`. Its host RESULT must have
the exact new continuation path. The actual result SHA/bytes are read from the
diagnostic, not invented here.

Invocation, after MAIN has reviewed and deployed the source:

```text
/usr/bin/python3 -I -B <reviewed-extractor-absolute-path> \
  --diagnostic-ref '<exact actual diagnostic Ref3 JSON>' \
  --output <new absolute summary-file-path>
```

The output parent must already be an ordinary existing directory. Existing files
are never overwritten; source, original diagnostic and historical results are
never edited. The diagnostic is read in full twice, with complete SHA, byte count,
file identity and ancestor checks. The extractor source is likewise checked before
and after. Duplicate JSON keys and nonfinite JSON values are rejected.

Bounds: input 32 MiB, summary 256 KiB, address space at most 512 MiB, CPU at most
30 s, wall check 60 s, CORE 0. Lower inherited resource limits are retained.
No child processes or fallback execution are used. If a schema, identity, size,
or presence check fails, preserve the failure and inspect the actual data; do not
weaken the diagnostic reader or manufacture missing fields.

## What the summary retains

- Each rank's first observed native-boundary difference, first observed projection
  hash difference, and first availability difference, without a causal conclusion.
- All five stages for both generations: `projection_input`, `quant_return`,
  `pre_reduce`, `post_reduce`, `projection_return`, including complete producer SHA,
  actual logical shape/dtype/bytes/geometry, and explicit unavailable reasons.
- Actual per-generation layer/custom/quant class and object metadata, method roles,
  original call trace, exceptions and supported caller reduction sites. The five
  runtime/host-source mappings are retained in order for `source_index` lookup.
- Original norm→input, quant→pre-reduce, post-reduce→return and return→outer joins.
- The original ten same-generation cross-rank comparisons with all four observations.
  Different TP ranks may contain different shards; equality is not required.
- Native0 full131 input hashes, core/norm/out-projection last8 numeric summaries,
  rank COMPLETE Ref, HTTP request/token comparison and all twelve original limitations.
- All twelve state endpoint transitions per rank. Their `changed_hashes` list is
  summarized by count, first change and the SHA of the entire canonical list; the
  full list remains in the exact source diagnostic. No full-list equality claim is
  inferred from that presentation reduction.

Every optional displayed field is represented as `{present, value}`. Missing
means `{present:false, value:null}`; explicit null and explicit false remain
`present:true`. This includes the historically missing
`interval_contains_unobserved_work` and unavailable join fields. Two unavailable
stages may have equal availability while their hash comparison remains null.

## Interpretation boundary

The original reader's integrity flags are copied under `saved_reader_flags`.
This extractor verifies the exact diagnostic document and its own source only;
it does not reopen the reader's thousands of nested evidence files, replay state,
recompute tensor hashes, or independently reproduce the original qualification.

Projection full-tensor hashes are source-bound producer witnesses without new raw
values. The retained last8 BF16 metrics cover those slices only. Shapes can change
through padding, reduce-scatter, gather or native processing. A hash difference
does not imply a difference over an identical logical span. The summary introduces
no magnitude threshold and no task-accuracy interpretation of a tensor error.

Weight/bias version, allocation and storage metadata do not prove weight bytes or
backend-private format. Caller source is bound; collective callee, HCCL transport
and kernel are not independently source-pinned or directly observed. Missing
supported reduction sites do not prove absence of other communication. Blocking
device-to-CPU observations can alter scheduling.

The historical complete ON/OFF pair remains recorded FAIL, with its exact old
EXECUTION Ref. That historical record is explicitly marked **not reopened by this
extractor**. The actual diagnostic must retain `original_pair_gate_replaced=false`
and `original_pair_gate_rerun=false`. Numerical, paired-state, performance,
formal-performance, model-ready and task-accuracy flags remain false.

The output status is `SAVED_DIAGNOSTIC_SUMMARY_NOT_GATE`. No runtime or admission
PASS is created by this package.

# Native projection observer v1 — source-only draft

## Scope and status

This helper observes the existing layer-0 `out_proj.forward` call during each of
two genuine native prefills. It does not perform another GEMM or collective,
change a tensor, replace an original return value, alter a runtime option, or
split a fused operator. It is a diagnostic observer, with no numerical,
ON/OFF-pair, performance or final-task qualification. Its synchronous device
reads and Python tracing can change execution timing; observed repeatability
with this observer would not establish repeatability of an unobserved run.

The previous real boundary result narrowed the first *observed* divergence to
the interval after layer-0 gated norm and through projection return. This helper
can subdivide that interval only when the actual native branch exposes Python
locals. The five installed source files remain exact Ref3s, verified at runtime;
the communication callee and HCCL kernel are not independently pinned by this
observer. A source-bound callsite is not an HCCL-kernel observation.

## Parent integration contract

`create(owner, environ)` is import-safe and default OFF. An inactive or absent
`BOLE_NATIVE_PROJECTION_PROBE_ENABLE` returns `None` before accessing `owner`.
The active value must be exactly `1`, and
`owner.manifest['projection_probe_profile']` must exactly equal `DECLARATION`.
The parent source validator must retain its independent declaration/flag and
source-lineage validation; the inactive factory itself deliberately does not
inspect the manifest.

An active factory constructs the observer and verifies source/owner identity;
it installs nothing. After its original source checks and hook installation, the
parent calls `observer.install()`. The parent must put construction and explicit
installation under its existing failure-restoration guard. Call
`observer.before_retire(generation)` after the parent's original native-removal
proof and before writing original `RETIRE`. G2 retirement restores the instance
forward. Parent `uninstall()` should call observer `uninstall()` first; that
operation is idempotent after successful restoration. Parent G2 `COMPLETE` adds
`projection_observer_restored: true` and `projection_records: 2` only after the
original lifecycle and restoration conditions have passed.

The manifest adds the independently reviewed helper and profile, and preserves
the existing `projection_runtime_refs`. That is an exact map keyed by the five installed
guest paths. Its complete reference set is also emitted as a sorted list in each
record. Parent code must preserve original observer semantics, complete original
148-file layout, original source checks, numerical gates, cleanup, and budgets.

## Actual ownership and trace selection

The selected owner must identify the real model and current request. Required
state includes `scope is True`, generation 1 or 2 equal to retired-generation
count plus one, no pending native layer, and `native` containing exactly layer 0
whose GDN object, request object and actual 131-token metadata match the owner.
The original gated-norm raw witness must already exist, and original projection
raw witness must not yet exist. The wrapper's original bound method, actual
quant method object and actual custom object remain strongly held and checked.
Calls outside the native scope pass directly to the original bound forward.

Source binding compiles the entire exact installed module without executing it.
The actual method's code object must equal the uniquely located compiled code;
the actual function module globals and bound receiver must also match. This
uses the worker's own Python runtime. Recorded
`sha256(marshal.dumps(code))` values are producer-runtime witnesses, not
cross-version host-recompilation proofs.

Within the one original forward call, the trace accepts only pinned method code,
the exact receiver, actual `quant.apply(layer=target_layer, ...)`, and a live
selected original-call ancestor. Other layers sharing a method code or a quant
object do not acquire this scope. There must be no pre-existing trace or profile.
The helper removes only its own retained trace callable. A foreign replacement
causes sticky failure and is never overwritten. Python trace callback failures
can automatically clear tracing; that is accepted only after the helper itself
has already failed. The original bound method is called exactly once with the
original arguments, and its original result is returned directly.

## Five stages and their meanings

| Stage | Actual observation point | Absence rule |
|---|---|---|
| `projection_input` | Original bound forward's actual `input_`, immediately before the one native call | Required |
| `quant_return` | The selected actual quant method frame's return argument | Absent for an executed fused branch |
| `pre_reduce` | The caller's actual `output_parallel` at the native AST reduction-call line, read immediately before execution | Absent for a fused call or a branch with no selected reduction |
| `post_reduce` | First source-assigned `output` after that exact callsite; for Sequence inline return, the actual frame return argument | Absent only if no selected reduction executes |
| `projection_return` | Original selected projection frame's actual returned tensor; tuple handling follows actual `return_bias` | Required, independently read |

Each observed stage reads the actual tensor's complete logical byte extent and
records actual shape, stride, offset, dtype, device, object and storage geometry.
It does not assume that a custom branch's intermediate tensor has 131 rows.
The existing original 131-row outer witnesses remain unchanged. The same tensor
read at two moments incurs two complete charges. In-place collective mutation
does not turn the earlier `pre_reduce` witness into a deferred read.

For MatmulAllreduce or fused Sequence execution, no local Python result exists
between matmul and reduction: `quant_return` and `pre_reduce` are explicitly
`{observed:false, reason:'fused_no_python_local_result'}`. The one fused call is
left intact. For a native no-reduction branch the missing pre/post reason is
`no_reduce_callsite_executed`. All other missing required stages, duplicate
stages, wrong order, wrong scope or unresolved selected callsites fail closed.

Flashcomm's first output after reduce-scatter is observed before its later
all-gather/cropping. Sequence's inline `return all_reduce(output_parallel)` is
observed at that selected frame's return. Final projection return is a separate
stage in both cases. These labels still denote Python callsite boundaries.

## Exact record layout

Each generation writes one exclusive `G1-PROJECTION-INTERNAL.json` or
`G2-PROJECTION-INTERNAL.json` through the original `owner.writer`. It is inside
the existing `BOUNDARY-R{rank}` directory and appears after original
`Gg-RAW-layer0_gated_norm.json`, before original projection `.bin` and `.json`.
No new directory, unaccounted output path or raw file is created. The final
closure becomes exactly 150 files: 132 JSON and the same 18 raw files; COMPLETE
contains 149 prior Refs and does not reference itself.

The outer envelope keeps the original boundary schema, source SHA, rank, PID,
generation, event and qualification fields. `event` is `PROJECTION-INTERNAL`.
The **whole serialized envelope including its newline** is bounded by 8192
bytes before exclusive publication. There is no truncation or dropped field.

The inner `record` keys are:

```
schema, generation, request, request_object, active, runtime_refs, roles,
calls, exceptions, stages, reductions, read_bytes_generation,
read_bytes_total, code_hash_algorithm, outer_records, trace_restored,
original_bound_calls, new_raw_bytes, weight_bytes_hashed,
source_bound_python_callsites_only, collective_implementation_pinned,
numerical_qualified, formal_performance, diagnostic_only
```

`active` identifies actual layer/GDN/quant/custom objects and classes, prefix,
actual layer TP rank/size and booleans, and weight/bias metadata. The weight
metadata contains geometry and the actual tensor version when available;
`bytes_hashed:false`, `format_observed:false`, `format:null` remain explicit.
Same geometry/version is not proof of equal weight bytes or hardware format.
Layer TP metadata is not a proof of the communication callee's actual group.

Each role has `role, source_index, qualname, receiver, code_sha256, first_line`.
`source_index` addresses the sorted `runtime_refs` list. Calls are ordered
`[role, 'call'|'return']` pairs. Exceptions contain only bounded role/line/type,
without values or traceback text. Caught native source exceptions can be
observed without turning them into an algorithm change.

An observed stage has `observed, read_ordinal, source_role, line, sha256, bytes,
dtype, shape, geometry, finite, full_actual_tensor, numerical_qualified`.
Unobserved stages contain only `observed:false` and the exact reason above.
`read_ordinal` numbers the actual reads 1..N; the reader must independently sum
their bytes and add those to original RETIRE/COMPLETE owner charges.

A reduction has `line, end_line, target, kind, destination, fused, role,
callsite_only, callee_source_pinned, transport_kernel_observed, alias`.
The actual alias is inspected without invoking a property or manufacturing a
communication group. If a dynamic descriptor cannot be inspected this way,
`alias.observed` is false with the explicit reason
`descriptor_or_dynamic_receiver_not_evaluated`. An observed alias records its
object/type/module/qualname/code witness, with `source_pinned:false`.

## Budget and independent-reader requirements

Every successful full read calls the original `owner._read` exactly once and
the original `_finite`; the original 512 MiB counter remains authoritative.
Additional accounting limits each tensor to 2 MiB, each generation to 8 MiB,
and both generations to 16 MiB. Failed finite checks retain already incurred
read charges. The frozen worst original device read bound is 515,220,032 bytes;
adding the full new 16 MiB bound gives 531,997,248 < 536,870,912 bytes. No old
cap is enlarged. All new metadata passes the original writer/accounting, META
512 KiB and OTHER 3 MiB checks, terminal host accounting and independent reader.

The ordinary 131x1536 BF16 input plus four 131x5120 BF16 stage reads costs
5,768,192 bytes per generation; fused input/post/final costs 3,085,312 bytes in
that shape. These are diagnostic read volumes, not inference timing results.
The conservative actual-source envelope fixture with six roles, twelve call
events, five stages, one native AssertionError record, long pinned Ref paths,
64-bit identities, 128-character request/prefix and the original boundary
schema is 7,915 bytes. Every actual envelope still passes its own hard 8 KiB
check; unsupported or larger metadata fails instead of being truncated.

The independent reader must keep original gates, reopen the exact 150-file
closure and all Refs, independently rederive stage byte sums and ordering,
join original outer norm/projection witnesses, verify source snapshot hashes,
and require restoration/terminal accounting. Hashes prove observed logical-byte
identity only. There are no new raw values from which to compute numerical
errors. A mismatch localizes a narrower observed interval; unchanged weight
metadata does not exclude weight-content changes, and differences after a
callsite do not by themselves establish HCCL nondeterminism.

## Focused CPU verification

Run `python test_projection_probe_v1.py`. The 16 controls use temporary exact
pure-Python pinned module files, real `sys.settrace` frame events and fake CPU
tensor objects. They execute no torch/NPU/model code. Production pins are
independently matched to all five saved source snapshots. The test looks first
for `evidence/` alongside the helper, matching the child source layout; the
local draft falls back to the supplied `boundary_actual_review/` snapshots.

The controls cover default OFF without touching an owner, exact declaration,
source-code tamper rejection, generic immediate pre/post witnesses, inline
return, fused absence, no-reduce behavior, one original call, complete return
identity, two real generations and exact instance-slot restoration, sticky
wrong scope, pre-existing and newly foreign trace/profile ownership, failed
read charging, partial-install rollback, single-read caps, foreign forward
preservation, exact native AST sites and the complete-envelope bound. They are
source-level controls and do not qualify this observer or any candidate on NPU.

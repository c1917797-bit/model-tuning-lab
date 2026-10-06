# Actual runtime CPU metadata observer v1 — default OFF

This NEW subpackage leaves the five frozen parent cache files and four frozen
continuous metadata files unchanged. It preserves the original native arguments
and return objects. It is preparation, not an actual runner/lifecycle/NPU result.

## Public seams

`Producer(owner, actual_image_id)` verifies deployed sources plus frozen cache
helpers. Register one producer per actual runner and map each original
`runner.input_batch.block_table[gid]` object to that producer. Call
`install(NPUModelRunner, AscendGDNAttentionMetadataBuilder,
AscendAttentionMetadataBuilder, BlockTable, producer_for_runner,
producer_for_table, after_preview, enabled=True)` before the first BlockTable
commit. Default `enabled=False` is a no-op. Foreign/wrapped original callable,
source hash or signature drift fails before installing any wrapper.

The original `commit_block_table` receives exactly its original arguments.
Immediately before its original nonblocking CPU→GPU copy, the observer freezes
the real CPU rows, int32 row counts, physical/logical block ratio and original
GPU allocation/view identity. No cache contents are copied.

The original `_build_attention_metadata` invokes its original FA/GDN group
builders. Each actual builder call is captured once, including its actual
`layer_names`, input CommonMetadata and returned metadata object. Coverage is
proven against the returned native per-layer mapping; 48 GDN and 16 FA names
are not manufactured as 64 separate builder events.

## Honest data origins and admission

CPU query starts, exact non-async sequence lengths, computed/prompt lengths,
is-prefilling flags, actual BlockTable inputs and native CPU chunk boundaries
are observed. FA slots, GDN state indices, initial-state flags and decode lengths
are **derived_not_device_observed** using pinned native rules and original
buffer identities. FA slot derivation uses scalar token positions computed+j,
not multi-row MRoPE positions. CP=1, no padding/spec/cascade/ubatch/graph,
prefix OFF, mamba NONE, text eager T<=16 only.

`Producer.finish` returns a Preview with ready=false and npu_executed=false.
It does not call Owner.native_receipt or permit a DAMP writer. The parent's
existing Owner.before_update guards cold geometry + paused/live leases +
scheduler-predicted byte footprints BEFORE the original early FA cache zero.
Future attention metadata cannot be used to justify that earlier zero.

For an independent checked diagnostic gate, `checked_admission(preview,
mode="checked-diagnostic", formal_perf=False)` explicitly reads only actual
NPU metadata tensors to CPU and compares every derived field, for each actual
builder event. Only after exact equality and complete native coverage does it
create the parent's NativeReceipts and call Owner.before_model. That CPU safety
admission is consumed by the DAMP core before its first conv/state writer.
An exception retains Producer.last_failure (CPU expected/read metadata/buffer origins), then retires the worker; no partial dense fallback or retry is allowed. MAIN must save that failure into the new diagnostic result directory before shutdown; this module performs no result filesystem writes.
The diagnostic report remains ready=false, not performance-admitted, and is
not a numerical/lifecycle/output parity result.

The after_preview callback should store the returned checked AdmittedTurn in
the core's runner context; core safety calls consume its actual native metadata
objects. All 48 successful cores must commit through the parent Owner; this
observer never fabricates LeaseBook commits. Preview-only/native diagnostic
use can discard a preview but must supply separately proven native lifecycle
tracking before a second scheduler turn: discard does not release its Owner
ticket or fabricate recurrent leases.

`pending_formal()` always raises. Formal no-D2H admission, complete mixed
lifecycle, FA shared-pool collisions/zeroing and all-layer output parity need
independent real checked NPU evidence and a reviewed producer policy. A source
mirror is a low-cost implementation seam, not evidence that the algorithm is
impossible or that the complete service is already safe.

## Exact unverified gates

- Actual installer dispatch and original result identity in the immutable image.
- Correct source-derived GPU values on real mixed/continuation T1..16 metadata.
- Guard before early zero with live and paused shared FA/GDN byte intervals.
- Checked complete48 mixed writers + output/state parity and no request leakage.
- Separate no-hot-D2H formal serving policy and matched E2E/quality protocol.

Only stdlib source/fixture tests are prepared here. The preparing Agent did not
start Docker, load Torch, execute NPU, build operators or mutate Git. MAIN's
stopped immutable-image source copies are independent provenance, not NPU use.

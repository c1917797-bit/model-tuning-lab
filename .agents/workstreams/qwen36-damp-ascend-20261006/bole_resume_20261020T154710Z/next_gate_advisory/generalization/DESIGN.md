# Advisory: stages after the bounded C1 service lifecycle

This is a design proposal. It changes no worker, live source, Git repository,
container or device. The current service source is immutable while its owner
runs. A successful four-token lifecycle is a prerequisite; it does not qualify
any of the extensions below or establish a speedup.

## Concrete current facts

- Target is actual Qwen3.6-27B/Qwen3.5 hybrid, TP4, 48 GDN +16 FA layers,
  BF16 model boundary, FA Q6/KV1/D256, ND kernel pages of 128 tokens.
- The saved actual r23 FA mappings, on all four ranks, report
  `use_hybrid_blocks=True`, `blocks_per_phys_block=12`, physical block size1536,
  request physical blocks `(1,)`, and CPU kernel-page row `(12,...,23)`.
  Raw physical-block IDs must never be compared directly with that expanded
  kernel-page row. Root is repairing this separately in the next lifecycle run.
- `adapter.validate` needs real destination capacity for at most root+child:
  `ceil((L+2)/128)`. `adapter.prepare` independently allocates private branch
  scratch `ceil((L+3)/128)`. These are intentionally different quantities.
  Example L126: one real destination page suffices, but private three-node
  scratch needs two pages. Changing both formulas to the same value is wrong.
- Prefix131 +1024 returned tokens totals1155 tokens; the final processed cache
  length is1154, with the last bonus still unprocessed. This fits the initially
  allocated1536-token physical block. Therefore the first fixed131/1024 case
  does not need allocator growth. Its FIA prefix/scratch geometry still changes
  from two pages to ten, and its state/scheduler lifetime grows substantially.
- The current service has singleton request state, exactly131 prefill tokens,
  an exactly-two-page FIA guard, prefix131..135, at most3 tree steps, output4,
  and process hooks restored after the first request. It also exports full
  tensors per step. These restrictions must change explicitly, not through
  accepting a manifest that still declares the old experiment.

## Ordered next gates

| Gate | Declared workload | New behavior | Required result before proceeding |
|---|---|---|---|
| G0 | Current131/output4/first request | Hybrid physical-to-kernel mapping repair | Actual four-rank lifecycle, old numeric gates, HTTP IDs, native retirement, cleanup pass |
| G1 | Two sequential C1 requests, each131/output2, max1 target step | Re-register each real request; retain process hooks; new generations | Both real requests take BOLE decode, independent two-frame math and writes, exact output streams, both retire; original aggregate raw cap; record whether physical slots were actually reused |
| G2 | Single131/output32, max31 target steps | Parameterized limits, current prefix, actual N1..3 target rows, bounded capture windows | Full32 IDs join native output; independent original-epsilon consumption of every captured window; deterministic repeated windows cover the actual trace before declaring all-step numeric qualification |
| G3 | Single131/output1024, max1023 target steps | Long lifetime, two-to-ten FIA pages, capture-disabled execution | All1024 output IDs, full eligible-decode activation, all native counter acknowledgements/retirement; separate qualification coverage and genuine native reference comparison |
| G4 | Actual formal prompt set, all measured requests | Varying prompt lengths and native allocation growth; chunked prefill only if workload needs it | Every measured request registered/active/retired; all encountered supported geometries covered; no silent native decode fallback |
| G5 | Three matched OFF/ON pairs, frozen actual concurrency | Formal client/timing and common precision policy | Fixed1024 outputs, TTFT/TPOT/E2E throughput, >=10% gain, and required task accuracy within both1pp and1% relative |

G1 intentionally uses output2: each request has one native prefill output and
one root-only target step. It tests process reuse and independent generations
with two bounded captures, without first making the original1GiB per-rank raw
budget unbounded. G0 remains the earlier accepted-child lifecycle evidence;
G1 does not claim to newly exercise child2 acceptance.

For G2, output32 is a new frozen profile, not a reinterpretation of output4.
The number of target steps lies between16 and31 for the current depth1 tree.
For output1024 it lies between512 and1023. The finite owner runtime/memory and
client deadline must be declared for each new profile before admission.
No run should silently continue past its declared step bound.

## Request and worker lifetime

Separate a process-lifetime `WorkerRegistry` from request-lifetime state:

```python
WorkerRegistry.register_native_layers(worker, runtime_source_refs, component_receipts)
WorkerRegistry.observe_native_prefill(request, actual_schedule, native_context)
WorkerRegistry.begin_request(request, completed_prefill_proof, policy, capture_plan)
WorkerRegistry.prepare_frame(request, actual_schedule, actual_input_batch) -> Frame
WorkerRegistry.acknowledge_native_output(request, actual_model_runner_output)
WorkerRegistry.retire_request(request, actual_finished_ids, worker_journal_event)
WorkerRegistry.close_worker()  # Restore owned methods only when process work ends.
```

Each active request holds its actual strong `CachedRequestState` object. Its key
contains internal request ID, object identity, and a monotonic generation epoch;
that epoch is never reset to1 when a physical slot or Python ID is reused.
`Owner.slot` is the current logical batch row, never a physical state slot.
The minimal G1/G2 implementation may retain C1/row0 explicitly; it must reject
unqualified batch configurations rather than counting a native fallback as BOLE.
If the frozen formal workload requires concurrency>1, C1 results are diagnostic
and a separate multi-request batch gate is required before G5.

`worker_entry.install_after_native_prefill` currently fires only once, and
`prefill_tail.install_capture` currently assumes one unchunked initial prefill.
They need request-generation scoped observations. The minimal C1 version can
retain the outer runner/MTP/prefill hooks, restore only the previous request's
64-layer bridge, rearm the native tail observer, and install a new request's
bridge after that request's actual native prefill. A later process-lifetime
layer dispatcher can avoid repeated layer-hook installation. Native prefills
for every new request must still execute the exact original model.
On retirement clear only that request's state and pending drafts; do not disable
BOLE for every subsequent measured request. Keep the worker identity journal.

The actual native-convolution calibration matrix should run once per loaded
worker/model/operator/library identity and be independently retained. A new
request may reuse that same process-local qualification only after checking
the actual operator object, model weights, layout and binary identities.
Running a full calibration matrix inside every request's timed prefill would
be a major TTFT cost; hiding that cost outside timings without a declared
shared initialization protocol would also be invalid.

The current Bridge constructor unconditionally calls `MC.run` and uses fixed
per-rank calibration output locations. Before re-instantiating Bridge for
request2, inspect the actual calibration writer and introduce an explicit
`VerifiedModelCalibration` process-local handle: first registration runs and
validates the actual matrix; later registrations revalidate the same retained
receipt and actual object/library identities. Do not infer qualification merely
because a path already exists. Pass the real request epoch through
`cache_registry.register`, per-layer binding identities and every constructed
Owner; remove any constructor-created hardcoded generation1 for request2.
Object IDs are rank-local identity evidence and must not be all-gathered as if
the same Python object existed in all four worker processes.

## Current ownership and dynamic page rows

Replace the frozen per-request whole FA row with an immutable per-frame
snapshot obtained after the original `_prepare_inputs` has committed tables:

```python
PageSnapshot = {
    'request_epoch': int, 'owner_version': int, 'schedule_ordinal': int,
    'logical_batch_row': int, 'native_group': int,
    'request_physical_blocks': tuple[int, ...],
    'use_hybrid_blocks': bool, 'blocks_per_phys_block': int,
    'physical_block_size': int, 'kernel_block_size': 128,
    'kernel_page_row': tuple[int, ...], 'allocated_kernel_pages': int,
    'table_object_identity': object_identity,
    'key_arena_identity': tensor_identity, 'value_arena_identity': tensor_identity,
    'committed_prefix_length': int, 'max_processed_nodes': int,
}
```

Expand `request.block_ids[group]` exactly as the original native mapping does:
`physical_id*ratio+j` for j0..ratio-1 only when `use_hybrid_blocks` is true.
Validate the expanded row against CPU allocated entries, current native GPU
block table and current attention metadata aliases. Validate cache pool aliases
against the actual layer and backend objects. Do not infer authority from a
same-shaped tensor or padded table zeroes.

Freeze the snapshot for the entire verify/stage/publish transaction. Stage FA
destinations through `frame.page_snapshot`, not the original `binding['table']`.
The original table object and cache arenas must retain their process identity.
Current tensor views may be rebuilt by the native metadata builder; re-observe
those views rather than retaining stale GPU metadata buffers.

Across frames, verify that page IDs covering the previously published committed
prefix remain the same in this minimal prefix-cache-OFF implementation.
Do not require every unused lookahead page to remain unchanged: the native
allocator may legitimately release or replace uncommitted trailing reservation.
Any change to committed-prefix pages, strong request, request epoch, GDN slot,
group or cache arena invalidates the old transaction. Preemption/resume or COW
requires an explicit independently qualified native handoff; never merely relax
the equality check to accept a new table.

The current Mamba `none` mode can initially keep its actual per-layer state slot
fixed for the request. A changed slot must abort until current native GDN
metadata's source-proved slot selection and native copy/recompute have their
own qualification. Physical state slot selection must never use logical row0
or FA page IDs. Do not invent current GDN metadata field names from FA behavior.

At the later allocator-growth gate, use a prompt/output envelope that actually
crosses1536 tokens. Include L1534 andL1535 frames: L1534 requires12 actual
destination pages but13 private three-node scratch pages; L1535 needs a13th
actual destination page. Verify the exact new raw physical block and expanded
kernel pages, existing committed data, rejection writes, and final retirement.
Passing131/1024 cannot be presented as having exercised this growth.

## Variable target N and sequence limits

Use real native admitted rows N1..3 throughout the target forward. The initial
three genuine tokens remain `(root, child1, child2)`, but compute only their
actually scheduled prefix. Do not pad an N1 orN2 target call to three nodes in
a formal performance implementation. Native MTP's own rejected-row padding
remains governed by its original source and is a different, required behavior.

```python
Frame.genuine_tokens: tuple[int, int, int]
Frame.active_tokens: tuple[int, ...]  # genuine_tokens[:scheduled_nodes]
Frame.positions = [L, L+1, L+1][:scheduled_nodes]
Tree.parents = [-1, 0, 0][:scheduled_nodes]
Tree.offsets = [0, scheduled_nodes]
Bridge.forward(frame) -> native_hidden[N, 5120]
FiaBoundary(frame, scratch_pages=ceil((L+N)/128))
```

Remove the hardcoded3-row shape assertions in GDN, FA, model context and the
consumer only after the actual N1/N2/N3 component matrix passes the original
bounds. `treeconv118.prepare` and `tree_metadata111.Tree` already express
general node counts, but the current `NodeRows`, model bridge and native
operator adaptations are still fixed to3. Core source and ABI support must be
checked; generic tensor shapes alone are not a qualification.

Parameterize `max_output_tokens` through the manifest, actual request policy,
client, owner and consumer. Require actual prompt tokens + output limit to fit
the source-pinned native `max_model_len`; the real scheduler remains authority
for any final admitted-token/model-length truncation. Do not manufacture a
larger native scheduled count. The final unprocessed bonus is included in the
output budget and excluded from processed cache length.

`max_steps=max_output_tokens-1` applies to this specific topology after one
actual native prefill sample. A normal EOS can finish earlier; a full1024
fixed-output request must produce all1024 token IDs. Counters are observed
from native request/output state and checked against the declared limit.

## Genuine MTP and final stop handling

Keep the proven child2 rule: before original `propose_draft_token_ids` performs
advanced-index copies, permute only the actual GPU target IDs and actual native
hidden rows `(0,2,1)` when child2 was selected. Preserve all admitted N rows and
their native metadata. Never swap CPU token history after native bookkeeping.
The exact first-pass live prefix is accepted child then bonus, or just bonus;
the rejected tail's final input ID may be stale by original native design.
Record actual target positions and exact int64-to-int32 native position copy.

The ON algorithm currently executes one real original MTP first pass and uses
its genuine vocabulary top2, returning a CPU two-wide draft list; the temporary
`num_speculative_tokens=1` must be restored in `finally`. The original declared
native MTP configuration8 is not evidence that eight draft passes actually ran
in ON. Freeze and report the effective proposal method/budget for both modes.
Resolve the existing authority's baseline MTP mode from its actual source;
do not assume OFF means either AR-only or native eight-draft speculation.

Keep the final remaining1 rule: root-only publication and one emitted bonus.
For normal-EOS accuracy requests, add a source-proved `StopPolicy` before
publication. The native scheduler subtracts rejections before it trims stopped
output. If an accepted candidate child itself is EOS/stop-ID, choose root-only
and emit that stop token as the bonus; do not publish child state plus a second
bonus that the engine will trim. A non-stop accepted child followed by an EOS
bonus is a valid two-token result. EOS remains unprocessed at retirement.
Source-pin the real `check_stop` semantics and minimum-output rules.
Unsupported stop strings, grammars, penalties or processors remain a hard
admission failure until qualified; do not bypass them with raw argmax.

Fixed1024 throughput and normal-EOS/max2048 task accuracy are separate frozen
profiles. Use the same stop policy in each profile's OFF/ON pair. A successful
ignore-EOS throughput request does not qualify normal-EOS task behavior.

## Capture and long-run qualification

Current per-step payloads contain several complete37.7MB GDN-state copies.
Accumulating31 or1023 such steps exceeds the original1GiB per-rank raw cap.
Changing only `max_steps` would fail the resource contract before completion.

Introduce an explicit capture plan in the frozen source:

```python
CapturePlan(mode='qualification', request_ids=..., target_step_windows=[(0, 3)],
            max_raw_tensor_bytes=2**30-36*2**20, report_all_steps=True)
CapturePlan(mode='performance', target_step_windows=[],
            max_raw_tensor_bytes=0, report_all_steps=True)
```

For the first32-token gate, bounded repeated runs with predeclared <=3-frame
windows can preserve the existing cap. Keep the entire actual32-token stream,
request lifecycle and all-step activation ledger for each run. Join source,
input, output tokens, owner counters, tokens, admitted N and decisions across
the deterministic repeated traces; then take the union of independently
consumed original-epsilon windows. If traces differ, they cannot be spliced
into one all-step qualification. Uncaptured new prefixes remain explicitly
unqualified until their matching windows are consumed.

For1024, worst-case window repetition needs341 runs. That may be too expensive.
A later bounded online independent-consumer protocol can validate a <=1GiB
spool, produce immutable per-window numeric/identity receipts, and release only
already-validated transient tensors. Its retention/backpressure/failure
preservation policy must be a new declared contract; it is not the current
single-file raw contract. Preserve failed operands and stop on a failed or
missing consumer acknowledgement. Do not silently turn sparse captures into
a claim that every new prefix passed the original mathematical bounds.

The first capture-disabled1024 run is a lifecycle/generation gate. It does not
by itself establish component qualification for unseen prefixes or speedup.
Exact whole-stream greedy identity against an actual same-precision native
reference is separate strong evidence, and task accuracy remains mandatory.

## Common precision and performance activation

The FP16 FIA repair currently belongs to the private tree boundary and private
native-AR control. It is not a production native vLLM dispatch patch. A formal
OFF/ON pair must use a qualified common precision policy rather than giving
only ON the corrected FA boundary. Keep GDN math, model dtype, output dtype,
HF32 policy, weights, native extension, cache memory configuration, context,
eager/graph settings and profiling policy fixed between the pair.

Before G5, qualify an actual native-service common FA dispatch policy in OFF
and ON. Record actual operator input/output dtypes and calls by target/draft,
prefill/decode, prefix and N. If baseline is native eight-draft MTP, include its
actual multirow decode queries up to9; the saved256 one-token AR FIA tests
cannot qualify those calls. Existing common native prefill paths may remain
unchanged in both modes, with the exact policy explicitly recorded. Do not
select an unsupported cache-dtype flag or pretend the private AR control
already changes the production backend. A new FP16 cache layout or shared
lookahead-page staging would be separate optimization/qualification work.

In performance mode retain request/owner/page authority, actual TP decision
agreement and fail-closed native output accounting. Remove only explicitly
qualified observation work: `_snap`, exported all-step full states,
`native_before`, diagnostic prefix anchors, stored local/global logit clones,
all-three commit outputs created only for capture, and CPU oracle execution.
Use one frozen algorithm implementation with a reviewed capture adapter;
validate captured versus capture-disabled outputs/cache decisions before
timing. Removing runtime full-byte scans or changing persistent commit behavior
is a separate execution-path change that needs its own qualification.

Existing adapter copies the whole prefix, native operands and source anchors;
turning off `torch.save` alone does not remove that work. These costs may prevent
the required gain. First measure the qualified capture-disabled path. Any
faster paged-prefix reuse, shared FP16 cache, fused GDN solve, device-side
decision or batched transaction is a later independently qualified change,
not something this proposal implements or credits with a hypothetical speedup.

Each rank emits bounded performance activation evidence after the timed work:

```python
{
 'schema': 'bole.actual-performance-activation/v1',
 'source': source_ref, 'mode': 'ON', 'capture_mode': 'performance',
 'measured_request_count': R, 'request_entries': R, 'request_retirements': R,
 'eligible_decode_steps': D, 'tree_decode_steps': D,
 'native_decode_fallback_steps': 0, 'target_padding_rows': 0,
 'layer_traversals': {'gdn': 48*D, 'fa': 16*D},
 'genuine_mtp_first_passes': observed_count,
 'capture_tensor_export_calls': 0, 'capture_tensor_bytes': 0,
 'cpu_oracle_calls_during_timing': 0, 'profiler_active': False,
 'request_ledger': bounded_ids_counts_acknowledgements_and_decisions,
}
```

Counters must be updated by the actual source-pinned dispatch, not filled from
expected constants at shutdown. Match all four ranks and actual HTTP request
IDs/output IDs. OFF must show native decode and zero tree dispatch; ON must
show BOLE on every eligible measured decode request. A native-only retirement
barrier, if needed, is explicitly labeled and excluded from performance counts
and denominators; ordinary measured requests are never treated as barriers.

Use streaming HTTP with actual `return_token_ids=True` for TTFT/TPOT: the exact
installed protocol exposes token IDs in both ordinary and stream choices.
Measure first nonempty generated-token chunk using client monotonic time;
keep all chunk token counts because speculative chunks can contain two tokens.
Compute the frozen TPOT definition over actual generated token count, not
number of network chunks, and retain request start/first-token/finish times.
All three matched pairs use the same real prompts, tokenizer, concurrency,
ordering/seed, fixed1024 output rule, common optimization and profile-OFF
settings. Include failures; never discard an unfavorable request or pair.

## Exact API edits required

| Current location | Required edit | Must remain unchanged |
|---|---|---|
| service_experiment/profile/client/CPU CLI contract | New explicit request count, prefix policy, output limit, finite max steps, capture plan and timing mode | Default OFF, source/mount/owner/resource admission |
| LiveOwner | Per-request epoch; parameter limits; per-frame current expanded page snapshots | Strong actual request, native CPU counter/bonus acknowledgement |
| cache_registry/prefill observers | Per-request final-native-prefill registration; variable actual length; later explicit chunk handling | Actual native cache/metadata/ABI authority |
| service_bridge/model_entry | N1..3 real rows; frame-bound destinations; no formal target padding | Tree ancestry/RoPE, original GDN/conv math and epsilons |
| service_fia/adapter | Dynamic prefix, actual N and scratch shape; common precision receipt | BNSD, actual page128 ABI, masks/scales, original per-element bounds |
| eligibility/transaction | Parameter budget and source-proved EOS policy; per-frame PageSnapshot | Complete TP owner+decision+bonus agreement,128 real destinations, failure semantics |
| MTP wrappers | Per-request genuine draft state, observed source-bound effective budget | Actual native first pass and child2 GPU-only compaction |
| publisher/consumer | Multi-request receipts and bounded window mode; separate performance activation schema | Independent actual numeric math and honest qualification coverage |
| host/client | Mode-specific actual output contract, request identities, streaming timestamps | Unique outputs, retained failures, exact device ownership and cleanup |

No source change above is authorized for the currently running immutable
packet. Root should freeze each new packet only after its scoped CPU/source
and same-image CLI/mount checks pass, then perform the corresponding real gate.

# Source-bound continuous metadata preparation, not NPU success

This NEW stdlib packet does not patch service/operator/collector, import Torch,
allocate runtime caches, launch hardware, or claim serving/E2E acceptance.
All existing source hashes stay frozen. Prefix caching remains OFF, mamba cache
mode none, TP4, synchronous text-only eager. Normal request pauses and prompt
continuations are designed here; preemption/slot relocation, speculative decode,
CP/PP, graph dummy requests and multimodal remain fail-closed until separate
real source/numerical/lifecycle proof. This narrower first scope does not justify
claiming the formal C16 throughput target.

## Exact source seams

The MAIN stopped immutable-image snapshots are authoritative:
runtime-source-snapshot-v1/receipt.json SHA
4a4e548e300339a0d28fbd71068ca803ad026325a5cf1c0fce1b8d7ee7261177
and runtime-continuous-snapshot-v1/MANIFEST.json SHA
2a37b75ec59f185943fb214e7efe6c8d08f8efa95a554de50c64558c62f19130.
The /cache/austinov/src copies used for line inspection are byte-identical
to the listed deployed pins; /cache/cch/vllm-ascend differs and was not used.

* Ascend gdn.py 217–283: with any prefill, native causal conv run_mode0 consumes
  ALL non-spec rows; its starts/slots/initial flags must not be suffix-sliced.
* gdn.py 337–369: mixed compressed decode is the token prefix [:num_decode_tokens],
  state indices [:num_decodes], lengths [0,1,...,1]. Actual T=number of decodes,
  not total mixed tokens or padded16. Use prewarmed exact-T key.
* gdn.py 377–410: native chunk receives suffix query/key/value/g/beta,
  rebased prefill starts, selected prior state transposed value-major->key-major;
  final native state transposes back before pack. Outputs join original order.
* gdn_attn_builder.py 55–79: one-token prompt continuation with prior state is
  reclassified to recurrence. The input remains a prompt token but has the same
  state update ABI; never clear its existing state.
* builder 591–601,733–735,768–771,912: ordered first-column state slots,
  suffix starts minus num_decode_tokens, suffix initial flags computed>0.
* utils.py 606–650: native order decode->short_extend->long_extend->fresh prefill.
  mamba_get_block_table_tensor 871–894 returns none-mode table unchanged.
* GPUModelRunner _update_states 1135–1180: finished IDs release requests;
  unscheduled IDs leave only the batch, retaining request/cache state.
  1368–1379 resumed preemption REPLACES block IDs; 1436–1447 re-add,
  condense and reorder. Batch row identity is not a state lease.
* Ascend model_runner 3147–3154 supplies CPU computed/prompt tokens;
  3284–3293 substitutes UNPADDED gdn_query_start_loc for GDN.
  4124–4132 shares ONE raw int8 storage across shared_by layer names.
  4681–4714 lays four typed Mamba views contiguously in this same raw storage.
  Hybrid FA views 4569–4589 also refer into that raw storage.

## Minimal service-owned adaptation

1. Before native execute/_update_states writers, retain exact finished/new/resumed
   events; record actual CachedRequestState object generation and source-bound
   per-group CPU block table. Release only explicit finished identities;
   pause/unscheduled requests keep leases. Same-ID new request after finish gets
   a new generation. Preemption/recompute must be rejected BEFORE allocator/model
   writers in this first scope, not discovered after overwriting state.
2. In runner _model_forward use post-reorder IDs, actual per-layer group CPU
   first-column slots and gdn_query_start_loc CPU prefix. Call plan() and verify
   its source-bound counts/metadata before any layer writer. Metadata values
   copied D2H may only be diagnostic, not formal timing; source-pinned builder
   CPU receipt adapter is needed for production.
3. Core calls unchanged native conv once for mixed ALL rows and native gating.
   For decode prefix reuse actual DAMP allT operator and exact prior packed state.
   For Nprefill suffix allocate only Nprefill FP32 scratch, zero fresh requests,
   unpack ONLY continuing selected packed states with true SR and permutation
   inverse (independent golden/reference proof required). Pass original native
   prebuilt suffix chunk metadata; pack final state to exact suffix slots using
   separately gated NPU pack. No arena-sized, layer-retained, or persistent FP32
   sidecar. Scratch high-water B16 is 12,582,912 bytes per active layer/rank;
   include native chunk workspace/output and pack temporaries as well, not just
   scratch. Same common total dense/candidate HBM budget.
4. Commit all layer lease advances only after whole model turn succeeds.
   Partial failure retires the entire worker; do not retry/native-fallback or
   resynchronize compressed states from a hidden dense state.
5. Cold native shared_by must bind each raw allocation's actual storage,
   tensor offset/shape/stride/item bytes and group owner. Runtime live footprint
   must include all retained GDN slots (paused too), FA readable history blocks
   and current write blocks from actual corresponding group tables.
   block_accesses()/verify_live_accesses() check selected byte intervals, not
   merely distinct physical block IDs or whole GDN-only pointers.
   Source bytes prove sharing exists, NOT that new four-state SoA is safe:
   requires actual model allocation plus mixed FA/GDN lifecycle NPU validation.
   If observed inner/block strides are unsupported, fail closed; do not create
   extra shadow buffers. No memory-saving claim from theoretical 258,048B state
   when padded common page/raw pool remains unchanged.
6. Use independent training HOLDOUT for real cache init/continuation:
   pure prefill->decode, mixed decode+fresh, mixed decode+continuation, q1 final
   prompt continuation, batches1..16, changed scheduling order, pause/resume
   (same slot), finish/reuse, adversarial duplicate/relocated/aliased slots,
   whole packed/conv state+full outputs+untouched bytes/pointers and all48
   instances x4 ranks. Include real FA reads/writes and common page budget.
   Separate NPUGraph/cache replay, fast pack/unpack, actual model weight identity
   gates remain open; CPU tests are not numerical/kernel/lifecycle evidence.
7. Only after these gates and instrumentation-free candidate exists perform
   matched same-stack C16/40requests/input32768/prefix16384/output1024.
   Common general optimizations identical; eager/prefix-off screening is not
   final baseline. TTFT/TPOT use actual token-ID stream/usage, final GSM8K and
   LongBench max2048+normalEOS are separate, never used to fit/train plans.

## Public API

Row includes actual request_id, slot, query/computed/prompt lengths, generation.
plan(rows, starts, slots, max_requests=16) returns immutable Turn and never
reorders model inputs. verify_native(turn, receipt) checks exact metadata values.
LeaseBook.finish(actual_finished_ids), check/commit/retire contain CPU identities
only. block_accesses(...) accepts actual observed axis0 physical block geometry;
verify_live_accesses(...) rejects cross-layer overlap with any writer.
There is NO ready=true/serve-ready output and NO automatic execution command.

Software check, MAIN or subagent CPU only:
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -m unittest discover
-s projects/damp-ascend/integration/continuous_metadata_v1 -p test_contract.py -v

# DAMP packed-cache integration draft (not NPU validated)

Only this independent directory is changed. No upstream runtime, collector,
operator or shared maintainer file is edited. No NPU workload, container lifecycle,
build or Git mutation was performed in this stage. Parent owns all device scheduling.

## Actual Qwen binding and request admission (unvalidated live revision)

The deployed Qwen layer is QwenGatedDeltaNetAttention, not an instance of its
Ascend function donor. The upstream patch_qwen3_5.py copies forward/core
function objects into that Qwen class at import; changing only the donor does
not update the copied binding. The draft now checks both original aliases,
patches both classes, registers typed specs for the actual Qwen class, and
verifies all48 real no_compile_layers instances before each model call. A
first-turn receipt includes receiver/copier source hashes and every prefix.
No hook installation or synthetic binding test is claimed as live activation.

Request admission directly checks source-bound CachedRequestState payloads:
nonempty mm_features, any user prompt_embeds, mixed token/embedding masks,
missing fields, encoder modes/cache and every extra model kwarg are rejected.
Pure-text MRoPE appearance is not a media absence proof. The source-proven
multimodal-capable Qwen preprocessing uses native inputs_embeds even for text;
that route remains allowed only after payload checks, with an unchanged native
buffer identity, existing CPU token-mask proof and no encoder/extra kwargs.
When native requires_raw_input_tokens is true, both native raw IDs and native
text embeddings are admitted and both buffer identities are checked; this is
the pinned _prepare_mm_inputs branch, not arbitrary caller-supplied embeddings.
Token-ID native routes remain allowed for text-only models. No device-to-host
metadata copy is added. General SR, graph, mixed-turn and numerical-receipt
gates are unchanged; restricted native pass does not activate this integration.

Focused CPU contracts are tests/test_live_request_binding.py. Host CPU tests
ran27 contracts OK with the optional real-Torch packing class explicitly skipped;
all9 Python files passed AST. Same-image validation and real cache/serving
execution remain parent-controlled and due.

## Actual source-bound seams

Read from the **stopped/no-device** qwen36_damp_cache_source_20261006 by docker cp
to stdout. Each file SHA is pinned in damp_integration/patch.py.

- MambaBase.get_kv_cache_spec (abstract.py) builds MambaSpec from arbitrary
  get_state_shape/get_state_dtype tuples. It does not limit states to two.
- GatedDeltaNetAttention.get_state_dtype and AscendGatedDeltaNetAttention
  get_state_shape delegate the GDN calculators in mamba_utils.py.
- Qwen3_5ForConditionalGeneration class config-derived sizing and copy funcs
  delegate those same calculators (qwen3_5.py lines678-712).
  Patching only the layer methods would leave hybrid startup page sizing native.
- MambaSpec.page_size_bytes sums zip(shapes,dtypes), then honors padded_page.
- NPUModelRunner._reshape_kv_cache_tensors lines4681-4717 accepts arbitrary
  typed states, creates contiguous SoA views of one raw byte arena, and leaves
  unused padded bytes. Its allocator creates zeros; no persistent FP32 sidecar
  is necessary.
- mamba_utils get_conv_copy_spec/get_temporal_copy_spec use each tensor's
  numel/data_ptr. The GDN copy-function tuple is originally only two entries.
  We return four functions with num_accepted_tokens==1. Actual align/all modes
  are fail-closed; this is cardinality safety, not prefix lifecycle support.
- AscendGDN._forward_core uses cache[1] as FP32. Its chunk prefill receives
  [B,Hv,K,V] temporary initial/final state and writes final into cache[1].
  The draft keeps original convolution, gating, Q/K norm, and native chunk
  routine but replaces only persistent final-state packing and decode.
- CPU identities come from NPUModelRunner._model_forward's ordered req_ids,
  query_start_loc.cpu, prompt/computed CPU tensors and the native
  MultiGroupBlockTable.get_cpu_tensor first block per group. For cache none,
  upstream mamba_get_block_table_tensor returns the same device block table.
  All48 layers are pre-admitted before the first layer may mutate state.
  CPU metadata never calls .cpu() on a device tensor.

## Typed allocation

Per rank / slot / layer, native SD conv is BF16 [3,2560]. Packed states:

- FP16 high [12,128,16]
- INT8 low [12,128,112]
- FP32 scales [12,4,112]

State axes are native V-major. Every group covers32 reordered V rows; high
precision covers16 reordered K columns. Persistent payload including conv is
258048bytes, versus801792native. **Actual padded allocation may remain801792
or larger** after hybrid reconciliation. An unwritten/padded arena is not an
HBM saving. The allocator receipt reports payload and real padded page
separately; measure true allocated storage before making any memory claim.

Prefill supports exactly one entire initial prompt. It uses one transient
FP32 [1,12,128,128] scratch, preserves native prefill output, applies calibrated
SR/Pv/Pk only to the final state, packs three typed buffers, then discards the
temporary state. A layer never retains full FP32 state. Decode consumes the
packed buffers directly with independently named qwen36_damp.decode.
Prepare runs once in eager outside graph. No native recurrent fallback exists.

## First supported experiment

Explicit first screen: TP4 BF16, eager, prefix off, mamba cache none,
max_num_seqs=1, chunked prefill off, no speculation/PD/CP/PP/async scheduling.
Only initial full single-request prefill + one-token B1 decode.
The operator additionally supports exact B16; the draft CPU guard will reject
every B2..15, mixed turn, chunk/continuation prefill, stale/recycled state,
padding and graph. **Do not use a scheduler batch16 merely because the operator
accepts16**: ramp-up/tail/mixed batches remain unsupported. B1 is a lifecycle
screen, not the final concurrency16 throughput target.

All48 GDN layers/all4 TP ranks need immutable external plans. This is an
equation-derived port; no official DAMP repository has been verified.
Integration-smoke identity plans must be explicitly labeled and must never
be reported as36-prompt calibration or a tuned DAMP candidate.

## Parent-controlled activation after gates

No automatic entry point is installed into the existing collector. Add this
directory to PYTHONPATH (append/preserve image paths) and call:

    DAMP_PACKED_ENABLED=1
    DAMP_MAX_DECODE_BATCH=1
    DAMP_PACKED_LIBRARY=/absolute/new/library.so
    DAMP_SERVING_PLAN=/cache/cch/qwen36-damp-20261006/serving-plan-v1.json

    from damp_integration import register
    register()

Call register in every worker before any model/config-derived cache sizing.
Bothoff/on must preserve actual Ascend platform/model/loader plugins. Off must
not activate this patch. Use a new result directory, for example
/cache/cch/qwen36-damp-20261006/packed-integration-b1-v1; refuse if it exists.

Plan schema damp-serving-plan/v1 contains model_config_sha256, tp4, purpose
integration-smoke or calibrated-candidate, operator_sha256, operator_gate,
and192 plans (rank0..3 × actual48 layer IDs). Each plan entry has external
path,sha256,rank,layer. Each weights_only torch file contains only CPU INT32
pk/pv and FP32 sr [12,128]. Operator gate receipt requires compressed_recurrence,
untouched_slots,changing_inputs,multiple_steps true and external
receipt_path/receipt_sha256. The reader validates the actual damp-independent-packed-oracle/v1 report:
mode npu-operator, numerical_pass, complete160-step matrix, B1/B16 cases,
all step guards and checks passed, and identical operator-library SHA.
A reference-only, CPU, short smoke or failed report is rejected. A calibrated
candidate additionally declares36 TRAIN-only prompts, input1024/output4096 and
full calibration manifest hash. Absence of any gate/plan is a hard error.
This code does not manufacture a passing receipt or full calibration.

## Verification boundary / remaining gates

CPU validation:13 metadata/manifest tests PASS; optional real-Torch packing
class SKIPPED because host Python has no Torch. Eight Python files passed AST;
Maintainer Skill Tree and scoped diff check passed. This does not verify import
or packing in the actual image. The optional test_prefill_pack.py compares
nonidentity SR/Pk/Pv mapping to the independent oracle when real CPU Torch is
available (parent-controlled same-image test still needed).

CPU unit tests cover shapes/bytes, request/slot identity, one-step update
ordering, recycling, duplicates, padding, first-prefill length, mixed/continuation
rejection, and B1/B16 versus intermediate-batch rejection. They do not prove NPU
packing, allocator storage format, compressed recurrence or output quality.

Before ANY performance claim the parent still must:
1. Finish custom operator build and real NPU equation/multistep/untouched-slot
   tests, including discrete quantizer boundaries. Do not relax failed gates.
2. Same-image import/config-derived spec/allocator preflight. Verify each typed
   view's physical format is ND; wrapper rejects blocked format. Confirm CPU
   slot mirror maps to native GDN metadata in all ranks.
3. NPU native prefill output/final-state packing crosscheck, live B1 multiple
   decode steps + slot recycling + full48/TP4 path receipts. Compare independent
   compressed oracle, then measure quantized-versus-dense drift separately.
4. Close any unexpected scheduler mode honestly; no silent dense fallback.
5. Implement/gate scheduler-compatible batches and graph only if worthwhile;
   neither is implied by this B1 draft.
6. Same-stack paired fixed1024 E2E performance, TTFT/TPOT, actual allocation,
   and final nonthinking normal-EOS GSM8K/LongBench task accuracy.

    PYTHONPATH=projects/damp-ascend/integration python3 -B -m unittest discover \\
      -s projects/damp-ascend/integration/tests -v

Sources remain copyright their upstream authors under Apache2.0. This draft
reuses native public calls, not a copied modified upstream module.

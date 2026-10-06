# DAMP continuous native-core seam v1 — NEW, default OFF, source preparation

This packet is required algorithm/cache adaptation, not a generic operator
optimization and not service acceptance. It reuses native Qwen GDN ALL-row
causal convolution, native gating and native chunk recurrence. The only
replaced state seams are compressed recurrent decode, selected continuing
state reconstruction, and selected final-prefill state packing. Original
runtime/image/frozen binary sources are unchanged.

Actual callable: ContinuousCore(layer,mixed_qkv,b,a,core_attn_out), with explicit
TorchBackend and cache_identity_v1 AdmittedTurn injection. There is no public
installer that can skip pending receipts and no torch.ops reassignment.
bind_receivers verifies actual image copier/receiver/donor source hashes and
copied-function identity, then binds BOTH actual Qwen receiver and donor.
Caller must additionally enumerate all48 real no_compile_layers instances
before each model call, verify exact outerforward/core/prefix identity and
all48 metadata, and commit leases only after ALL48 layers succeed.
Four TP4 ranks own192 separately calibrated plans; smokePlanStore forbidden.

Native source d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816:
ANY prefill: one causal conv run_mode0 with ALL rows' query_start_loc,
cache_indices and computed-token initial flags. No prefill suffix-only conv.
No PCP>1 path, spec, CP/PP, encoder/media or synthetic padded requests.
Native gating runs once over ALL actual tokens. True decode T=number of
prefix single-token stateful requests, in1..16; no padded16/PAD slot.
For mixed turns, compressed decode sees only native prefix and native chunk
sees only rebased suffix. Output concatenation preserves exact original order.
One-token continuation with existing state uses decode per actual builder.

Selected continuation unpack is not an S-slot FP32 sidecar. Allocate ONLY
P suffix initial states; fresh entries remain zero. For continuing suffix
positions, gather selected hi/lo/scales, reconstruct lo.float()*group32scale,
join hi16, inversePv, inversePk, multiply original-coordinate FP32 SR once,
then transpose V-major to native K-major. No BF16 transform intermediate.
Native chunk consumes the original rebased starts/prebuilt chunk metadata,
not regenerated order. Its final FP32 K-major state is transposed to V-major
and passed to NEW qwen36_damp_selected_prefill_v1 exact Float pack.
All transient tensors die within the layer/cold prepare; no persistent dense
cache or native fallback is allowed. Selected unpack's TorchNPU API/numerical
behavior remains UNTESTED and requires a real NPU oracle gate.

Cold prepare happens outside capture/model-call for EVERY actual T/P1..16,
static inversePk and plan/allocator identities retained. The current C16
preparation requires actual allocated slots>=16. Dense shape probes are
temporary static-key setup, not dynamic metadata validation or cached state.
Graph key must include all static plans/source/SO, actual pointers/strides/
storage_offsets/S, token count, native metadata identities and device. This
checked backend does not claim graph/service/performance admission.

Safety authority contract agrees with NEW cache_identity_v1:
require_layer(prefix,md)->frozen continuous Turn;
before_writer(prefix,turn,md);writer_started(prefix);
layer_succeeded(prefix);retire(prefix,reason,retry_allowed=False).
It must enforce _update_states BEFORE native early cache-zero, source-bound
native post-reorder CPU receipts and real live FA/GDN byte footprints including
paused leases. A whole-GDN disjoint-view check does NOT prove shared FA pages
safe. The actual CPU producer observer/source proof is separate and missing
fields remain Pending; never replace with hot GPU->CPU metadata copies.
Whole-model authority commit requires all48; a failure after any group/layer
may leave prior state writes and MUST permanently retire worker/affected slots,
without retry/fallback/partial publication. No transactional rollback claim.

CheckedSink retains ALL guarded selected-pack status rows and verifies success/
groups/count. It explicitly D2H-copies status and checks output finiteness.
TorchBackend(formal_perf=True) rejects. These costs are exposed and cannot be
reported as instrumentation-free formal performance. Removing this check
without a validated asynchronous device-error/retirement seam is forbidden.

Dependencies: integration root AND this directory on PYTHONPATH; frozen
continuous_metadata_v1 contract SHA113f37c...1b; explicit already-admitted
qwen36_damp_all_batch_v3 and NEW selected_prefill namespaces/library schemas;
typed cache allocator four real regions conv/hi/lo/scales, per-layer actual
source identity and complete cold shared_by/raw span observation.
Full source hashes appear in source_manifest after source/software freeze.

MAIN-only required validation, still PENDING:
1. New exact Float IEEE RN32 division/probe and selected pack build/ELF/load/
   Meta/NPU. Compilation/sample equality cannot certify an ISA float contract.
2. Native prefill FP32 -> independent exact SR/Pk/Pv/group32 pack bits,
   selected shared arena and all raw guards, first/last slots, P1..16;
   selected unpack parity including c1/power2/generalSR.
3. Native-prefill -> pack ->160-step compressed decode own-feedback states/
   output frozen1e-5/.00303 and full192 calibrated plans.
4. Fresh/continuing/q1/mixed/pause/resume/finish/zero/slot lifecycle at actual
  48x4 source-bound receivers; live FA reads/writes protected before ANY writer.
5. Only after source/API/numerical/lifecycle: true C16 fixed1024 E2E dense-paired
   performance, same common optimizations, TTFT/TPOT separate, final2048 EOS
   GSM8K/LongBench-v2 with <=1% E2E loss per user. No performance result exists
   for this packet and HYPIC is historical example, not a new success.

Software test (NO Torch/load/NPU):
/usr/bin/python3 -B -m unittest discover -s
  projects/damp-ascend/integration/service_continuous_core_v1/tests -v
Source fake-backend tests prove orchestration/fail-close only; not real arithmetic.

# Pre-registered real shared-arena gates (not executed)

MAIN alone owns fresh fail-closed physical NPU4–7 checks and one new output per
experiment. Keep NPU0–3 untouched. Never poll/restart someone else's load.
Do not rebuild/load an unchanged deterministic failure; preserve raw receipts.

## Identity / load

Bind source_manifest compiled_sources9, actual NEW build receipt, image, CANN
OPP identity, non-UND exported launcher, library SHA, actual runtime SoC and
device mapping. Use explicit Candidate injection for
torch.ops.qwen36_damp_arena_v2, not torch.ops replacement.
No-device dlopen/schema/Meta first, recording inherited Meta limitations.
Production-integer-compaction v1 reports remain original evidence, not v2 results.

## Two physical arena geometries

Both use one physical-ND UINT8 raw storage and actual contiguous dtype views,
NOT separate packed buffers:

1. Allocator-faithful SoA: conv FP16[S,3,2560] (equivalently native transpose
   shape when source binds it), then hi FP16[S,12,128,16], lo INT8[S,12,128,112],
   scales FP32[S,12,4,112], then documented page tail padding. Zero inter-region
   gap exactly follows the actual v0.23 slice/view allocator.
2. Diagnostic guarded SoA: same region ordering with at least 64B sentinel gaps
   between regions plus 64B outer guards, all offsets divisible by32 and element
   width. Conv/raw gap/tail bytes must remain bitwise unchanged.

Slot bytes: conv15360, hi49152, lo172032, scales21504.
Payload258048 per slot before page padding. Per group DMA writes remain
hi1024, lo3584, scales448; output per head256. Tensor DATA intervals may touch
exactly at a boundary; they cannot overlap. Include a region ending exactly at
the backing end to catch off-by-one checks.

## Numerical / state lifecycle

Use B1/S4 and B16/S19, at least160 sequential changing-input steps per layout.
Select first and last slots and vary indices each turn. Include static per-Hv
permutations/SR1/power2, then general positive FP32 SR with the independent
native-derived reference and separately own-feedback independent packed golden.
Use the exact frozen original fixture/algorithm protocols rather than new
easier random input or candidate pack helper. Fixed saved-step45 must rerun.

Pre-register same state relativeL2<=1e-5 and output<=0.00303; require complete
packed bytes/guards equal when the original relevant protocol is bitwise.
Capture EVERY returned raw output/full packed state/raw arena before assertions.
Compare complete state, unselected slots and every raw byte outside selected
hi/lo/scales writes, including conv, gaps and page padding. All input bytes,
plans, metadata and storage/data pointers/offsets/strides remain unchanged.
prepare before/after must leave ALL user inputs and full raw arena bitwise intact.

Exercise slot recycle only via declared full prefill/import lifecycle later.
This decode gate does not establish arbitrary reset/shared_by ownership,
prefix snapshots, actual cache managers or whole model192plans.

## Explicit refusal / pre-writer dynamic failures

Host reject B2–15, wrong dtype/device, blocked physical format, noncontiguous,
misaligned pointer, mutable overlapping DATA intervals and state↔readonly spans.
Legal B1 4B/8B metadata must NOT reject due to byte length.
Where PyTorch forbids fabricating malformed overflow views itself, retain that
fact plus stdlib boundary check; do not call a Python-fabrication rejection a
tested C++ rejection. Kernel malformed lengths first!=0/active!=1, indices<0,
>=S and B16 duplicates must leave ENTIRE raw arena bitwise unchanged and return
nonfinite output per the original pre-writer contract. Preserve failures.

Do not require internal quantization errors to transactionally rollback:
earlier groups/tasks may already have stored, so any execution failure or
nonfinite output retires all touched slots/worker, no retry/native fallback.

## Actual graph replay, after eager numerical acceptance

Cold prepare outside capture; warmup on separately resettable typed arena.
Hold raw storage/views/static plans/input buffers for whole graph lifetime.
Bind full pointer/storage_offset/dtype/shape/stride/S identities plus actual
device/SoC/vector cores/plan identity. Only B1/B16. No torch.compile claim.

Capture once, repeatedly change Q/K/V/g/beta and lengths/indices IN PLACE,
at least160 graph replay updates with the independent own-feedback packed
golden and complete raw arena checks above. Verify dynamic indices redirect
state writes and invalid metadata graph replay leaves raw arena unchanged.
For deterministic replay, reset the complete raw arena and input bytes and
compare three replay trajectories bitwise. No deleting the graph's partial
outputs, masking NaNs or clearing bookkeeping to hide a failure.

Poisoned D2H/copy errors must be nullable recorded fields: save original dispatch
error, CPU fixture/before/golden and every available raw after, THEN assert.
Never let a secondary copy exception prevent evidence saving.

## Service remains a separate gate

A v2-bound NEW adapter must validate conv+hi+lo+scales DATA intervals, cold cache
and shared_by map before actual model-forward; retain48 observed GDN receiver
bindings, original request admission and ownership/noRetry. B1/eager smoke and
final192plan/prefill-pack/fullcachelifecycle gates precede paired performance.
B16 numerical operator acceptance does not prove real C16 scheduler support.
Do not change formal performance workload to B1 and claim C16 acceptance.

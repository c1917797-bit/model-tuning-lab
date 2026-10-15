# MXR044: real32K gap and minimal source implementation (NOT READY)

No NPU/remote/Git action was performed. 043 remains frozen. This packet is a runtime/math adaptation plus an executable numerical callback/CPU consumer, NOT a new model/PF owner. It does not grant numerical/model/performance/task qualification.

## Why043 is not32768/C16

043/042 refiner has MAX_TOKENS192/MAX_CHUNKS4. Its whole packed FP32 correction conservatively retains about1056MiB at32768, exceeding both042's32MiB diagnostic pool and original formal512MiB pool. Raising those constants alone is invalid. C16 means16 concurrent requests; scheduler's max_batched_tokens40960 bounds ONE packed prefill solve, not16*32768. Actual serving recipe/config must prove that bound before use.

## Chosen implementation, not the earlier grouped037 design

block_refine.eager calls the UNCHANGED official037 launcher once on original full FP16 conversion, original cu and original chunk count. It then refines independent64x64 matrices in groups of at most64 chunks, using the same original-A32 residual R=I-(I+A32)X0 and X1=X0+X0R, two FP32 bmm per group. Six packed FP32 buffers plus explicit FP32 scatter buffer are allocated once and reused on the SAME stream. Full contiguous groups pack/scatter with strided copies; tails are independent matrices grouped separately. This changes layout/scheduling, not equations or thresholds. No new C++/DSO/build or CPU solve substitutes the actual candidate.

The discarded16-chunk design would launch03741times at worst655chunks and make82FP32 bmm. Current design:32768B1 has1 official launch+16 bmm;32768+8192 packed40960 has1+20; max655chunks/B16 has1+38 (full runs plus tail group). More launches than native remain a real performance risk; no gain is asserted.

## Working-set proof / limits

At40960: originalA120MiB + fullFP16 conversion60 + original037 FP32 X0120 + BF16 output60 + fixed7packed-equivalent scratch84MiB + identity/metadata about.024MiB = about444.024MiB strong-reference payload. It fits ONE existing512MiB ticket; TWO do not fit. KeepalivePool's EXISTING FIFO/event backpressure waits the previous SEALED ticket before allocating another longest call. No unsealed global ticket blocks its own child tickets (there are none), no per-group synchronize/D2H, and no pool increase. All buffers remain held to the final actual stream event; failures after foreign entry quarantine. Larger backing storages of input views/cu are counted, not just numel. If that exceeds the original pool, reserve rejects.

This is NOT a bound on CANN allocator/compile/internal-workspace peak; actual longest-case NPU peak and fullmodel HBM headroom remain required. Model weights/FA/GDN state memory are outside this private inverse payload. CPU/NPU budgets may not be inferred from these bytes alone.

## Real production seam reused

Use existing actual004/005 Associations->Certificate->eager_receiver chain. Only add immutable host_boundaries to Certificate and its verified consume result, then pass that tuple to block_refine.eager. Original producer epoch, attach, cu/indices identity/version, per-prefix single-use, original fwd/core dispatch and source guards remain. No new outer chunk wrapper is installed, so snapshots' function identity is not deliberately broken. Actual005 production_binding assigns the real copied Qwen target directly to the same algorithm_core, without diagnostic capture or per-layer files. Stale sibling support-module imports are rejected.

Zero-length segments remain rejected by existing metadata_certificate.host_geometry and therefore take native fallback; block planner's ability to enumerate them is not service qualification. Graph remains refused/native fallback, PCP1 and eager actual source only. q.lengths are still an EXPLICIT QUALIFIED whitelist. Missing full-GDN/multistep/lifecycle/length qualification remains refusal; do not expand q.lengths or switch mode=performance just because local tests pass.

common_precision.environment must be applied identically to BOTH dense/candidate environments, registering mxr_common_precision044. Actual worker receipts record effective HF32off; pair_gate requires both arms' four already-proven worker PID mappings. This only establishes common Torch matmul policy, not vendor-internal exactness. Dense output/input/prefix-cache/async/graph/commonopts/output1024 are unchanged by this module and remain the existing pair owner's responsibility.

## Next actual numerical node (no new controller)

qualification_probe.produce is fully implemented to be called AFTER existing042 Owned child setup/actualDEVICE->SMI->ARM, passing initialized actual037 solver, original512MiB/2 KeepalivePool, EventBackend, exact source/probe/ARM refs and existing900s child deadline. It makes9 source-preregistered cases x3 repeats: two unchanged real16/40 A129 (also actual old-refiner bitwise peer);32768; packed32768+8192; worst655chunk16-segment40960; four16-segment groups covering every tail0..63. Long matrices are explicitly tiled from actual042 real A64 submatrices, NOT genuine longest wholemodel Q/K/V capture and not a globally unseen accuracy sample. Source seed2610154401+ordinal and grouping are fixed. Raw cap1.25GiB is registered within original4GiB disk budget; no RAM/phase increase.

Independent qualification_probe CLI uses original FP64 inverse/metrics (.002/.02/.999 unchanged), every valid tile/head and three repeats, immutable original input and two actual legacy-short bitwise controls. Failed metrics are persisted, not threshold-adjusted. Successful operator evidence is NOT fullGDN/model/PF permission.

### Exact remaining execution gaps (no false READY)

The existing042 owner cannot run this packet UNCHANGED: its child/report/cardinality/CPU receiver is four-arm9raw, whereas044 is nine cases each containing3outputs and its own independent result. MAIN must source-bind a thin existing-owner child/body+CPU receiver adapter to call the supplied produce/consume APIs, retain DEVICE/SMI/ARM/stop/release/ledger, and cold-test the actual host/result ABI before NPU. No such owner adapter or actual same-imageCPU/NPU receipt is claimed here. No new resource platform was created.

After that: actual longest/varlen operator PASS -> new math fullGDN/model qualification including real32768/40960 and multistep/metadata -> extend existing formal admission SOURCE pins -> existing fixed1024 paired driver. The copied005 admission intentionally still refuses new full_numeric evidence not meeting its original full model/lifecycle contract; it must not be bypassed with043/042 component PASS. Old005/012 captures are OLD math;043 new refined129 alone is not32K/mixed proof. Original005 PF-host integration tests were not cloned/run; only its direct-target API controls are in this runtime packet. These are real remaining critical edges, not plans labelled runnable.

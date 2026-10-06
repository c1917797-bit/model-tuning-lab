# Explicit UB, queue, writer and synchronization audit — not a pass

Original work79872B and queues18944B are retained. New disjoint TBuf42496B is allocated first; no original live buffer is reused for the quantizer. Total explicit allocation **141312B**, excluding compiler stack. The initial four-argument Broadcast's hidden LCM assumption was removed by the public five-argument call using the existing8192B scratchB_ region only after its LoadState use has ended; the actual2201 implementation needs at most1024B. See BUILD_V2_REPAIR.md for exact SDK source hashes and lifetime proof. Neither192KiB capacity nor an arbitrary8192B stack allowance is an observed allocator bound.

| New region | Byte range (end-exclusive) | Size |
| --- | --- | ---: |
| certWork0..15, each INT32[448] | [0,28672), plane1792 | 28672 |
| accepted INT32[448] | [28672,30464) | 1792 |
| quotient FP32[448] | [30464,32256) | 1792 |
| repeatedScale FP32[448] | [32256,34048) | 1792 |
| magnitude INT32[448] | [34048,35840) | 1792 |
| correctedCodes INT32[448] | [35840,37632) | 1792 |
| originIndices INT32[448] | [37632,39424) | 1792 |
| compactIndices INT32[448] | [39424,41216) | 1792 |
| C/F INT32[128] each | [41216,41728),[41728,42240) | 1024 |
| reject packed mask UINT8 storage | [42240,42496) | 256 |

Every new range is disjoint and 32B aligned. Mask offset is also256B aligned within the TBuf; that is **not** a physical allocator alignment receipt. Raw x aliases only original lowFloat offset for read-only use, and quantizer scale is copied per each of four rows from original scaleVector. Sign/packed-mask temporarily reuse quotient/cert0 after their prior consumers finish; repeatedScale is reused as FP16 cast destination only after scalar ExactCode reads finish.

Queues (original six queue objects, eight allocated buffers): metaIn1*160;tokenIn1*864;planIn1*2048;stateIn1*5120;packedOut2*5120;output2*256 =18944. No new TQue/crosscore event. Existing Fetch V_S event plus newly matched S_V event are direction-specific resources; exact device allocator/event quota remains a real build/runtime gate.

| Producer -> consumer | New dependency |
| --- | --- |
| Immutable tiling/LUT GM MTE2 -> V | reused planIn EnQue/DeQue; 1024B load/core once |
| LUT UB DataCopy -> Certify Gather | PipeBarrier<PIPE_V> before freeing input and later consumption |
| raw x/scale -> Div/bit sanitization/RINT | per-stage V barriers; Div only proposer |
| certificate -> sign/mask -> GatherMask | V barriers, packed bit comparison, count448>0 |
| GatherMask indices/raw inputs V -> S | explicit Fetch/Set/Wait V_S before GetValue |
| only retained ExactCode scalar writes -> Cast V | explicit Fetch/Set/Wait S_V on both valid/failure paths |
| packed output V -> GM | original packedOut EnQue/DeQue then full-group DMA |
| complete head BF16 V -> GM | original output queue and full256B DMA owner |

GatherMask count-safe guard precedes compact dereference, lane-range guard precedes raw dereference. Its unused suffix is never read. Each group owns1024B high +3584B low +448B scales at original non-overlapping slot/Hv/group offsets; all transfers are32B multiples. One core owns full head output; no small per-lane GM SetValue/atomic scatter. Quotas, UB overflow, out-queue early free path, exact API lowering, mask storage and pipeline visibility must be confirmed on real NPU. Static source equality/sums do not close these gates.

Actual isolated certificate/compaction and new production saved-step45 ran successfully on910B4 physical4. These cases provide bounded ordering/arithmetic/guard evidence, not a complete allocator/stack proof, B16 feedback proof, graph gate or service acceptance. See ACTUAL_GATES.md; preserve every still-unfilled gate.

Cannbot review scope used: direct-invoke/PTA ASC queued route, precision-debug, sync-audit workflows/fix-patterns, npu-arch and API GatherMask/buffer/pipeline/precision references. No generator/cleanup script or original repository was modified. A generic scanner reporting no visible flow is not treated as proof; any later scanner candidate must be preserved and reviewed rather than blindly applied.

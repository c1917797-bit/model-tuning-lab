# Independent step-45 NPU arithmetic trace (diagnostic draft)

This directory is a standalone direct-invoke AscendC build. It does not modify or replace the production operator, its namespace, registry, libraries, gates, or old failure records. The production v4 numerical failure remains unresolved until fresh actual NPU evidence proves the cause.

## Question and frozen provenance

Restricted-native-golden v2 first diverged at B1 identity step45. Updated native FP32 independently repacks to the saved golden. One low code differs: selected token0 / head6 / reordered V77 / lowK40 (original V41 / K126). Native x is FP32 bits 0xbd05a10e, scale 0x39919209, IEEE quotient -117.5, RNE -118; saved production output code is -117. The 20 CPU arithmetic hypotheses suggest fused-vs-separate multiply/add rounding, not proof of CANN execution. Neither native nor candidate source naming MulAddDst guarantees a specific hardware rounding topology.

Frozen fixture SHA256: 59795deab9d00328df79dfeeefa08ff6d917f455bfe9d7565d0fd9c3cbf70598.
Frozen production v4 library SHA256: 22f522cf5befcf6afa12560dd2624fd6ddb1c99cc8d9bf04a4b08502363b3937.
Original numerical gate stays state max-head relative L2 <= 1e-5 and output <= .00303. This diagnostic has no replacement numerical acceptance threshold.

## ABI and seams

Distinct TORCH_LIBRARY namespace: qwen36_damp_trace.
prepare(query, high_state, pk, pv, inv_pv, sr) -> () must run eagerly before decode.
decode_trace has the same fourteen production arguments in the same order and mutable a/b/c state aliases, returning (out BF16[T,12,128], updated FP32[T,12,128,128], quotient FP32[T,12,128,112]).
All plans are INT32[12,128] logical indices. SR is FP32[12,128] original-coordinate c. Physical ND format2 is strictly checked, not silently converted by the wrapper.

updated is copied after the production UpdateReadout and before PackStore. quotient is copied immediately after the existing low-region Div and before the existing FP32 CAST_RINT. No state arithmetic, reduction, update, scale, rounding, or clipping is replaced. Functions MatVec/ReduceRows/UpdateReadout/LoadState/LowBroadcast are exactly audited against the pinned production source; PackStore and ProcessTask differ only in trace calls. Scalar task identity does not affect arithmetic.

A separate VECOUT depth1 queue stages immutable trace copies; its 16,384-byte addition makes declared UB 115,200 bytes. EnQue/DeQue/FreeTensor provide the same event-backed ownership model as the production queues. Build and runtime resource compatibility are unverified. Trace tensors are not initialized for invalid metadata; this saved-valid-fixture diagnostic does not test or promise invalid-metadata trace contents.

## Pre-registered interpretation

1. Verify source parity, explicit source/library hashes, same image/CANN/device mapping and immutable fixture identity.
2. Load the exact frozen production v4 library and this independent trace library by absolute paths, without replacing either.
3. On fresh independent packed-before arenas, execute production once and trace once with exactly the saved step45 inputs. This is a one-shot attribution test, not another closed-loop matrix or a resynchronization trick.
4. Require production after/output bitwise equal the saved actual, and trace after/output bitwise equal production. Untouched slots, immutable inputs/plans, pointers and ND format must stay exact; trace FP32 fields must be finite. If tracing changes production bits, retain failure and stop attributing it.
5. Then compare trace updated FP32 with the saved native updated FP32. Independently scalar-pack trace updated and compare high/codes/scales; separately RNE-clamp the traced quotient to verify the actual quantizer. Record IEEE division vs actual traced quotient, FP32 bits/ULP and original coordinates at every differing code.
6. Updated differs but quantizer is faithful: investigate real update lowering. Updated matches but quotient differs: investigate division lowering. Both updated and quotient match but code differs: investigate RNE/cast/store. No hypothesis becomes a conclusion without its actual seam evidence.

The extra GM stores/UB/queues can change scheduling and compiler choices. Exact production alignment is necessary, not optional. No performance timing belongs to this diagnostic. It cannot claim compressed recurrence passes, arbitrary SR coverage, graph replay, serving integration, 48-layer calibration, task accuracy, or >=10% E2E gain.

## Build (parent-controlled; child did not execute)

Use a NEW output/build directory in the unchanged same image with physical NPU hidden for compile/Meta. Configure this directory as source, not its parent, and preserve all logs/errors:
cmake -S /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/diagnostic -B <NEW_BUILD> -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3
cmake --build <NEW_BUILD> -j2
Do not delete or overwrite old build directories. check_source_parity.py uses Python stdlib only. The parent owns build, Meta load, fresh device checks and the one physical-NPU4 execution.

## Skill/source choices

Reviewed repository-adapted Torch-AscendC direct-invoke, repository coding red-lines, direct-invoke template, launch and AscendC API lookup skills completely. This .asc-included wrapper retains queued stream(false) + OpCommand::RunOpApi, not a C++ split direct-launch recipe. It does not assume registration means graph support, overwrite any old target, or generalize A3 rules to current 910B4/CANN9.1.

Official CANN9.1 API evidence: DataCopyPad UB-to-GM uses byte blockLen and supports A2 FP32; TQue EnQue/DeQue/FreeTensor owns synchronization. MulAddDst documents dst + src0*src1 but does not freeze fused rounding:
- https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_UBToGM.md
- https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/resource_management/TQue/DeQue.md
- https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/MulAddDst.md

Licenses and original attribution remain in the parent operator/LICENSE-APACHE and repository root CANN license; this diagnostic retains the copied file notices.

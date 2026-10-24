# BOLE verification cost audit — SOURCE_ONLY

## Evidence and scope

MAIN reopened V16 RESULT at /opt/host/vnf/austinov/run-bole32k-lossless-profile-disk-short8-v16-20261024/RESULT.json: 2231146 bytes, SHA256 3028f15dddafc54551e998bfae2d53be66f286a235f28a84b6e48025e2f76f51. MAIN1478/1479 checked task-owned reports; the assisting cost reviewer did not independently open these remote originals.

The actual R0 G1-O0 mathematical report at dense/receipts/FASTPATH-NUMERIC-R0/G1-O0.json is82596 bytes, SHA256 db10eb879588104c57e2c874796ba1d25531027fdf96f1af6f6eac950888f12f. RAM pre_export report is1426 bytes, SHA256 281fd892a36bb439dd01c36bb5b773f8086188586ede04d7f8ea5c83985e49b0. The mathematical report has frame_checks_passed=true, domain_complete=false, whole_model_pass=false and logical_tensor_bytes=99554048. This last value is not total external FA IO or memory peak.

## Corrected timing conclusion

RAM reports contain no epoch/duration; recursive inspection of the complete mathematical report found no elapsed/duration/epoch/start/end/seconds/timing/monotonic fields. PID start_ticks is process lifetime identity, not a stage timestamp.

Earlier130–150s and70–77s approximations from adjacent file publication mtimes do NOT establish native algorithm, consumer, CPU or NPU execution time. Host total wall also includes source checks, software, loading, copying and cleanup. V14 per-stage timings remain unmeasured here.

Consequently,160-output timefit is UNPROVEN and risky, not a proved universal >3600s result. Keep the original deadline, phase and cleanup gates; no coverage reduction or automatic extension.

## Source-supported operation scale, not measured physical IO

Given264 native pages,128x256xBF16 per page,16 FA layers and before/after K/V reconstruction:16x4x264x65536=1107296256 logical bytes per frame,16896 logical block reads. Deduplication and page cache mean this is not unique physical disk traffic. If the actual row also includes two257-page scratch K/V pairs, it adds538968064 logical bytes, for1646264320 total; this addition is conditional, not a measured count.

The reviewer read its allowed V16 fa_block_store.py copy(10603 bytes,SHA256 a4fc9d7619438b80cedcbe90f1f02d7487b1b197393468fc69dd807949d6b6a3). Reader.raw/tensor reconstructs blocks with full hashes, joins pieces, allocates bytearray and clones the Tensor. This proves copying work exists, not that it dominates. Its exact source-to-bound association must be checked before any optimization.

MAIN read the actual frame-declared g2_numeric.py(24956 bytes,SHA256 e2b66454b354175e1b00708ebbb70cd562a707acce34e8678ea581d7b6c2da91) fa_math: prefix K/V each use per-token indexing/stack; then FP64 and FP32 references each retain three nodes and six heads. This is another operation-scale candidate, not a measured bottleneck.

## Next discriminating action

Measure source/rank/generation/ordinal-qualified monotonic_ns and process_time_ns around capture/D2H+archive, reconstruction/hash, independent consume, and report publication. Aggregate by layer, not noisy per-block logs. Count logical bytes/calls. Do not sum nested intervals as exclusive time, sum four-rank walls as model latency, or subtract CPU wall to invent NPU time. Native device timing needs its own qualified event/profiling boundary. New timing fields must fit the existing source/metadata/terminal contracts.

Only after measurement, consider a minimal exact optimization. Removing Reader.tensor's final clone is a hypothesis because bytearray is already private; it requires same-image bitwise checks, independent-read nonaliasing, GC lifetime, real downstream storage/in-place/resize audit and complete original-frame consumer comparison. Prefix gather/stack reuse likewise needs exact ABI/value/order checks. Neither is implemented, approved, measured or guaranteed to make160 fit. Keep all full hashes, layer/request/128-write coverage, math thresholds and RAM reservations unchanged.

No new experiment, container, device access, source permission, authority or task/performance PASS is created by this audit.

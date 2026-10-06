# Minimal v2 source repair following actual no-device compiler failure

Actual MAIN operation MA0335 ended FAILED; configure exited0, build exited2.
Read evidence (preserved externally, not replaced):
- /cache/cch/qwen36-damp-20261006/compaction-build-v1/build-receipt.json
- /cache/cch/qwen36-damp-20261006/compaction-build-v1/phase-1.log
- CANN9.1.0, dav-2201; image SHA256660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1.
- phase1 log SHA2560db4fb57cba2e6f72fa52d34c18157f7028e8ebfef2cfb02370eb7046ce99eac;
  receipt statusfailed, npu_executedfalse; completed2026-10-06T13:13:21.072866+00:00.

Two observed compiler errors ONLY:
1. compaction_probe.h:53:36: GUARDS[i] used std::array::operator[] from
   __aicore__; compiler rejects host-only method.
   Fix: same four values in constexpr int32_t GUARDS[OUTPUTS] C-array; remove
   unused plan <array> include. Wrapper's own std::array remains host-only unchanged.
2. compaction_probe.h:59:9: Duplicate<unsigned char> is not supported by actual
   dav_c220 implementation. Diagnostic states supported uint32, not uint8.
   Fix: Duplicate(packedMask.ReinterpretCast<uint32_t>(),uint32_t(0),64);
   same full256B zero bytes, SAME packedMask offset/shape and following CompareScalar.

Byte-preserved v1 sources:
- audit/probe_plan-v1.h.txt SHA256d45955942a930d3d73c90a86d7f740ec8d7c2ca561a1d8e0bdf40606016676bf.
- audit/compaction_probe-v1.h.txt SHA256bb9fea145f7ffeb34534e24c707d32bdffbf9de31aec5d423c771f7c4d015798.

No change to CompareScalar/GatherMask, exact fallback, UB50688B, dataflow, schemas,
mathematical oracle,49 fixtures, runner, guards or gates. New software assertions
compare guard values against independent fixtures, verify complete256B zero fill
and exact v1->v2 textual diff. These are NOT compiler/load/NPU evidence.
MAIN alone will full-review minimal diff then fresh compaction-build-v2.
Do not retry original failed v1 configuration; do not reset DAMP deadline.

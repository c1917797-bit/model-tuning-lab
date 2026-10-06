# Manual/static source preparation record

This record is source-level only. No ASC compilation, no devices, no timing, no acceptance.

Actual remote source contract v1 MA035d failed because the software test called the existing K128 method by a non-existent name MatVecK128; actual source method is MatVec. Only the test name was corrected; seven compilation files were kept frozen. The failure receipt is preserved in audit/source-contract-v1-failure.json. Fresh v2 MA035e terminal0 ran71ms and passed source hashes/eleven unchanged bodies/pack prefix+store suffix/ProcessTask sole error-control seam/N448 new26 disjoint UB regions/LUT equality/stream split/host-projected global. Raw stdout and operation evidence are preserved separately. This does not prove ASC stub emission or NPU execution.

Actual read-only diff generation MA035f terminal0 yielded29274bytes in ORIGINAL_TO_CANDIDATE.diff. Original seven files and shared two helpers were re-hashed by MA034f; original production SHA ecc24f...a856 and helpers f5d380...6169/e96cbd...b9cb are unchanged. Full hashes are in source_manifest.json.

C/F logical INT32 tables, little endian128 entries, match frozen model exactly: C SHA7c6e8dbfe3ea2a3dcaf62ab2ef14936d2d9252a36738eb6b78ba4b1d37c7c708; F SHA2df58f09be50ce6051418c229acf641a37c9596f1826884ee02d7a02b1581a83.

Public API checks carried forward from isolated probes: current ASC queued wrapper/RunOpApi stream(false), explicit public ND query/cast, CompareScalar packed rejected mask, CreateVecIndex, GatherMask counter N448 with parameters(1,1,8,1), V_S then sparse scalar ExactCode then S_V. Host-visible annotated global is retained, device-only implementation includes retain frozen dav2201 restriction. No std::array member call or Duplicate<uint8> in device source. The newly observed compaction build failures belong to that independent probe; they do not constitute candidate compile results.

Unclosed hazards requiring MAIN review and real execution:

- GatherMask retained count/order and packed-mask semantics; production does not rely on unused suffix.
- All pointers/backing intervals and physical ND; conservative full-storage guard intentionally rejects shared backing until typed-arena ownership is separately implemented.
- TPipe physical alignment/event quota; original6queue objects/eight queue buffers plus direction-specific V_S/S_V. TQue FreeTensor on early failed packed-out allocation path is untested.
- Explicit141312B excludes original Broadcast LCM and compiler stack; no guessed8192B bound/192KiB observation.
- IEEE exact fallback helper scalar uint64/clz lowering and post-S_V cast path, and invalid state/nontransactional earlier group writes.
- Metaregistration does not prove graph; prepare has no graph-capture validation receipt.
- ~many SIMD operations/barriers per chunk and sparse fallback cost can erase memory savings. No proposal acceptance ratio is a speedup.

No Cannbot scanner has yet been executed for this candidate. This manual record is not a zero-redline scanner report; source scanners, if run, must preserve every candidate and failed/empty-flow output without modifying original Cannbot cache. Required NPU gates remain unchanged.

# New-candidate const-correctness source fix — not a compile result

Before any build, a source review found that the new LUT binding used reinterpret_cast to remove const from const __gm__ DampTilingData*. It is not valid standard C++ const conversion. MAIN authorized a narrow new-directory fix: preserve the const read reinterpretation then explicit const_cast for the public GlobalTensor nonconst pointer setter, retaining LUT_OFFSET_INTS. No arithmetic, external/internal ABI, layout, scale, recurrence or event sequence changed.

MA0368 verified the byte-exact v1 header archive SHA966a675c2e8c640b935b3fa08b253c2271672c89a2581a431649b7ee83480b84, and the new active header SHA891703ddd6f10ddb56d4103b448e3c06ed5f0c8d91e31bf4caf11aca86168f77. Old source manifest/diff and source-contract-v2 raw receipt remain separately archived; the active manifest/diff now bind the corrected header. The only uses of quantizerLutGm_ are pointer binding, private declaration and DataCopy(local,quantizerLutGm_,256), where GM is the source. There is no LUT GM writer/SetValue.

This is source preparation only. No compiler, linker, dynamic loader or NPU has executed the candidate. No passing outcome is inferred from const_cast or source equality; MAIN owns the real next gates.

Fresh source-only v3 MA036b terminal0 ran70ms: full9 compilation dependency hashes and7 originals,11 unchanged original method bodies, the byte-exact archived v1 header, and LUT GM read-only use-count checks passed. Raw evidence is in audit/source-contract-v3.json and audit/source-contract-v3-execution.json. This software result remains asc_compiled=false/npu_executed=false and does not validate const-cast lowering.

# Exact retained018 provenance caller repair
Original0574 failed before numeric at consume_prefill.py321. Original capture_tiles writes capture_source_sha256 = SHA256(prefill_provenance.py)=a93894..., while original consume_raw supplies runtime_roles.capture=398cd59...(native layout collector). These are distinct source roles.

New raw caller source c7779d479ba82c4771d5e7a15a85a3ab3b1505fbde6fa875f9ea74e50e8487c1 derives unchanged original consume_raw.py3252/05ed6ed6:
- retain exact original loader/source205, modules/geometry/oracle/writer/codec and all aggregate arguments;
- only aggregate argument capture_sha256: roles["capture"]["sha256"] -> roles["provenance"]["sha256"];
- source-qualified new entry --entry-sha256 is mandatory and checked;
- retain and read original caller + both original distinct capture role Refs;
- output records explicit caller/originalcaller/provenance/native-layout sourceRefs.

Whole consume_whole.py 933d4324c9e15ae97d7df48558029ae7f1d49d2e356dc6defcc1ae1ff4123e44:
- exact new caller/old caller/source role metadata checks, all64 writer installer+capture receipts;
- child argv checks exact new caller path and --entry-sha256; original producer_only/raw_result/numerical bodies unchanged.
Five inherited whole files byte-exact including original EOF.

Raw host changes only new caller read-only source root/mountedCLI, one source-field passthrough, two basecore pins and software fixture archive. Resource budget/Devices[]/ownstopretain/full64/5400incl90 unchanged. No peer expansion.

Tests:115 originalwhole +69 originalresource +8 new actual-five-original-chain/seven-source/actual-entry/AST-call equivalence/whole-source regression =192. LOCAL_0018errors was test PINS=dict AST extraction, original retained; LOCAL_002192PASS16.130s. Tensor aggregate in entry control-flow regression explicitly fixture, actual numerical64 UNRUN.

Old producer018/whole021/raw022/actual0548/0574 remain immutable. No NPUrecapture/no mathPASS/no whole176/FULL/mixed/perf claim.

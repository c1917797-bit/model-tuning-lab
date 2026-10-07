# SparQ v4 actual no-device ABI failure, not paper no-go

Original MA exec-0000000000000ef8 terminal exit1/49.658s.
Root /cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-token-native-v4-20261007-1910-001.
RESULT SHA b78a761ef82e8d941efa297c83fdaebf897efa4c36be07cd54804b9accf0d618.
CPU-only original command receipt SHA fbbc184b6e606080318dc982b30b86d510ca607bb1ef5f37b7f1421e8f2663c5.
ABI.json SHA6831432f7cead82b13d1dffc6dbd2e2b5d714cf37ae7802d6611cf4c22214677.

The real same-image CPU-only source/export prerequisite failed at
preflight.py exports(): expected slot_mapping in the bottom native
_npu_reshape_and_cache complete argument list.
Actual pinned device_op.py SHAde6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47
shows a concrete API distinction:
BaseDeviceAdaptor.reshape_and_cache(...,slot_mapping) calls
torch_npu._npu_reshape_and_cache(...,slot_indices=slot_mapping).
The v4 observer used a wrapper keyword as the lower native keyword. This is
an adapter-observer contract error; it does not show unsupported native
cache writes or rejection of the SparQ paper mechanism.

Neither CPU golden smoke nor candidate NPU/canary/matrix ran. No NPU CID was
created. Failed ABI receipt npu_executed=null is preserved, not rewritten.
Independent MAIN MA0efd exit0/1.358s verified exact CPU-only CID
63d09431f20cb84ad557746fcc3bebdefca500370fcb735abdd0c3ecb875e431
stopped/retained/Pid0/noExec/noOOM; devices/requests/rules absent. Four authorized
cards idle/healthOK, protected0–3 original585850–53 identities unchanged.
No external CID was stopped; no original runtime/image/core algorithm modified.

Next: source-supported independent v5 observer preserving both actual wrapper
and native API identities and their exact keyword mapping, with actual schemas/
signature/doc and initialization/node evidence persisted BEFORE assertions.
Keep all original algorithm/core/native writer calls/numerical thresholds.
Do not delete a parameter gate, union incompatible overloads, relabel v4 PASS,
restart its retained CID, or repeat its deterministic failure. Fresh v5 source/
software review and actual CPU-only prerequisite precede any new NPU stage.
SparQ TP4 service003 remains preparation and cannot inherit numerical authority.

Separately, extra MAIN read-only admission0ef3 incorrectly asserted returned
own-source dictionary length23; source_identity actually returns17own and
validates the full23-source closure. Exact private/canonical hashes match0ef5;
correct source-derived read-only admission0ef7 passed. All originals retained;
no algorithm or acceptance gate changed and no NPU was used by these probes.

Memory32GiB release is complete; OVS24GiB unchanged, no further reclaim.
Paper/portfolio clocks remain fixed. No model/performance/final task result.

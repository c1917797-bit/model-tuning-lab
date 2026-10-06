# All-batch shared-arena wrapper v3 — default OFF

Source prepared only; no v3 build/load/Meta/NPU/graph/service result is claimed.
Namespace `qwen36_damp_all_batch_v3`, SO
`libqwen36_gdn_damp_all_batch_v3_decode_ops.so`, annotated launcher
`qwen36_gdn_damp_all_batch_v3_decode_kernel`, explicit build switch
`DAMP_BUILD_ALL_BATCH_WRAPPER_V3` defaults OFF.

## Exact existing blocker and smallest adaptation

The frozen numerical header SHA
`15142a8360043e30cafbaebd19e2f528573819dcfdb519580867732e69340ff1`
is NOT already runnable at T2–15. Its LoadValidateMetadata, line162, explicitly
returns invalid for `(tokens_ != 1 && tokens_ != 16)`; merely changing the host
and Meta would therefore produce NaN outputs. Original source and binaries stay
unchanged.

This separately named candidate copies that header with exactly three source
differences: new include guard, explicit path to the original byte-exact tiling
header, and that single device token-range predicate replaced with
`(tokens_ < 1 || tokens_ > MAX_TOKENS)`, MAX_TOKENS=16. All arithmetic, DMA,
padding, slot/duplicate/length validation, readout, quantization, LUT, UB
allocations and event synchronization remain byte-for-byte unchanged.
The copied header retains original copyright/provenance comments, referring to
the original v1 source; those comments do not assert this candidate passed.
Original native arithmetic attribution/license remains in
`../production_integer_compaction_v1/README.md` and LICENSE-APACHE.
ALL_BATCH_DIFF.patch is the exact readback-derived full diff.

Host and Meta batch predicates likewise admit only T1..16 in this NEW
namespace. This is a proposed extension backed by SOURCE_PROOF.md and source
contracts, not a relaxed numerical acceptance gate. Real execution still must
prove every newly admitted T. No code/importer/lease in the existing service
adapter has been silently switched to this namespace.

## Same ABI and arena checks

prepare six inputs and decode fourteen inputs remain unchanged. Each token is
one decode step, not an arbitrary flattened mixed/prefill token. Lengths must be
[0,1,...,1], indices unique/in-range, and all request states initialized.
q/k BF16[T,4,128], v BF16[T,12,128], g FP32[T,12], beta BF16[T,12];
hi FP16[S,12,128,16], lo INT8[S,12,128,112], scales FP32[S,12,4,112];
pk/pv/invPv INT32[12,128], positive FP32 original-coordinate SR[12,128].
Fresh BF16 output[T,12,128]; a!/b!/c! mutable state schema unchanged.

Arena-v2's complete physical-ND/contiguous/same-device/aligned pointer/offset
equality/overflow/backing bounds checks and DATA-byte-interval nonaliasing
remain exact. Readonly short metadata/g/beta are NOT required to have a 32B
byte length. Mutable regions and whole-head output are. Conv is not a decode
argument: integration must validate all four typed regions, actual shared_by
map and arena lifetime. No separate-allocation escape or persistent FP32 state.

Only actual Ascend910B4, compile target dav-2201. Immutable plan/tiling prepare
is cold and synchronizing, outside capture. Its key already includes T, S,
device, vector cores and immutable plans/pointers/versions. Changing T requires
a separately prepared identity and graph. The single ASC TU queued
RunOpApi/stream(false), public TorchNPU format API, host-visible global definition
and independently named SO are retained.

Inherited Meta limitations remain: shape-only proof is not physical format,
byte spans, all-input contiguity, S upper bound, actual plan values or
functionalization/torch.compile/NPUGraph acceptance.

## Build preparation and software result

Actual MA0445:11 unittest methods PASS using only standard-library source/hash
and integer geometry/ownership models. No Torch import/device/API execution.
Compiled-source manifest has six NEW files plus three exact delegated headers;
the original mathematical header is a source reference, not a delegated compile
dependency because its fixed B1/B16 validation would prevent T2–15.

MAIN may build ONLY in a fresh external directory, same identity-verified
CANN9.1/image/ASC environment, full repository read-only dependency mount:

```text
/usr/bin/cmake -S /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/all_batch_wrapper_v3 -B /cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/cmake -DDAMP_BUILD_ALL_BATCH_WRAPPER_V3=ON -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3 -DCMAKE_BUILD_TYPE=Release
/usr/bin/cmake --build /cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/cmake --parallel 2
/usr/bin/nm -D /cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/cmake/libqwen36_gdn_damp_all_batch_v3_decode_ops.so
```

Require actual non-UND defined launcher then dlopen/schema/Meta, not compile
alone. Preserve real new commands/image/OPP identity, compiled9, library SHA and
export audit in new receipts. Do not rewrite old failures or attach v1 accepted
numerical reports to this new source/SO.

```text
/usr/bin/python3 -B -m unittest discover -s projects/damp-ascend/operator/all_batch_wrapper_v3/tests -p test_all_batch_contract.py -v
```

NPU_MATRIX.md gives the remaining actual gates. Existing service12 remains
B1/eager and rejects original sharedarena. Even an all-T operator gate would
NOT establish C16 scheduler/media/mixedprefill/cache lifecycle/192plan/
prefill-pack/E2E quality acceptance. Keep those separate and do not alter the
formal dense/candidate performance workload to disguise this gap.

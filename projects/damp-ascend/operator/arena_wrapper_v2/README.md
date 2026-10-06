# Default-OFF shared-arena ABI wrapper v2

Status: source prepared only. No build, library load, Meta execution, actual NPU
or shared-arena replay has been performed for this new namespace. The original
integer-compaction candidate's accepted numerical receipts do not admit v2.

## Why this adaptation is necessary

The deployed v0.23 allocator is
`/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py`,
SHA256 `94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968`.
Its read-only snapshot is
`/cache/cch/qwen36-damp-20261006/runtime-source-snapshot-v1/model_runner_v1.py`.
Lines 4681–4714 construct each MambaSpec state's full typed tensor by slicing
`raw_tensor[start_idx:target_idx].view(dtype).view(target_shape)`, advancing
`start_idx` through shapes/dtypes. These are contiguous SoA regions sharing one
raw backing storage, not independently allocated buffers.

The frozen v1 host wrapper rejects overlaps of entire backing storages. It
therefore cannot admit these real, mutually disjoint typed views. This v2 changes
that ABI check, not the paper method, quantizer, precision, or recurrence.

## Source/ABI

Independent namespace `torch.ops.qwen36_damp_arena_v2`;
library `libqwen36_gdn_damp_arena_v2_decode_ops.so`;
launcher `qwen36_gdn_damp_arena_v2_decode_kernel`.
Build option `DAMP_BUILD_ARENA_WRAPPER_V2` defaults OFF.

`prepare(query, high_state, pk, pv, inv_pv, sr) -> ()` remains a cold,
synchronizing immutable-plan/tiling preparation outside graph capture.
`decode` retains the same 14-input ABI and fresh BF16 output:
query/key BF16[B,4,128], value BF16[B,12,128], g FP32[B,12],
beta BF16[B,12]; hi FP16[S,12,128,16], lo INT8[S,12,128,112],
scales FP32[S,12,4,112]; three INT32[12,128] logical permutation plans;
original-coordinate positive FP32 SR[12,128]; lengths INT32[B+1]=[0,1,...,1],
unique in-range indices INT32[B]. Only B1/B16 and actual Ascend910B4 are admitted.
B2–15, mixed/continuation prefill and service scheduling remain unsupported.

Each region must be contiguous, physical ACL_FORMAT_ND, same device and have a
32B-aligned actual data pointer. Every logical interval is computed from
`numel * element_size`, checked for overflow and wholly contained in backing
storage. `storage_offset * element_size` is independently checked, and
`data_ptr == backing_base + byte_offset` must hold for dtype-reinterpreted views.
All three mutable region intervals must be disjoint from each other, every
readonly input and cached tiling; fresh output must be disjoint from all inputs.
Only mutable state/output byte lengths need a 32B multiple. B1 indices=4B,
lengths=8B and short g/beta reads still use the unchanged DataCopyPad path.

Conv is not an argument to this decode operator. The real integration must
additionally validate all FOUR cache regions including conv, track cross-layer
shared_by ownership and retain the raw arena plus typed views. Do not substitute
separate allocations, persistent FP32 sidecars or global torch.ops reassignment
to bypass this requirement.

## Unchanged numerical source

The new kernel launcher directly includes the frozen production header/tiling,
which directly include the frozen exact quantizer and integer certificate.
There is no copied new numerical header. Source manifest lists five NEW compile
files plus four exact delegated headers. The normalized launcher body and Meta
registration equal v1 (only names/include paths and redundant EOF newlines).
Full diff is in WRAPPER_DIFF.patch.

The whole-head/group32 layout, reciprocal FP32 bits, updated-FP32 readout before
pack, original-coordinate output restoration before its one BF16 cast, sparse
rejected-lane exact fallback, pre-writer metadata validation and 141312B explicit
UB all remain unchanged. CANN OSLA template and original native arithmetic
attribution/license remain at the referenced original files; consult
`../production_integer_compaction_v1/README.md` and its LICENSE-APACHE.
Queued single-ASC-TU RunOpApi + stream(false) is retained. The global annotated
kernel definition/braces remain visible to host compilation; only the device
implementation/body is guarded. Never treat successful shared linking as proof
of launcher export: verify nm-defined, dlopen, schema and Meta in order.

Meta retains v1's limited structural checks: it does NOT prove physical ND,
pointer/span/alias, all decode input contiguity, high-state S<=UINT32 or static
permutation values. Runtime checks cover these; functionalization/torch.compile
and graph support are not inferred from the schema or Meta registration.

## Evidence and next execution

Actual standard-library software check MA0430: 17 unittest methods PASS. No Torch
imports/build/load/devices. Initial MA042d had two EOF-blank-line equality failures,
saved verbatim; no mathematical source or numerical tolerance was changed.
PREPARATION_AUDIT.md and audit/ retain this bounded evidence.

MAIN owns all compilation/NPU/service/Git operations. In its SAME verified
CANN9.1/image/ASC environment and with the complete repository dependency mount:

```text
/usr/bin/cmake -S /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/arena_wrapper_v2 -B /cache/cch/qwen36-damp-20261006/arena-wrapper-v2-build-v1/cmake -DDAMP_BUILD_ARENA_WRAPPER_V2=ON -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3 -DCMAKE_BUILD_TYPE=Release
/usr/bin/cmake --build /cache/cch/qwen36-damp-20261006/arena-wrapper-v2-build-v1/cmake --parallel 2
/usr/bin/nm -D /cache/cch/qwen36-damp-20261006/arena-wrapper-v2-build-v1/cmake/libqwen36_gdn_damp_arena_v2_decode_ops.so
```

The external output directory must be NEW/nonexistent. Capture real commands,
image ID, all nine sources, ASC target, OPP identity, library SHA and non-UND
launcher export in a NEW build receipt; do not edit original receipts. A raw
source manifest is not a successful receipt. No shared-launcher ABI shortcut was
taken because actual inter-library queued launch ABI has not been proven.

For software preparation:
```text
/usr/bin/python3 -B -m unittest discover -s projects/damp-ascend/operator/arena_wrapper_v2/tests -p test_software_contract.py -v
```

NPU_GATE_PLAN.md pre-registers the required same-arena numerical, byte guards,
malformed metadata and graph tests. The actual executable thin runner remains
a next step, not an already-run test. Old integration/integer_compaction_v1
explicitly rejects shared arenas and MUST stay that way until a new v2-bound
adapter and these receipts exist. This wrapper is not service-ready, not C16
scheduler-ready, not final192-plan acceptance and not an E2E performance result.

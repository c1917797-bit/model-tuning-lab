# Selected-row native reference seam v1

Status: default OFF, preparation only. This packet does not load Torch, acquire a device, dispatch Docker, or issue a receipt. No NPU equivalence has been executed. MAIN alone owns physical NPU4–7 admission, current deadline, actual image/library/schema/maps proof, commands, retention and execution.

## Exact change and source basis

The NEW object inherits the frozen `independent_allT_dispatch_v1/reference_seam.py::NativeRows` and overrides only `_rows` with independent selected-slot CPU extraction and merge. The original `anchor`, `_native`, and direct whole-native T1/T16 branch remain unchanged. Normal `step` additionally refuses use before this true-T group's new equivalence gate and the original six anchors have passed. No old module globals or `torch.ops` registry are reassigned.

Frozen `native_compressed_golden.step` performs the same SR1/power2 transform, true B1/native HQ12 expansion, lower64/WholeReduce/FMA arithmetic through the actual native op, BF16 readout boundary, independent CPU pack and guards. Full original CPU packed state is checked by the frozen unpacker before any local call, including invalid unselected high/scales/-128. Each selected slot is copied to independent S1 packed allocations, actual native sees INT32[0], and only that original slot is copied back to the complete independent CPU feedback pool. Duplicate/out-of-range slots fail before native calls. No candidate state/output is an oracle input.

Read-only native source evidence motivating, NOT proving, equivalence:

- Fixed source `/cache/austinov/src/vllm-ascend/csrc/attention/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h`, SHA `96e6d9667af1e3457316ffce92a8a983fcb90096df08e3efd13ec0b35b8b1c5b`: slot read L189; L455/463/475/476 address = `((slot*NV+h)*V+v)*K`; compute L351–400 does not read S/slot.
- Fixed checkout host tiling `.../op_host/recurrent_gated_delta_rule_tiling.cpp`, SHA `72bc53c4f46ffe3ff4d262098796ac878ae01364ba9dbaa519e417c8c0ce204e`: stores S at L299, block dimension L321–330 depends on B*NV, not S. This checkout source alone is not an actual compiled-SO proof.
- Actual native library identity must still be measured from the existing original native manifest/maps: `vllm_ascend_C.cpython-312-aarch64-linux-gnu.so`, SHA `eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a`, image `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`. Do not substitute the unrelated BF16-state ops-transformer variant for this FP32-state path.

`SOURCE_MANIFEST.json` binds all NEW runtime sources and the complete original independent packet's 41 file dependencies. Its externally supplied digest is checked before construction and before/after the new equivalence gate. This is source integrity, not signed execution authority.

## Injection API — MAIN consumer still pending

```python
rows = seam.build_reference(
    gate, protocols, native_compressed_golden, torch, torch_npu,
    repo_root, exact_new_manifest_sha256, enabled=True)
rows.run_equivalence(native, batches_for_this_physical_shard, "npu:0")
rows.anchor(native)  # Original six whole-B16 vs 16 independent B1 anchors.
# Use the existing explicit rows parameter; do not patch old globals:
case = frozen_reference_seam.clone_graph_case(
    graph_protocol, protocols, rows, registry, metadata_cases, storage_disjoint)
```

MAIN must implement/review this injection in a NEW consumer with original fresh proof/route/loaded maps/source-before-after checks and immutable original receipts. No old runner/controller/packet is edited by this packet. Calling `run_equivalence` without an admitted real native function is not device authority. The object stays blocked if a pair, source recheck, final checkpoint or original anchor fails. It only admits true T values named in the completed equivalence report; no inferred T2–15 support from T1/T16.

New preregistered equivalence gate: 192 pairs, 48 per original four-T shard. For every T1..16: S=T+3; SR1 and power2/per-Hv Pk/Pv; fixture indices 0/7/159; original slot 0 and S-1. Both full-S B1 and local-S1 calls start from independent identical CPU state, with original native guards and exact immutable input checks. Compare complete FP32 reconstruction, selected FP32 update, every cast/readout/transform field, complete packed state and original BF16 output bitwise. Both actual calls' guards must pass. Full-S native untouched slots and complete CPU merge untouched slots are separately checked. Save immutable full raw-before before either native call; retain both raw results and the exact failing exception on error.

The old 24 whole-B16-vs-16single anchors (six per shard), 64 graph cases, true T1..16, 160 changing steps/case, eight identical replays, warmups, malformed metadata and full shared-arena/candidate guards remain unchanged. The new gate is additional, not a replacement for them or final 192 calibrated plans. Thresholds 1e-5/.00303 and all original bitwise requirements are unchanged.

## CLI/source/software preparation

All paths below are canonical. CLI is audit/plan only and default OFF; `--execute` raises Pending before any framework import. Replace EXACT_SHA with MAIN's independently checked NEW source-manifest digest.

```text
python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/tools/selected_row_reference_v1/test_seam.py
python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/tools/selected_row_reference_v1/seam.py --repo-root /opt/host/vnf/austinov/model-tuning-lab --source-manifest-sha256 EXACT_SHA --batches 1 2 3 4 --audit-only --gate-plan
```

Remaining original shards use batches 5 6 7 8, 9 10 11 12, and 13 14 15 16. Device CLI is deliberately not self-dispatching: `run_equivalence` is the callable gate interface and actual NEW consumer/proof bridge remains pending.

Standard-library tests use symbolic row containers and a SYNTHETIC stand-in, not floating-point math, actual loaded source proof, Torch semantics or NPU execution. They exercise source drift, full unselected-state validation, original-slot/index0 routing, read-only/full CPU merge, malformed indices, local result ABI/casts, exact exception preservation, secondary retention failure, gate-before-use, report-save failure, raw-before non-overwrite, 192/48 matrix and default-OFF CLI. Any simulated returned NPU booleans remain in memory, never authoritative run receipts.

## Evidence scope and cost caveats

A local S1 untouched set is empty. Its frozen native `untouched` check is therefore vacuous; the NEW result explicitly labels this and proves all other ORIGINAL slots bitwise by full CPU merge instead. The unchanged full-S numerical preregistered comparison independently checks the actual full-pool native untouched state. This does not claim the full original pool was transferred to or observed on every later row's NPU call. Candidate complete raw arena/conv/padding/untouched guards remain in the original graph gate.

Current-row before/after CPU clones are bounded in memory and retained by original failure handling; a process kill can lose the current row. The new equivalence raw-before files alone are durably written before dispatch. The adapter preserves the same exception propagated by the frozen helper, including its available dispatch/copy fields, and does not let its own secondary retention error replace that primary. The frozen observer's existing pointer-after/copy exception limitation is not repaired or hidden here.

Static transfer model only: preserving native call counts and the whole T1/T16 path, localizing intermediate-T rows and split anchors changes modeled full-state transfer from 3487.711 GiB to 305.355 GiB across four complete original shards (91.24% reduction). This is neither measured elapsed time nor performance evidence; CPU full-pool validation/clones, quantization, native-call overhead, reporting and extra 192 pairs still cost time. No timeout, deadline, live source or sample count is changed, and the same mathematical equivalence remains pending actual NPU proof.

Not admitted: general SR, final calibrated plans/SOURCE_LOCK, prefill or continuation, persistent production/cache state, scheduler/mixed turns, real 48-layer TP4 service, formal TTFT/TPOT/E2E speed or task accuracy.

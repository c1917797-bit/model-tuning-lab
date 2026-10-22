# BOLE clock repair and long160 preparation checkpoint

This is a source-only checkpoint, not numerical, performance or task-accuracy acceptance.

## Authoritative baseline

- Work branch: work/qwen36-damp-ascend-20261006.
- Parent: 7b7910c3c82bea6f9046158c403147d60dff4965.
- Model: /cache/efim/Qwen3.6-27B, actual Qwen3_5 hybrid GDN.
- Frozen NPU batch cutoff: 1792710600 (2026-10-22 23:10 UTC). It is not extended here.
- Physical NPU4-7 only. No new Docker, NPU, HTTP, authority or SOURCE_BOUND action occurred in this preparation stage.

## Actual defect and repair

The short8 public host entry still called a phase/controller helper tied to the historical cutoff even though qualification validation used the current source-owned authority. A new authority alone could not fix this deterministic rejection.

fastpath_clock_seam_prepare_v1 contains an explicit, reversible 4-file successor (420 total files) of the unchanged 419-file short8 parent. It resolves the current source-owned authority at the actual phase/controller entry, preserving original main-entry monotonic time, 3600 phase, 180 cleanup, 60 creation reserve and failure gates. Historical cutoffs and failed outputs are retained.

Actual exec-00000000000009f2 exited 0 in 27.426 seconds: real source reconstruction, component readset, contract090.source and public host CLI exercised in an explicitly synthetic in-memory filesystem/authority. The entry stopped before owned helper/device access. Invalid approval, scope, expiry, binding, remaining phase/window and controller cutoff were rejected. This is not physical binding or NPU qualification. Independent read-only review confirmed this scope and retained limits.

## Long160 state/evidence preparation

fastpath_long_gate_prepare_v1 contains lossless bounded report wire, complete independent report reopening, compact state-event identity with full rows restored before original checking, original prefix continuity and complete reservation accounting. Original algorithm/math sources remain unchanged under whole-source inverse.

Actual exec-00000000000009db exited 0: 20 primitive controls and 4 actual rendered160 controls. These use synthetic data, not NPU outputs. Tested reservation is 66155552 bytes per-rank metadata (limit67108864), and 6807552 bytes four-rank combined STATE (limit10485760). A per-frame limit is NOT proof that retained first/current/failed raw data fits the joint1GiB budget.

Raw actual operation evidence:
- /opt/host/vnf/austinov/run-bole-followup-preparation-evidence-20261022T230600Z-v1/LONG160_SOFTWARE_EXECUTION.json
- WINDOW_EDGE_OBSERVATION.json in the same directory: 7491 bytes, SHA256 c9dc52142efcbb4c949107ecabcdeff6c7015fb0e2a07809db6d95aa3c5b386a. Observation epoch1792710595.4327989: all named owned model/CPU jobs stopped, npu-smi command exit0. This single snapshot does not prove full-window utilization.

## Exact next dependency

1. Genuine new execution-window authorization and MAIN source review/binding; pending, not implied by this checkpoint.
2. Actual short8 FAST mathematical/state qualification, including true worker/operator loading and durable evidence, before160 dispatch.
3.160 whole-source producer/validator integration, actual raw-size/joint-budget observation and NPU result.
4. Same-config true nativeAR/candidate fixed1024 source-bound performance screening, then3 real pairs only if promising.
5. GSM8K/HumanEval/MMLU smoke thenfull, thinkingOFF/max2048/normalEOS; report percentage points and relative change.

Parallel source preparation continues in separate scopes for strict timing/bound-source lineage and accuracy transport/decoder lineage. Prepared manifests are not SOURCE_BOUND. Formal/numerical/task acceptance remains false. The131-token prototype is not general2k/16k workload acceptance.

## Delivery limits

No remote push is claimed. Existing GitHub HTTPS authentication is unavailable; existing SSH22 timed out and SSH443 rejected the available public key. Do not reuse AWMCP verification for Git, disable host/TLS verification or force-push. Preserve the three unrelated tracked modifications outside these exact staged files.

## Source-binding successor (still no NPU acceptance)

fastpath_160_source_binding_prepare_v1 now connects the real160 producer/validator/public host prefix with the current-authority clock and a strict short8 predecessor. Actual0a34 exposed execution of caller-selected wrong old helpers before complete source verification. Its failed behavior is retained; the successor first rebuilds the entire trusted420-file short8 template, checks its exact binding transition, all file bytes and historical MAIN review, then loads the original consumers. It additionally joins the common HCCL policy and exact server source.

A second source defect was the creation renderer's future-only directory predicate when reading a completed predecessor. The successor applies one exact source-derived read-only materialized-reconstruction delta in a private namespace; frozen parent files are unchanged. Actual0a44 explicitly presents the old source/output as existing: the original creator rejects, the complete read-only reconstruction succeeds. Its17 software events also cover bad-helper rejection before execution, HCCL drift, CLI argument and module-restoration cases, full422 source reconstruction, original component/command lineage, current-clock controls and real short8-missing refusal before any device action. This is synthetic in-memory source/authority validation only, not physical binding or same-image160 execution.

Final source SHA256: f2768d3a264af4c26f8e5d3234140d02c3aa0f8815be2b60bc3cbb4a917fdf75. Check script SHA256: ce50430294213b604c9ba896d43d3a27451c0afa9a4f2accf36a29597cf5a4f1. Actual original operation responses for0a29,0a34 and0a44 are retained in SOURCE_ENTRY_CLOSURE_OPERATIONS_V2.json under the external evidence directory above (11306 bytes, SHA256313a9793c3424d45fc2f0bb6256158943a38cefa2d7e0a227d2b0a3aacba2183).

The final format-only transport decoder controls' original synchronous tool response was recovered rather than rerun after operation_get could not find0a2e. TRANSPORT_DECODER_FINAL_FORMAT_OPERATION_0a2e_V1.json in the same evidence directory is7279 bytes, SHA256d279abf5b0e3c2b38cfeb0361d454fd60410a45dd79d0824a8bb7bce25127f61. It records9 actual software controls and the final five file identities; it is not generation, CPU-owner or task-score evidence.

CURRENT remains the actual short8 mathematical/state experiment awaiting a genuinely new NPU window and MAIN source binding. NEXT160 still requires that real predecessor, actual same-image execution, NPU outputs and joint raw-budget coverage. Strict1024 paired performance and task acceptance remain false. Independent representative2048-input preparation has started because131 is only a prototype: its static private attention/page assumptions require real adaptation and new numerical coverage, not relabelling the old profile. No new NPU lease or authorization has been created.

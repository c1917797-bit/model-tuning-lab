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

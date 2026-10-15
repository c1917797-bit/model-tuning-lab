# DeltaLog NEW48H source snapshots (not a qualified release)

These are byte-exact source copies of the debug015 build and empirical016 test implementations used in the 2026-10-14/16 fixed experiment window. Generated NPU tensors, datasets, model weights and actual experiment outputs are intentionally NOT included. This directory is an audit/recovery source snapshot, not a production plugin entry point. Default execution remains OFF.

The actual remote execution roots remain under `/cache/cch/qwen36-paper-preparation-20261007/lowbit/`. Their immutable source/build/result references are recorded in the current NEW48H workstream handoff and case record. Existing source contracts deliberately reference their original frozen paths; copying these files is NOT evidence of relocation, portability, numerical qualification, model readiness or performance.

Debug015 adds an independent FP32 readout sidecar to the unchanged B010 production arithmetic. `verify_inverse.py` recovers eight original source files after erasing only the exact debug additions. Actual compilation and runtime numerical evidence are separate obligations. Empirical016 compares actual precast readouts with independent CPU64 full-history recurrence and exact BF16 RNE, with fixed per-request criteria; original013/016 failures remain historical failures.

Do not promote the diagnostic service to formal performance: its per-layer CPU metadata copies are not a production implementation. The independent audit additionally found value-equality/bitwise and native-checkpoint evidence gaps and missing redzone/pointer receipts on regression137; these require explicit supplemental evidence and are not hidden by these snapshots.

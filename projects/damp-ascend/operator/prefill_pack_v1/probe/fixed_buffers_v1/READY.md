# Fixed-address FP32 SR division gate — NEW, default dry, eager only

This four-file packet closes a specific coverage gap in the frozen float probe:
its changing fixtures previously used fresh allocations. It does NOT modify
the old compiled9/runtime15, exact helper, operator, collector, deadline or gates.

Registered execution: N64/N896 × exact/certificate, each three independently
guarded INT32 roots and their views allocated once, cold prepare exactly once,
Prepare uses seed turn19; verification turns0..19 compare ALL three fingerprints
against that seed and each prior turn, proving20 genuine changes (not19).
Each turn then has8 identical repetitions
per turn. Updates use original root.copy_ followed by actual synchronize;
both data/storage pointers, complete raw inputs and32B guards are preserved.
All4 complete guarded outputs compare bitwise to the independent Fraction
RN32 quotient golden and flags. Overflow remains signed Inf(valid1/finite0);
no clipping. Malformed fixture golden/raw bit range rejects before H2D.
Each turn's CPU before is saved first, then nullable raw output/input-after
before every assertion. Primary dispatch errors and poisoned-copy failures
remain distinct. SOURCE_BEFORE/AFTER are saved for success AND failure,
including failed source admission; no unchanged retry or overwrite.

Status is preparation only: no Torch/device execution/build/load or performance
claim. Pure stdlib tests include an explicitly labeled software lifecycle MODEL;
it is not a device/algorithm pass. Actual20/8 constants never change.
NPUGraph, selected-slot packing, recurrence, shared cache, general service,
E2E and task accuracy remain out of scope. A real graph protocol would need
cold prepare outside capture, fixed inputs/outputs, changing synchronized
updates and independent graph-feedback arenas; none is captured here.

Read runtime_manifest.json for exact old17/source3 pins. MAIN must first obtain
the real unchanged float-probe9 build/export/load receipt and immutable library;
this runner additionally checks frozen actual schema and loaded library maps.
The default CLI only emits a nonlaunchable preparation plan and creates nothing.

Software-only (host Python, no Torch/Docker/NPU):
python3 -B projects/damp-ascend/operator/prefill_pack_v1/probe/fixed_buffers_v1/test_fixed_buffers.py
python3 -B projects/damp-ascend/operator/prefill_pack_v1/probe/fixed_buffers_v1/run_fixed_buffers.py

MAIN-only future execution argv (replace required values with ACTUAL hashes;
placeholders are not admission; use a NEW output and fresh physical proof):
python3 -B projects/damp-ascend/operator/prefill_pack_v1/probe/fixed_buffers_v1/run_fixed_buffers.py
  --execute --fixed-manifest-sha256 ACTUAL_NEW_RUNTIME_MANIFEST_SHA
  --library ACTUAL_UNCHANGED_FLOAT_PROBE_SO --library-sha256 ACTUAL_SO_SHA
  --build-receipt ACTUAL_FLOAT_PROBE_BUILD_RECEIPT --build-receipt-sha256 ACTUAL_RECEIPT_SHA
  --preflight ACTUAL_FRESH_ONE_CARD_DEVICE_PROOF --preflight-sha256 ACTUAL_PROOF_SHA
  --physical-card 4 --output-dir /drrqr-results/prefill-float-fixed-buffers-v1

The frozen old manifests default to canonical repository paths and exact hashes;
mount repository/build/proof read-only and only this NEW output writable.
Logical0 must actually map to the selected authorized physical4..7.
MAIN owns fresh nonprivileged canary, resource/deadline admission and execution.
Do not launch alongside live TP4/reference/calibration or formal timing.
A successful future report must have fixed_buffers_exact_float_pass,4cases,
1prepare/case,20changed turns/case,8repeats/turn, intact source-before/after.
No numeric threshold has been relaxed. Exact bits here are not GSM8K accuracy.

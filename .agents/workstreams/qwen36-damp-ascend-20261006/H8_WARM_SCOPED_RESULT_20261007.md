# H8 warm-transition diagnostic — scoped result

Actual MAIN MA0f29 finished exit0 in 1373.049s on physical6, container logical0.
Its original whole envelope is H8_WARM_ORIGINAL_TERMINAL_20261007.json,
SHA256 2faf8bd403fcc8564e570c7fa07e711da833ef1fa92cad761754e2ea4d4116c5.
RESULT is /cache/cch/qwen36-paper-preparation-20261007/recurrent/MAIN-h8-warm-prelude-b6-20261007-001/RESULT.json,
SHA256 9e97bc1d251a15ebb27ca32bbba4962c6a735ed9c329c8b5f03c0767f716b26e.

B14 and B11 each completed eager plus three graph trials of160 steps (1280),
followed by B6 eager first step (1): nine cases,1281 steps.
The frozen source144, H8 library/build/Meta, independent native/H8 fences,
9087 immutable phase records and12 raw checkpoints were checked.
Original output .00303 and state/head2e-6 gates, all state/log/input/redzones,
pointer/storage identity remained unchanged. The raw format metadata is integer
ND, avoiding a torch_npu enum import when reading with CPU-only Torch.

Actual independent consumer MA0f5b finished exit0 in5.966s:
H8_WARM_INDEPENDENT_CONSUMER_20261007.json. It reads the original NPU result;
it performs no new NPU computation. The initial consumer MA0f50 terminal was
unavailable (operation_not_found when observed); its launch ACK alone is not a
PASS. A bounded read-only replay consumed the already persisted original;
the NPU experiment was not repeated.

This is warm-diagnostic success ONLY. Full11520, lifecycle, chunk64 mixed,
full-model64layers/48GDN, matched1024 E2E and final2048 task accuracy are unverified.
Historical fullv2 MA0e6e B6 synchronize507035 remains a failed original run.
This fenced no-sibling configuration weakens a single-shape-only explanation;
it does not establish the cause as async/concurrency or invalidate that failure.
Next source-bound full-runtime successor must independently cover its entire
matrix/lifecycle and exact cleanup before any model or performance admission.

Memory32GiB release authority is already spent; OVS and NUMA3 remain protected.
No new throughput/task result and no accepted non-HYPIC technique are claimed.

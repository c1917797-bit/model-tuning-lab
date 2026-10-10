# KIVI first-decode bootstrap v2 — retained failed source

These files are byte-exact copies of the deployed v2 packet. SOURCE_MANIFEST.json
keeps the original `/cache/cch/.../kivi-model-firstdecode-bootstrap-v1-002` paths
and hashes for audit; it is not a relocated deployment manifest. Do not run this
archive as a fresh-clone service or change the failed manifest in place.

Actual MAIN operation0226 exited1 in102.813s at the no-device CPU preflight:
`native_format_patch_chain` used `manager`/`npu`, while the unchanged original
format policy requires `patch_manager`/`npu_patches`. The six source Refs and
hashes correspond, but the exact-key contract rejects the wrong labels before
candidate arithmetic. No NPU/model/performance/task result was produced.

The original12 software tests passed but did not exercise this real interface.
A successor must add the actual binding producer/consumer regression and pass
the same-image CPU entry, then actual TP4 first-decode/raw-independent checks.
Keep numerical thresholds, physical4–7 isolation and all later gates unchanged.

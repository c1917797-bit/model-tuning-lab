# HYPIC GDN affine r4 — driver-init gate passed, operator registration absent

r4 added the six frozen successful-service driver/DCMI/npu-smi binds read-only.
Unlike r1–r3, `torch.npu.set_device(0)` succeeded and the continuous guard
observed the exact container's process on physical NPU0. This identifies the
missing host driver bundle as a required condition for the standalone probe;
it does not isolate which individual bind fixed initialization.

The first `_ascendc_gdn_h` call then failed because
`torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h` was absent. The pinned
vLLM-Ascend source defines a lazy `enable_custom_op()` bootstrap in
`vllm_ascend/utils.py` that imports `vllm_ascend_C` after device selection;
the standalone probe had not called it. No GDN residual was produced. Sixteen
guard samples had no foreign PID, and the exact owned container was released.

Immutable root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/gdn-affine-20261009-r4`.
SHA256: `terminal.json` 6bd343d1bad0c5583cfed3f4c92221f3bb6f72c982d426bedcfeb8f3d42efe6d;
`container.log` ce4f04769929db26aef5bef350d5409e7167665c6c6d215b941a24f7adc7f443;
`container-inspect.json` 23a6b95c12922b06cee7eda2735cdc2f3b0dd1af4048928503cdac5cfb32a340;
`lane-guard.json` 2646349668fb8227e4cc5230b5393c69bb321020991f8f79f3905785dca3f9bb.

r5 freezes only the official custom-op bootstrap addition in a distinct raw
root. Neither r4 nor a later microdiagnostic can revise r13's quality rejection.

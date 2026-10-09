# HYPIC GDN affine r2 — device-count hypothesis rejected

r2 mapped only physical NPU0–3 and shared management devices into the pinned
image, with `ASCEND_RT_VISIBLE_DEVICES=0`. It failed at the same
`torch.npu.set_device(0)` SoC-discovery/ACL `507008` point as r1, before any
GDN operator call. Thus four-device mapping alone did **not** resolve the
initialization error. The controller recorded 12 clean guard samples, no
owned NPU0 PID, and exact owned-container release. The immutable raw root is
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/gdn-affine-20261009-r2`.

SHA256: `terminal.json` 61a602ac1121ba58f5a6efd33cef85e784da1e1cc289a782b6af6970d2ba19ce;
`container.log` 7e9908a0330597bdeaf915ea3e52cb42354c12c079ea985be1fd6d73bd6140c7;
`container-inspect.json` 78c9c882eebac1cf6dc7d27c0eaa9581b13228ffb5d1a1acbb3ec5a0d189e6ab;
`lane-guard.json` 1d4e5c74518a615250f118fe36661f5cf083d40381309624a200df53578459b4.

The next frozen r3 tests only the remaining visible-device setting difference
against the successful four-worker recipe. It does not change the r13 quality
decision, and no current GDN parity result exists.

# HYPIC GDN affine r3 — visible-device hypothesis rejected

r3 retained physical NPU0–3 mapping and changed only
`ASCEND_RT_VISIBLE_DEVICES` from `0` to `0,1,2,3`, matching the frozen
successful HYPIC service. It failed at the same `torch.npu.set_device(0)`
SoC-discovery/ACL `507008` point before any GDN operator. Device visibility
alone is insufficient. Twelve continuous guard samples were clean, no owned
physical NPU0 process appeared, and the exact container was released.
Immutable root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/gdn-affine-20261009-r3`.

SHA256: `terminal.json` 244f3d85b5881104d92e2404494b5ecff3d454bb8392e7d61f2af0dd3b3336ee;
`container.log` 45fe527e4381afbcda9a5fc122d682e675dff3b4f5f3485f3816debc2101f1ff;
`container-inspect.json` 738731becf273961fb06aa6e562e0ce2b77582f1261a5dd0f3fb8e692e7de536;
`lane-guard.json` db9faef610a09a4f63a0480f0bb19c3828e9c66d0badf2a95c88a85888d20d37.

The frozen successful service also mounted host driver libraries, version,
DCMI and npu-smi files, absent in r1–r3. r4 tests that bundle as read-only
binds while preserving the same device mapping, visibility and network mode.
No GDN parity or HYPIC quality conclusion is available from r3.

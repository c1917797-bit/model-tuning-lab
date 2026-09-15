# DASC physical checkpoint design decision

Date: 2026-09-15

## Evidence-driven constraint

The W64 activation canary emitted 192 restore events: 48 GDN layers on each
of four TP ranks. Every local temporal state has 12 heads. Retained counts
range from 2 to 12 and sum to 1,728 across 192 rank-layer instances, exactly
9 retained heads on average (75%). The temporal checkpoint payload therefore
has a theoretical mean compression ratio of 1.3333x before conv-state and
allocator alignment overhead.

The distribution is heterogeneous: 29 of 192 rank-layer instances retain all
12 heads, while others retain as few as 2. Padding every layer to the maximum
retained count would erase all savings. Physical storage must therefore use
per-layer offsets in one arena (or size-homogeneous groups), not one uniform
12-head Mamba page.

## Runtime boundary

The native Ascend GDN operator consumes a dense fixed-head state and indexes
it with the state indices produced by the Mamba metadata builder. Existing
vLLM-Ascend allocation also aligns attention pages to the full SSM page and
reshapes each Mamba tensor using the original dense shapes. Changing only
MambaSpec.page_size_bytes is unsafe: the runner would advertise smaller pages
while constructing dense views.

The selected design is therefore:

1. persistent prefix checkpoints: compact retained-head storage, heterogeneous
   per layer and indexed by scheduler block id;
2. active recurrent state: dense fixed-shape workspace indexed by active
   request slot, preserving the native operator ABI;
3. lifecycle bridge: restore compact checkpoint into a zero-filled dense slot
   before model execution, then pack the updated retained heads when a block
   becomes cacheable;
4. scheduler accounting: advertise the compact physical bytes only after the
   runner allocation, views, metadata indices, invalidation, and save/restore
   paths all use the new representation.

## Rejected shortcuts

- Zeroing omitted heads in the existing dense cache: numerically reachable but
  no physical saving; measured prefix-reuse latency regressed 5.0949%.
- Shrinking only the cache specification: allocation/view mismatch.
- Uniformly padding all compact layers to 12 heads: no capacity gain because
  at least one rank-layer retains 12 heads.
- Treating the standalone pack/unpack test as an end-to-end result: it proves
  only primitive semantics.

## Gates before performance claims

- bitwise retained-head round trip and zero omitted heads on NPU;
- fixed storage pointers and valid-block/invalidation checks;
- all 48 layers and four ranks checkpoint and restore on real prefix reuse;
- measured physical bytes and admitted scheduler blocks match the compact
  geometry;
- common-config dense control, warmup excluded, repeated steady-state A/B;
- only then E2E GSM8K quality with no more than one percentage-point loss.

The plugin now contains CompactCheckpointLayout, pack/unpack primitives,
compact and full fixed-address arenas, and an atomic ActiveStateBridge. The
bridge synchronizes temporal and convolution restore/checkpoint, prefix block
copy, validity propagation, abort, and invalidation. The v0.23 container suite
passes 21 tests. This is CPU tensor/lifecycle evidence; the bridge is not yet
connected to scheduler allocation or live GDN execution.

## NPU lifecycle attempt

A bounded single-process validation mapped physical NPU4 to container device 0
and attempted to allocate its first NPU tensor. It terminated before any DASC
operation or assertion because `aclInit` returned `507899 Resource_Busy`
(AWMCP operation `exec-0000000000000f5b`). It was not retried and no broader
device claim was made. The NPU lifecycle gate therefore remains open.

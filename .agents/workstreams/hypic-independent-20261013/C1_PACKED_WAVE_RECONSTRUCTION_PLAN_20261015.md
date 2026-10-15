# Independent C1 packed wave reconstruction — source plan

## Scope and provenance
Read-only comparison authorized by human. Original3ad0967 and4429e35
GDN/attention/material code is unchanged between those commits (gitdiff lists
only context/runner/position-independent proof/tests). The human confirms the
successful route also ran on910B; do NOT blame a910C attachment/environment.
No old source is copied, imported, mounted or executed in the new runtime.

New implementation derives from affine recurrence H_after=T_segment@H_before+S.
Current implementation runs prefix and suffix serially perrequest. The reference
organizes live spans as packed variable-length sequences with reusable algebra
and batched state propagation. This is the next CORE architectural hypothesis;
R8 synchronization-only stays default-off and not device-admitted.

## Three-stage pure-state execution interface
1. Build immutable ownership-validated live-window jobs for the entire layer:
   request/rank/step, private state slot, original compact offsets. A private
   chain contains live prefix/seam, cached body map, optional live suffix.
   Native rows have no cached map; native1 remains separately batched by R7.
2. Prepare each live window once in a packed backend. Derive all live affine
   maps together, then walk dependency depth across requests with batched
   T@H+S. Record the incoming state for EVERY live window; cached transitions
   and zero-state insertions remain in prompt order.
3. Run packed live outputs from those seeds. Return private output/finalSSM/
   convtails; use existing all-request validation before real slots commit.

The official backend should reuse cumulative gate/WY for state-only zero and
identity passes plus seeded output, rather than invoking the full chunk wrapper
perrequest/window. Metadata/layout caches and material leases are bound to
exact geometry/source/device/generation; no cross-request cache aliasing.

## Gates
CPU exact FP64 serial recurrence, unequal key/value dimensions, mixed live and
cached rows, ragged lengths, no-suffix and shared material, reset initial-state,
request/slot identity and negative ordering controls. Count packed preparation/
map/output callbacks to falsify accidental per-window complete dispatch.
This is real execution-core implementation, not a scheduler-only claim.

Then inspect current official image primitives/API and implement own backend,
defaultoff integration; compare against own serialized C1 from same private
inputs on all48layers/fourranks. No new NPU until independent audit/package/
physical0-3/port/newroot and measured critical-path opportunity gates pass.
Current native profile supplies missing control attribution; raw parsers run CPU
only. Service wins require fresh paired full40/1024 and all G1-G4x3, quality and
rollback requirements unchanged. Deadline2026-10-15T19:04:09Z, not extended.

# Material-lineage observer: host-tested implementation, not device proof

2026-10-12, exact HYPIC source4429e35177979c874bf053ab29789e4773f39b22.
New files: material_lineage_observer.py, material_lineage_audit.py,
test_material_lineage_observer.py. No frozen r19/r22/r25 source or raw root changed.

## Implementation and verified scope

Default-disabled install returns without reading/mutating the store. Enabled
install hashes the real material.py and refuses existing instance patches or
a preexisting target material. Only one explicit segment and two selected layers
are observed. Wrapped put methods preserve returns and the original policy,
record actual stored objects/tensors, and distinguish duplicate retention from
new generations. Generation weak references do not keep evicted device tensors
alive. Snapshots are owned CPU samples, bounded to four generations/24 events;
uninstall restores inherited methods, clears snapshots/callbacks, and leaves
saved wrapper aliases inert.

A consumer must supply the actual material object, selected layer, exact target
request (or its single eight-hex runtime suffix) and one step. The independent
auditor checks event identity, rank/PID, generation/component sequencing,
sampling coordinates and same-request/step joins, then recomputes equality from
raw sampled values rather than trusting the observer's pass flags. It reports
whether a consumption used the latest observed generation; this is not by itself
a causal quality or semantic-equivalence decision.

Shared py311 execution exec-0000000000000041 exited0:14 tests, including actual
store duplicate/recreate behavior, mutation detection, disabled mode, alias-safe
uninstall, unchanged LRU timestamp, wrong request/step/rank/coordinates and
forged-pass-flag negative controls. Input tensors are tiny synthetic CPU tensors.
No NPU session or real material-generation capture exists for this module yet.
The initial11-test pass003e preceded request/step binding and independent audit.

## Exact remaining integration seam

Producer side must install before warmups; resolve actual TP rank on first
selected producer call after runtime initialization. The producer context must
identify materialization requests and step, not every request in the batch.
Write events need an exclusive raw writer started at that first producer; late
creation at the target hot request would lose provenance.

Consumer side must pass the material actually held by the production function:
- attention.py _repair_position_independent_kv, immediately after
  materials[seg_hash] = material (line1007 in the pinned source);
- gdn.py _position_independent_gdn_core, after
  material = MATERIAL_CACHE.get(seg_hash) (line887), for selected layer/hash.

Do not make an unrelated diagnostic get() call: it updates LRU and could read a
different object. Do not assume every read in a multi-request batch belongs to
the target: join the selected request plan's actual entry/hash.

The existing numerical_state_observer_v2 compiles functions from original file
text. Two independent source-recompiling hooks on these same functions would
overwrite one another. The next version must combine the lineage consume seams
with existing replay snapshots in one AST transformation and one uninstall
owner, leaving frozen v2/v3-package bytes intact. Test the combined function
before packaging; do not silently stack wrappers or rerun unchanged serial
lifecycle tests. No device launch is admitted by this host-only note.

After source-bound integration and a frozen bounded concurrency schedule, inspect
physical0-3/8223 freshly, run one isolated integrated diagnostic and audit actual
four-worker producer/consumer/hot receipts. NPU4-7/foreign jobs remain untouched.
No further unchanged full-quality wave, no standalone GDN, no post-hoc r19 change.
29 Skill status remains7 bounded verified/22 partial; main/remote unsynchronized.

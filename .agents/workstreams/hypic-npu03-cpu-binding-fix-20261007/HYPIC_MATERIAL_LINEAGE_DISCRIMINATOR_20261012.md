# HYPIC material lineage discriminator: exact-source CPU evidence

2026-10-12; diagnostic groundwork only. No NPU run, quality reclassification,
cache-policy change or runtime source edit.

## Reproducible result

Run from this worktree:
`/cache/cch/python-envs/model-tuning-lab-py311/bin/python -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/probe_material_lineage_cpu.py`

Execution exec-0000000000000037 exited0 in2.539 seconds, five checks passed.
It imports the real MaterializedSegmentStore from clean HYPIC commit
4429e35177979c874bf053ab29789e4773f39b22; material.py SHA256
cd677063af4e296be00d12ae9f148fc384cdf4f29b376170f89cd56eb5cf6f68.
Tiny synthetic CPU tensors, CPU storage and a stubbed free-device-memory
query isolate store semantics; there is no accelerator or serving proof.
The expected capacity rejection warning is the negative control, not test failure.

1. Stored CPU K/V/S/T/conv tensors own their bytes; mutating producer inputs
   does not mutate stored values.
2. A duplicate same-hash/layer put returns True and finish_step reports ready,
   while retaining the old object and old payload even if attempted input
   values differ. Therefore put=True or ready_hash is not a new generation.
3. An active replay hash passed in protected_hashes cannot be evicted by a
   competing segment at the one-segment limit; the new material is rejected.
4. Eviction removes the mapping but does not mutate a still-retained object.
5. Rematerialization after eviction can use the same segment hash with a new
   object and new numerical payload. Hash equality is not generation equality.

These are implementation semantics, NOT evidence that stale material caused
r19 quality loss. Duplicate reuse is intentional, not automatically a defect.

## Exact source seams and narrowed next action

- material.py begin_step / put_full_kv / put_gdn_state / finish_step / remove /
  _get_or_create: observe committed storage, not merely attempted inputs.
- runner.py execute wrapper calls begin_step with ctx.replay_hashes protected
  before original_execute and publishes finish_step afterward. The CPU probe
  plus source weakens an unqualified claim that ordinary in-forward LRU eviction
  itself mutates active tensors. Device scheduling/lifetime remains unproven.
- attention.py _store_position_independent_kv stores canonical selected rows.
  _repair_position_independent_kv consumes the actual material object.
- gdn.py _position_independent_gdn_core consumes conv/S/T by segment hash and
  persists cold zero-start state/transition through put_gdn_state.

The smallest useful successor is a bounded producer-to-consumer lineage capture
for sample059 in the HYPIC integrated path, reusing the now device-proven
observer-v2 lifecycle. It must start before warmup, distinguish actual insertion
from retained duplicate put, and associate each selected component with the
object generation that actually supplied its stored tensor. At hot consumption,
join actual material object, selected payload, request/rank/layer/step and the
existing independently checked slot/position replay. Never derive generation
from a ready event or use a production result as independent regeneration.

Negative controls before device admission: duplicate put with different input
must remain the old generation; same-hash delete/recreate must change generation;
mutating sampled stored values must be detected; wrong request/rank/layer/step
must not join. Observe only selected coordinates and disclose that limitation.

If storage identity and sampled replay are intact under concurrency, do not
keep repeating cache-generation diagnostics: investigate how the cold material
was computed and the native-versus-PIC semantic/context or decode difference.
A diagnostic result cannot change the frozen r19 decision or replace the final
matched full-quality/performance acceptance.

No new c32/full-quality run is admitted by this document. Freeze the exact
bounded request schedule and source-bound adapter after these distinctions work.
Do not rerun the completed serial lifecycle or unrelated standalone GDN tests.
Only physical0-3, fresh direct route/process/port checks, continuous guard and
exact owned cleanup; no changes to foreign tasks or NPU4-7.


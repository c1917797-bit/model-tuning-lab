# Actual new-helper callee contracts

| Actual caller | Actual argument | Used API | v10 treatment |
| --- | --- | --- | --- |
| `owned_create.create → parent_alias` | original025 `model_contract` as `c` | `c.obj` exists; `require` exists; `need` does not exist | parameter is named `c`; reads remain actual `c.obj`; alias assertion uses the helper's unshadowed, source-bound global `sourceio C.need` |
| `host_service → phase_admission` | `contract090 C` | `CUT`, `need` | unchanged; `contract090` imports exact original sourceio `need` |
| `host_service → controller_admission` | `contract090 C`, original025 `c`, derived safety `S`, actual controller | `C.need`; `c.CUTOFF`; `S.PHASE/CLEANUP`; actual `remaining` | unchanged; actual v9 passed this seam before the later proven helper error |
| `host_service → stage_saved_probe/ChannelWriter` | `contract090 C` | `need/ref/checked/obj/write` | unchanged; this argument is contract090, not original025 `c` |
| cold creator snapshot exclusion | explicit `import sourceio as C` | `need/ref/checked/obj` | unchanged; no original025 parameter is treated as sourceio |
| `service_entry → g2_cold_parent_output.run` | only exact source Ref | helper module's own sourceio `C` | unchanged; no caller facade injection |

There is no `getattr` compatibility dispatch, fake `need` added to original025, assertion bypass, relaxed Ref, or Docker call in local interface controls. The exact original025 whole module is loaded from its declared actual Ref (or the independently byte-verified local copy during local preparation). Its real `obj`, `sha`, `IMAGE` and absence of `need` are exercised. The unchanged real creator reaches the first `unique-name` Docker boundary with a valid alias and is deliberately stopped before that call executes. Illegal aliases, exact/descendant immutable-input conflicts and wrong source SHA fail before that boundary.

The v9 control fallback had a separate concrete source-read dependency: actual SOURCE.files lacked `safety_host.py`. The original18 test file's fallback reads that key when no local review tree exists. v10 preserves the entire test file. It adds an exact byteequal source-only snapshot from original `owned_substrate.REFS['safety_host']`, records both full Refs, and includes the snapshot in SOURCE.files/readset. The original owner still loads the original025 Ref through unchanged `owned_substrate`; no controller imports this snapshot. A new control executes the unchanged original18 fallback in a fresh source layout with no local review branch, and the assembled-source audit rechecks the actual original/snapshot/readset join.

# 023 real Qwen service bridge — code prepared, actual model gates pending

This is a NEW source, not017 with changed environment. No017/018/021 edits.
No new resource/owner/controller, no remote/container/NPU/Git operation.

## Implemented real execution wiring

* Preserve source-pinned017 binding.py/contract/layout/helpers/transform exactly.
  B.resolve follows actual copied Qwen target/MRO, not only Ascend class patch.
* Production DSO stays B0102332672/298749129c8586ecea56cb6076c435631b6fbef4b4e7757636ff87a4ec09abf7,
  seven-entry state-log ABI unchanged. Actual _OP call AST equals017.
* primitives.py is EXACT audited0211b9a2e53...: mask deadU/K BEFORE contraction,
  reject nonfinite selected logical state BEFORE mutation. Diagnostic .item()
  synchronization remains explicit; this is NOT formal timing implementation.
* CPU metadata018-rev2 source adapted only for package-relative import, pure
  prefill nd0 reader sequenceNone, and rejecting overlapping registered layer
  arenas. Pure-prefill still consumes real zero-length decode view and all48 core
  readers; mixed/decode uses actual native nonNone sequence object.
* integration wraps actual runner._prepare_inputs BEFORE original preparation:
  enumerate native Mamba KVgroup layer_names, fetch actual objects from actual
  compilation_config.static_forward_context, require actual source-resolved Qwen
  type and real48 names/arenas. No invented mapping or future model receipt.
* Real _model_forward runs inside runner's existing actual forward context. On
  successful return, finish_step enforces all48 core/decode phase readers even
  on final step. Missing/duplicate readers fail before successful model return.
* Runtime algorithm and route consume CPU receipts rather than device tolist.
  Actual state/index views, shape/dtype/native scale, MRO/context, prefix/state,
  request generation, epoch/group and arena/source checks remain. Native conv,
  gating, normalization and prefill are NOT replaced. Only recurrent call seam
  changes to originalB010. No fallback is allowed with live deferred state.
* Startup-only dummy remains native and unannotated; live dummy rejected BEFORE
  native writes and invalidates epoch/current. MetadataNone is native only before
  live logs. PDC/copy is forbidden, graph/spec/async/PCP>1 forbidden.

##022 interface, no heavy raw replay in workers

admission.consume loads exact022 composite_api_ref, calls its lightweight
admit_receipt(composite_source_ref, composite_cpu_owner_ref). Never calls heavy
022 consume in a worker. It checks exact stored certificateRef/ownerRef, all
strict flags and dict strict137_join.actual_tensor_join, old019 FALSE unchanged,
all model/performance/task/PDC/graph flags FALSE. Production build Ref remains
separate, tied to actual016 component source, kernel manifest and actualB010 DSO.
Missing actual022 source/API/certificate/CPUowner is a blocker, not READY.

Template+one-shot binder only. SOURCE_MANIFEST.json absent until actual022 refs
are supplied and lightweight admission succeeds. Failed binder candidate remains
immutable, no automatic retry/overwrite. No model qualification is implied by
the component certificate or successful binder.

## Commands and activation boundary

Local CPU: python -B -m unittest test_wiring.py test_admission_contract.py
Cold: python -I -B entry.py (defaultOFF; no torch/backend import)
Sources: python -I -B verify_sources.py --old-root <actual017/package-dir>

Explicit worker environment for a future MAIN-owned bridge ONLY:
QWEN36_DELTALOG_SERVICE023_ENABLE=1
QWEN36_DELTALOG_SERVICE023_MODE=diagnostic-bridge-only
QWEN36_DELTALOG_SERVICE023_SOURCE_REF=<actual bound023 Ref JSON>
QWEN36_DELTALOG_SERVICE023_COMPOSITE_SOURCE_REF=<actual022 Ref JSON>
QWEN36_DELTALOG_SERVICE023_AUDIT=<MAIN-exclusive writable audit root>
QWEN36_DELTALOG_CPU_MIRROR018_REV2_ENABLE=1
Put this new root FIRST on PYTHONPATH; preserve actual platform/worker plugins
but whitelist qwen36_deltalog_service023, NOT oldservice003. Never run both entry
points against same package in one process. Restart clean for rollback; ENV OFF
does not uninstall already-patched methods.

## Test scope and remaining real gates

Eight CPU tests use the actual register/reader/finish/wiring functions. The Arena
fixture wraps CPU storage with an explicitly fake NPU device LABEL solely to
exercise registration guards; it is NOT NPU or worker evidence. One early fixture
lacked epoch and was corrected, not an actual kernel failure. Tests cover real
mapping enumeration/overlap rejection, pureprefill→decode/mixed, skipped prefill,
wrong None sequence, terminal forward completion, duplicate forward, runtime D2H
absence and component-not-model admission negatives. Source inverse and cold
isolatedOFF pass. No mock replaces register/reader/finish critical logic.

Still required: actual022 certificate owned CPU success; sameimage plugin
discovery/receiver source and CLI; new MAIN-owned real4x48 model tiny forward;
actual scheduler CPU→device join and all48 final finish receipts; real NPU native
prefill/mixed/flush/reuse/inactive-slot independent numerical bridge including021
dead-payload cases. Then model multi-step qualification, paired1024 performance,
and task accuracy. No component/fixture is substituted for these gates.

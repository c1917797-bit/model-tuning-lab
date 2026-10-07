# KVBuffer numerical diagnostics: scoped lessons

Read this when a deferred-state GDN migration fails a native Ascend numerical
gate or when adding an observation kernel. Concrete records are in the current
workstream's KVBUFFER_COPY_ONLY_TRACE_20261007.md; these lessons do not authorize
system pool changes, outside workload termination or a relaxed acceptance gate.

- First distinguish the rejected quantity. The current B16 graph trial0/step37
  has three differing active BF16 outputs (maximum one ULP), while recurrent
  state passes its separate tolerance. Small rounding differences are a
  diagnostic lead, not task-quality equivalence or permission to raise the
  original output limit. A user-allowed task accuracy loss is not a tensor limit.
- An original operation can fail an ownership predicate even when a real child
  result is valid. Retain both records and independently validate the child;
  do not relabel the parent. A canary abort before dispatch provides no candidate
  numerical evidence. Preserve actual SMI rows and PID/starttime/cgroup before
  ownership predicates; this case's outside profiling PID was on physical5,
  not physical4. Device declarations alone do not prove active occupation.
- For a non-timing numerical probe, scope the lease to the actual required card
  and independently retain other-card observations. This does not authorize
  overlapping TP4/model/profiling or comparative timing. Keep physical mapping,
  exact own CID/argv, ordinary RAM reserve and cleanup predicates intact.
  A protected-card process change must be attributed, not asserted to have been
  caused by the candidate. This implementation still aborts on that change.
- Actual public native Q/K/V/beta/output ABI is BF16 in the pinned v0.23/CANN9.1
  implementation. FP32 state and gate support do not create an FP32 output path.
  API definitions, validation, tiling, adapter and kernel template agree; do not
  spend a scarce-card run on a known illegal dtype or call a Torch dot product
  the native precast value.
- A source-derived trace is a different implementation until anchored. Copy
  actual UB data without feeding it back into arithmetic. First require complete
  candidate state, all candidate output rows, original inputs, guards and pointers
  to match the frozen production binary in eager and graph. Undefined native
  padding is not gold, but candidate inactive output must remain valid. Save
  raw/primary errors before assertions. Trace failure is instrumentation evidence,
  not automatically a paper-wide rejection.
- Source arithmetic equality is weaker than compiler/device equality. Real
  CANN compile/export/dlopen/schema/Meta is a prerequisite, not numerical or
  performance authority. C++ aggregate byte-count narrowing failed the first
  trace build; an independent successor makes its bounded conversion explicit
  and retains the original log. Do not rewrite pinned manifests/results.
- Bind actual producer and consumer receipt formats before reserving devices.
  Check original command bytes/exits, defined kernel export, real loaded library
  path/hash, source closure and every Meta rejection; do not fabricate a legacy
  PASS wrapper around a new schema. Bound captured telemetry so a truncated
  JSON dump is not mistaken for a complete consumer receipt.
- Host memory has separate ordinary, HugeTLB, anonymous and file-cache ledgers.
  Pool-free hugepages are not ordinary available RAM; stopped containers do not
  retain process RSS. Deleting them mostly frees disk. Recheck actual cgroup
  usage and ordinary MemAvailable before each launch; do not recycle an old
  ~80GiB snapshot after an outside model starts.

- A parent monitor abort can race an already completed device child. Inspect
  original child exit/argv/PID proofs, stdout-bound final Ref and raw tensors
  before rerunning. Here both eager and graph copy-only traces completed and
  independently anchored the production bytes despite parent protection failure.
  Preserve parent1 and child0 separately. Revalidate an archived identity at its
  actual original observation time; it is never fresh launch authorization.
  An independent no-device CPU reader may audit retained real-NPU tensors, but
  cannot replace device computation or establish a full numerical matrix.
- An observed candidate precast exactly at a BF16 midpoint, with the native
  output one ULP away, is a concrete arithmetic diagnostic—not proof of the
  native precast or a universal rounding-bias fix. Both modes agreeing weakens
  a graph-only hypothesis at that point; use an independently anchored native
  observation to distinguish history/state drift from readout-order effects.

- Evidence from a native incoming-state intervention can justify a new bounded
  materialization-horizon experiment instead of a readout bias or tolerance
  increase. H8 retained storage16 and native current-step order; its B16
  eager+three graph trials passed640 steps under the original limits. This
  verifies only that candidate/geometry; full batches, cache lifecycle, model
  integration and paired task/performance gates remain separate. See the
  workstream H8_MATERIALIZATION_ATTEMPT_20261007.md and MA0db7/0dd3.
- A materialization-boundary consumer must derive flush replay from the actual
  horizon, not storage capacity: length7 for H8 versus15 for H16. A source-only
  observer error should be repaired in a new frozen observer without rewriting
  old results or spending a device run on a known incompatible predicate.
- Compare original protected identities, not mutable RSS/HBM. Here a true new
  physical1 foreign Python process caused the first H8 canary abort, while the
  four original workers remained unchanged. Re-admit only after an independently
  observed external-state change; do not relax the watcher or stop outside jobs.
- For a claimed CPU-FP64 oracle on a device without native double support, move
  tensors to CPU before converting and verify the actual dtype/backend. A
  double-before-CPU expression plus a device cast warning is an oracle-boundary
  concern, not evidence of FP64 arithmetic. DeltaLog v6's B1 step69 state failure
  needs attribution; the warning alone does not prove its cause. Retain first
  raw pre/post state and inputs so a numerical failure is not only a summary row.

None of these lessons establishes an end-to-end speedup. Once the relevant
NPU gates pass, continue the actual lifecycle/mixed/capture integration, paired
dense performance, and final task tests under the unchanged experiment contract.

- An asynchronous native/candidate pair followed by one failing synchronization
  cannot identify the faulting operator. In H8 fullv2, physical6 B6 returned
  vector-core507035 after both dispatches; earlier B16 PASS does not exclude a
  shape/lifetime bug. Preserve the first exception, persist actual CPU raw pre
  before dispatch, and isolate native/candidate fences or processes in a new
  diagnostic. A runtime exception is not a tensor/task tolerance failure.
  Aborted sibling reports may retain running flags after exact owned stop:
  verify actual CID/process cleanup instead of treating stale report status as
  a live lease. See H8_FULL_V2_RUNTIME_FAILURE_20261007.md.

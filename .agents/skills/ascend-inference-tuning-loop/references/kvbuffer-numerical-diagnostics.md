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

None of these lessons establishes an end-to-end speedup. Once the relevant
NPU gates pass, continue the actual lifecycle/mixed/capture integration, paired
dense performance, and final task tests under the unchanged experiment contract.

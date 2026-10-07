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
- A guarded view's backing tensor may contain both sentinels and the writable
  state payload. Compare only the source-defined redzones for unchanged guard
  bytes, and separately prove payload/view alignment, storage offsets, pointer
  relations and state parity. Test legal payload mutations plus corruption of
  either redzone. H8 B6 diagnostic v1 compared the entire backing tensor and
  falsely rejected legitimate writes. Retain that actual failed operation;
  reanalyze its immutable real-NPU snapshots with a source-bound CPU-only reader
  before spending another device run. A corrected one-step reader is not a
  full-matrix or historical warm-transition PASS. Numerical limits stay fixed.
  See H8_B6_COMPARATOR_FAILURE_20261007.md.
- Distinguish framework wrapper keywords from lower native binding keywords.
  The pinned Ascend BaseDeviceAdaptor accepts slot_mapping but explicitly calls
  _npu_reshape_and_cache with slot_indices. SparQ v4's actual no-device preflight
  rejected its own incorrectly expected name, not the paper/native capability.
  Bind both signatures and the exact source-proven mapping; preserve actual
  dispatcher/signature/doc evidence before rejecting. Fix a new frozen adapter
  observer with positive and negative source tests, not by deleting a gate or
  unioning incompatible overloads. Same-image CPU software/source checks do not
  replace the actual CPU ABI or later NPU numerical/model/performance gates.
  See SPARQ_V4_CPU_ABI_FAILURE_20261007.md.

- Byte-exact reuse of a historical proof module does not prove compatibility
  with a renamed successor controller. Before reserving cards, pass the actual
  host-generated owner/inspect and complete CPU child argv through the real
  cross-module validator. SparQ v5-002 retained a v4 owner predicate and omitted
  the new host-output-root argv despite69 stdlib tests. MAIN caught both before
  device admission. Correct the new source-bound protocol in an independent
  successor; do not union old/new identities or call this an algorithm failure.
  See SPARQ_V5_PRE_CARD_REVIEW_20261007.md. Fixture tests and immutable hashes
  remain useful, but neither establishes deployed cross-stage closure.

- A bounded warm prelude with separately fenced operators can verify a specific
  history transition without proving a full runtime matrix. H8's1280+1 actual
  steps and independent whole-original consumer passed; full11520/lifecycle and
  model remain pending. Preserve the older asynchronous failure and avoid naming
  its root cause from a successful configuration with several changed controls.
  Save original operation terminals immediately; an expired observer handle is
  not a failed NPU computation. Replay only a read-only immutable-result consumer,
  never blindly restart the device workload.
- Preparation tests must execute from the canonical delivery path as well as a
  cache-private packet. In SparQv6-001, a fixture derived its output from source
  parent; private-cache tests passed while canonical /opt execution correctly
  rejected five fixtures against the unchanged /cache output rule. Fix test
  placement independently and retain the failure. Do not relax runtime ownership,
  canonical roots or source/argv checks to make a fixture pass.

- Separate per-Python virtual-address limits from the summed concurrent host/CLI
  memory ledger. H8 full-v3 actually reached262624KiB with four live Docker CLI
  clients; a256MiB aggregate limit aborted a validly dispatched experiment.
  Single-child/mocked software PASS cannot prove four-child resource capacity.
  Pre-register the whole parallel budget, validate actual child RSS and ordinary
  RAM together, and preserve the resource abort as infrastructure evidence—not
  a numerical failure or paper-wide no-go.
- Safety aborts must leave a bounded, exact-owner cleanup lane available.
  A latched RSS peak must not reject inspect/stop results before ownership can
  be validated. Retain the primary resource error and all secondary errors,
  revalidate full CID/source/labels/image/devices/mounts, then stop/retain only
  exact owned jobs within the original cleanup/lease limits. This is not
  permission for foreign stops or relaxed algorithm gates. Persist a successful
  create CID before any later resource rejection.
- Recovery actions and final observer checks are separate evidence. MAIN's
  four exact H8 stops succeeded, but its final optional call to nonexistent
  F.compute made the recovery parent exit1. Preserve that original; use actual
  source-defined helpers in a separate read-only verification. Do not repeat
  mutation, rewrite old cleanup, or relabel the failed parent. Later child writes
  may stale earlier partial refs; record that fact rather than updating old
  refs to manufacture PASS. See H8_FULL_V3_CONTROLLER_FAILURE_20261007.md.

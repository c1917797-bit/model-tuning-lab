# Controller observation and quiescent result references

Apply when a long NPU validation uses an RSS/process observer and mutable
child reports. This is a controller reliability lesson, not a numerical
tolerance or permission to repeat an unchanged failed experiment.

## Process lifetime is not resource overrun

Distinguish sampled RSS over-budget, a live unreadable sample, and an owned
descendant departing during a /proc read. Retain PID/start identity, failure
operation/errno and raw diagnostic. Do not interpret an observer exception as
an algorithm failure or infer memory pressure from idle NPU cards.

A proposed ESRCH/ENOENT handling change must verify the specific descendant
has departed and distinguish PID reuse, live unreadability and permission
failures. Do not suppress all OSError or silently weaken aggregate budgeting.
Use real short-lived-process competition and live-unreadable negative tests;
mock-only tests are not enough to establish the runtime fix. Preserve finite
budgets and record excluded departed samples rather than inventing zero RSS
for a live process. Sampling is not proof of unobserved peak memory.

## Reference only quiescent artifacts

On failure, first preserve the primary error, stop only exact owned resources
under the cleanup budget, and reap their CLI processes. Then snapshot final
report/journal/raw-file Refs after writers are quiescent. A stopped process's
last report can legitimately retain status running: do not edit it to passed
or fabricate a completed child. On success, require natural child completion
and the declared coverage before freezing result references.

If an original RESULT points to hashes taken before cleanup and they drift,
preserve its bytes and the strict consumer failure. A new independent bounded
read may record stable partial diagnostics, but it does not repair the original
authority or admit the missing full matrix/model/E2E stage. Never overwrite old
Refs to manufacture PASS.

## Scoped evidence and next loop

The Oct7 H8-v6 run ended on one retained ProcessLookupError with sampled peak
226048KiB below524288KiB; exact syscall/PID was not recorded. Four reports
advanced during cleanup, causing strict Ref bytes drift. Its 2189 checked steps
and12 complete cases were partial, not the required11520/lifecycle success.
This supports a narrowly tested observer/quiescent-snapshot successor, not a
paper-wide no-go or unchanged rerun. Keep frozen mathematical sources and
cutoffs, and prepare independent next paper gates while the controller is fixed.

Case authority:
[H8 v6 actual failure](../../../workstreams/qwen36-damp-ascend-20261006/H8_V6_ACTUAL_CONTROLLER_FAILURE_20261007.md).


## Complete publication before cross-process consumption

KIVI's exists-only consumer observed a partially streamed final JSON and failed;
a later complete producer file did not repair the original failed run.
For such shared completion artifacts, publish a fully written, flushed/fsynced
exclusive staging file with an atomic no-overwrite final link and directory
fsync, or an equivalent explicitly tested mechanism. The final pathname must
not signal completion while bytes are still being written. Preserve staging/
primary errors and charge retained artifacts to the disk budget. Real paused
writer tests and the full same-image CPU packing/readout proved this repair;
the repair does not grant NPU/model acceptance.

## Validate unordered inspect collections semantically

Docker inspect Mounts order changed between two observations of the same
stopped owned guest, while every mapping and all other ownership/state fields
were identical. Reject duplicate destinations, then compare all mount fields
by unique destination rather than list position. Do not ignore RW/source/type/
propagation differences. Retain the original failed controller terminal;
independently rehash valid copied child sources without repeating Docker work.
Actual evidence: [Oct8 selector and CPU stages](../../../workstreams/qwen36-damp-ascend-20261006/SELECTOR_OBSERVATION_AND_KIVI_CPU_20261008.md).

## Protected accelerator boundaries are not immutable external PID sets

On a shared host, "do not interfere with protected cards" does not mean
independent users cannot start, stop or restart their own workloads. Record
original snapshots and external churn; reject our exact PID/CID on protected
cards and actual conflicting use of authorized cards. Keep process identity,
raw SMI, mapping/FD, resource and own-only cleanup checks. Do not fabricate
unchanged snapshots or suppress genuine overlap. Shared CPU/RAM/IO changes
remain resource and formal performance-comparability considerations.

KIVI1271 was interrupted by external0–3 additions despite a physical5-only
owned guest. Actual read-only recovery proved it stopped and4–7 released;
the same equality also caused a secondary cleanup report error. Preserve the
failed controller/partial matrix, not a paper-wide negative result.
The source-bound SparQ successor and complete consumer implement the real
boundary; all145 canonical tests passed after two obsolete fixture assertions
were correctly replaced. This software result is not a numerical PASS.
See [actual correction and next gate](../../../workstreams/qwen36-damp-ascend-20261006/PROTECTED_CARD_OBSERVER_CORRECTION_20261008.md).

## Bind identity before the first RSS sample

Actual SparsePrefix134d failed with `unknown vanished process is not zero RSS`
after the four canaries, while its sampled peak was about124MiB under512MiB.
The specific rejected PID/syscall was not retained: do not claim that a named
Docker or SMI process caused it, or infer an unobserved peak bound. Its actual
stopped/retained cleanup and missing registry are distinct authorities.

For this bounded observer, capture actual Popen PID/start and descendant
parent/start before entering the RSS scope. A candidate disappearing between
enumeration and its first identity is not an already-known departed sample.
Keep unknown/live-unreadable/permission/PID-reuse failures hard. If a pending
candidate is retired, retain independent actual parent/thread/children and
strict absence fences; do not publish invented RSS=0. Record the first rejected
PID, syscall, errno and identity evidence before own-only cleanup.

MAIN136f really passed14 root/grandchild/lifetime/negative source tests.
It does not prove the v9 host integration, full167 suite, same-image software,
or NPU/model correctness. Preserve the134d failure.
[Actual evidence and remaining gates](../../../workstreams/qwen36-damp-ascend-20261006/EXECUTABLE_READINESS_LEARNING_20261008.md).


## Thread enumeration needs its own lifetime proof

A process being pinned does not pin every TID enumerated from its task list.
SparsePrefix1397 recorded thread.first-stat/PID3121095/TID3121130/ENOENT after
four arithmetic canaries and before model startup. Its first-refusal record
does not contain a parent-after fence: thread exit versus parent exit is not
yet proved. Preserve that uncertainty and the failed terminal.

For an observer successor, retain the same parent PID/start and task-set
before/after evidence, prove the vanished thread is absent rather than
unreadable or reused, and rescan all remaining parent thread children so a
departing thread cannot hide adopted live descendants. A genuine retirement
is recorded as such, not fabricated zero RSS. Permission, live unreadability,
identity drift/reuse and unknown absence remain hard failures. Real short-lived
thread/process competition and the complete aggregate/same-image paths are
required before a new source identity can admit NPU work; authored tests are
not their execution. Do not add these mechanics to unrelated non-thread
observers without a corresponding need.

## Generate short-lived admission evidence near dispatch

When a source-reviewed controller requires a60-second quiescence Ref, finish
slow static review/patch/hash work first, then capture actual host-time evidence
near dispatch. Retain an expired refusal and distinguish a new fresh-input
attempt from an unchanged retry. Do not set the clock, extend the window or
reuse a stale Ref to increase apparent utilization. Such a no-create refusal
does not prove a runtime or paper failure.

[Actual167/same-image successes,1397 first refusal and evidence limits](../../../workstreams/qwen36-damp-ascend-20261006/THREAD_ENUMERATION_AND_REGRESSION_LEARNING_20261008.md).

## Preserve child errors when a post-exit observer refuses ownership

When a device controller reports foreign occupancy, inspect its retained raw
SMI and the original child stderr before attributing the failure externally.
An exited owned worker can lose a live identity proof; a controller message
alone does not establish an unrelated occupier. Preserve both errors and their
ordering, rather than stopping external workloads or inventing the missing
identity. The Oct9 SP20 raw snapshot showed only its four owned workers while
the child actually rejected duplicate admission after abort/free and a skipped
scheduler step. A source-supported retirement repair is separate from the
still-failed TP4 result; complete lifecycle/NPU/E2E gates remain required.

For source-bound packets invoking another packet's real ABI entry, mount
coverage must include that entry's transitive source/identity reads, not only
the caller's direct pins. Host SHA/compile PASS cannot prove guest visibility.
Retain the no-device failure; qualify missing paths, immutable hashes and RO
destination coverage in a separate successor before taking a device lease.
Do not use the success consumer to relabel a failed prerequisite.

[Actual errors, minimal repair and pending gates](../../../workstreams/qwen36-damp-ascend-20261006/NATIVE_FREE_RETIREMENT_AND_MOUNT_CLOSURE_20261009.md).

## Check output parents before creating result leaves

A new output leaf being absent does not prove its required parent exists. Test
read-only ancestry, existing authorized parents, filesystem identity and the
combined disk reservation before inherited mkdir. Preserve a failed empty root;
use a new run identity after correcting the proved preparation defect. Inspect
all transitive time gates before calling a short phase executable near cutoff;
a shorter local lease does not override a longer shared admission guard.

[Actual MXR050 entry failure, DeltaLog051 compile and scope](../../../../docs/knowledge-base/ascend-infra/cases/split-scale-and-long-entry-20261016.md).

## Test real report semantics and plugin lifecycle

Use actual failed and successful report shapes in source-bound handoff tests.
A terminal nonzero-exit operation can have wrapper ok=False while its process
is completed; validate transport, exact command/owner, terminal state and the
expected exit separately. Do not require a failed historical phase to have
succeeded in order to preserve its quiescent evidence.

General-plugin registration can run in architecture-inspection subprocesses
before native operators or model instances exist. Keep registration distinct
from actual worker installation and prove the real first-instance dispatch.
A same-image cold plugin check is not model or numerical acceptance.

Preregister evidence coverage and the complete storage budget before dispatch.
A bounded smoke can precede larger workload validation without inheriting its
qualification. If input lengths change, freeze a new workload and recheck
consumers; fixed output length does not prescribe prompt length.

[Actual source-binding recovery, registry failure and bounded-evidence decisions](../../../../docs/knowledge-base/ascend-infra/cases/source-binding-registry-and-bounded-evidence-20261016.md).

## Match the cold service path before loading weights

A parser exercised after canaries or prior imports can hide an enabled-plugin
circular import. Keep default-OFF discovery in Devices[]; when the installed
runner legitimately queries HAL, test the enabled parser in a new isolated
process on the admitted mapping, before weights. Reproduce the actual service
CANN setup -> torch/torch_npu -> API -> parse order, not an invented colder or
prewarmed path. Charge the child to the existing phase deadline and preserve
argv/stdout/stderr on TimeoutExpired before refusing. A parser PASS proves that
startup seam only, never candidate math. R15 failed that real seam; R17's fresh
same-image process passed it without changing numerical or resource gates.

## Mutable output trees need complete bounded observation

A compiler can remove a temporary directory during a legitimate output-budget
walk. Preserve the first syscall/path/errno before cleanup; this is not a paper
failure. If exact root-contained ENOENT is proved, a source-bound successor may
restart the entire traversal within finite attempts and the original deadline.
Discard the partial sum, include every observed regular file, record the race,
and retain the unchanged byte cap/free-space floors. Permission, unknown/outside
paths, root replacement, churn or deadline exhaustion remain hard failures.
A completed sampled traversal is not an atomic snapshot or a peak-usage proof.

Test actual host ordering too: substrate load can precede the exclusive output
mkdir. Constructing a scanner must not inspect/create that absent root; pin its
ordinary inode at first real observation and reject subsequent replacement.
BOLE R7 exposed the compiler-directory race; R8's eager root pin was caught
before deployment, and R9 adds the load -> mkdir -> first-use control. Preserve
both failures/scopes instead of silently rewriting their source identities.

## Evidence ABIs and deliberate diagnostic stops

Do not loosen strict Ref3 readers to accommodate an original Ref2 producer.
Adapt every cross-stage call boundary explicitly: reopen a quiescent ordinary
file, derive its byte count and full hash, verify the original hash, and pass
exact Ref3 while leaving the original producer ABI intact. Test actual child
receipts, not only synthetic dictionaries.

An intentionally stopping observer can produce complete metadata while its
unaltered model owner exits nonzero. Preserve that failed owner and exact stop
trace, independently prove all writers released, then allow only a separate
metadata consumer. R17's all-four-rank/all64 ND/committed-index observation does
not authorize shared-storage alias bypass, numerical success, performance or
task acceptance. Strong live tensor/request/slot checks and the next NPU gate
remain required.


## Native ABI, complete entry wiring, and deadline evidence (2026-10-17)

- Never assume native model logits are FP32. Prove the active installed method, save original dtype/finite/full-vocabulary diagnostics before adaptation, and allow only a separately reviewed exact representation promotion. Keep the independent reader independent. An actual later BF16 observation does not retroactively identify an older run's unobserved failure subcondition.
- A default-OFF entry test or an abstract fixture does not prove the enabled path. Test the complete declared CLI through parser, actual predecessor consumption/readset, server environment, real speculative config and worker Session. Check metadata receipts against that same actual argv. A required ABI receipt must reach the leaf operator with its exact typed schema and semantics, not merely exist in a top-level manifest.
- Failure handlers may publish partial tensor files. Inspect each rank's primary failure before calling them completed computation; raw-file existence, model load and HTTP startup do not grant numerical or performance qualification.
- Keep worker/HTTP first failures separate from later host observer failures. Residual HBM after workers exit is not evidence of foreign occupation. Preserve timestamped SMI/process/ownership evidence and require an exact released-CID check.
- A lower actual container cap is a new resource experiment, not a relaxed reserve or a claim of universal peak fit. Create, inspect, cgroup observer, live globals and any copied resource globals must agree; OOM remains failure. Separate stale error-label captions from effective arithmetic and observed RAM changes.
- A remote timeout is an unknown outcome until independently checked. Recover executor receipts with the same idempotency key; inspect patch bytes before retrying. Re-read UTC after every unusually long call/yield. Never reset an elapsed experiment window, manufacture card utilization, or launch a late successor because an earlier tool call was delayed.

## Preserve compound guard operands, not just their error label

The Oct23 BOLE V5 short8 owner passed its Devices[] preflight and all-four tiny
canaries, then failed the compound PID/UDA/start/program guard during startup.
Its raw SMI retained physical5/PID3224862, but actual_compute was serialized
before the proof was appended. The exception name alone therefore cannot prove
which predicate failed or identify that PID's container. A different, earlier
physical5 process was independently attributed; do not transfer that identity.

A narrow diagnostic successor should retain the exact original guard's captured
PID/start/cgroup, own CID/server-start and per-predicate outcomes before cleanup,
then rethrow the original error. Preserve AND short-circuiting: not-evaluated
operands and uncaptured executable paths remain unknown. A later /proc read is
new evidence, not the missing same-instant value. Diagnostic write failures must
not replace the primary exception; instrumentation grants no retry or admission.
Keep the failed source/output and distinguish this ownership failure from model
mathematics or task accuracy.

## Give Devices[] stages their actual ownership domain

BOLE V4's cleanup-only repair was insufficient: initial observe ran before the
CPU role's expected create/inspect existed and still demanded unrelated NPU idle.
V5 bound a source-owned CPU-preflight intent before that first observation,
consumed it only for the exact original deviceless create, and required actual
Devices[] inspect plus own-only stop/reap/release. Its actual source-bound CPU
entry completed with no primary/secondary error; this did not qualify the model.

Inspect the actual controller before copying that repair. MXR's existing L21
resource_scope already used an empty card domain for card=None, and its real
upstream-bridge CPU owner completed while keeping the NPU branch and protected
boundary unchanged. Reuse correct scoped ownership; do not add redundant wrappers
or remove shared RAM/disk/CPU, source, own PID/CID or cleanup checks.

## A finite remote operation needs a terminal consumer

A submitted MODEL operation is not continuous scheduling. Bind an owner for
terminal recovery and the exact next consumer before calling the chain active.
Account for admission failures before the original owner creates RESULT.json:
retain a separate dispatch terminal with the actual exception/exit and whether
the registered model command was ever invoked. A RESULT-only waiter cannot
close that path. Keep its receipt distinct from the model owner's RESULT.

A narrow bootstrap may execute only the source-hashed, original model and
consumer argv. Preserve the child's actual entry, original resource/clock gates,
single-dispatch claim and original numerical consumer. Test real no-RESULT
process exit and startup rejection. A wait timeout must not silently kill an
owner or release an unknown lease. Source preparation, tested process handoff,
live model completion and numerical acceptance are separate states.

Operation retention can expire before chat resumes. not_found alone is neither
running nor released. Reconcile the original immutable terminal/source-before-
after, exact owned CID stop/exit and current overlapping-device state. If the
evidence cannot close the lease, keep UNKNOWN; do not wait forever for a deleted
control-plane record when equivalent final evidence is actually available.

Use actual compound-guard operands and installed globals. Captions32GiB/73GiB
can be stale while effective limits are48GiB/56.5GiB; measure before proposing
a resource change. A later healthy host snapshot is new admission evidence,
not a rewrite of a prior RAM/disk refusal.

For multi-rank diagnostic capture, reserve all simultaneously active CPU copies
against actual loaded usage. If serialization is required, acquire before
reservation/export and release only after original independent-report validation
and reservation retirement. Preserve lock-outside allocations in actual usage,
reject stale/failed reservations, and prove no collective lies in the held
closure. Do not discount filecache, raise tensor tolerances or count this
diagnostic scheduling change as algorithm performance.

A prepared downstream packet pinned to an old source/window is not READY.
Verify the actual predecessor consumer's exact source and time contract while
the current device phase runs. Reuse unchanged affected-code controls with
explicit equivalence; retain new source identity for changed execution metadata.
Include slow preparation/cold-admission costs when judging deadline slack.

Evidence: [Oct25 source, resource and dispatch recovery](../../../workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/renew24_20261024T075143Z/SCHEDULING_REPAIR_CHECKPOINT.md).
## Cost validation without weakening evidence
Before repeating a model gate, compare its actual startup, frame count and
independent-consumer cost with owner, client, individual HTTP and cleanup clocks.
Output tokens are not the diagnostic commit count; include the real permitted
commit bound. A monitor timeout with less than one second left can be the terminal
symptom of an underbudgeted phase, not a numerical defect. Repair all active
nested clocks in a distinct reviewed source within the unchanged human cutoff.

Choose a verification optimization from the actual executed path and whole
retained-frame timing. A fast synthetic indexing component may not match the
real reader; AST reversibility alone does not prove builtin binding, mapping or
Tensor semantics. Preserve failed applicability controls. A successful
same-frame metric match with negligible cost change is a closed prototype,
not an algorithm speedup or justification for another model run.

Offline mathematical-cost diagnostics must state omitted live-owner checks and
remain unqualified. They may identify the cause and test an implementation
change; only the original admitted NPU and scope consumers advance acceptance.
Do not cache evidence content or skip SHA checks merely to make a replay faster.


## 2026-10-25: Source construction, admission and budget boundaries

- Review proposed source in memory before materializing a destination when the native reviewer requires fresh source and experiment roots. Unbound generation and actual-authority validation may use different branches; exercise both, compare generated bytes, and preserve incomplete/failed artifacts.
- Rebind versioned controller references completely. Changing a path while retaining the previous controller's byte length or SHA-256 is not a valid Ref3. Check the actual CLI operand contract before calling the producer.
- A short output is not necessarily a short correctness run. The registered 32k-input/two-generation BOLE run exhausted the 3600-second phase after 20 valid frames. A later 10800-second phase/10000-second client/7000-second per-request proposal is a planning bound, not proof of completion or a performance result; two per-request upper bounds do not become two independently guaranteed allowances under one client deadline.
- Do not propagate a 512 MiB address-space limit from Python-only source inspection into the Docker client. A read-only comparison established that the same Docker inspect succeeded without that limit and failed to reserve Go page-summary memory with it. Separate virtual-address admission from physical-RAM accounting.
- Discrete RSS/cgroup snapshots are not simultaneous peak-allocation bounds. Keep serial export/consumer behavior until the aggregate RAM ledger, all live allocations, maximum case shapes and actual overlap establish safe concurrency.
- Keep source integrity, launch admission, numerical qualification and acceptance separate. Hash/inverse/import checks do not establish NPU correctness or whole-model gains. Time-window and disk-floor rejection are admission outcomes, not a paper-wide numerical or performance rejection.
- A same-image control import that stops at the disk precheck has not run. Preserve that result and its exact blocker; do not label it an import PASS or an algorithm failure.

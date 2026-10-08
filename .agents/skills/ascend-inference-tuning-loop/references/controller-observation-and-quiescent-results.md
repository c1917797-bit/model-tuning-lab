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

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

# Stateful plugin code-validation gates

Use for recurrent-state, deferred-update and cache-lifecycle changes. Adapt
coverage to the actual model and admitted runtime mode; do not enable unrelated
features solely to satisfy this checklist.

## Establish the invariant, then test the implementation

Write the relation between the original logical state and the candidate's base,
decay and pending updates. Derive append, merge, materialization and reset
transitions. Check actual head sharing, orientation, strides and conversion
boundaries against the executing source. An independent reference must not reuse
the candidate's key computation or state reconstruction.

When the ABI allows stale or uninitialized dead log entries, do not read them
into arithmetic: a zero weight does not suppress NaN/Inf. Mask payloads before
multiplication or sum only live entries. Test zero-length and partially live logs
with poisoned dead payloads; separately reject invalid live state before mutation.
Keep inactive slots byte-identical where that is the contract.

Compute the declared error metric at its declared unit (for example each request
or slot), then take the worst. A large-norm request must not hide a failing
small-norm request in a batch aggregate. For bitwise contracts compare shape,
dtype and byte views; value equality alone accepts signed-zero changes and can
hide dtype changes. Preserve legal dead NaN payload bytes rather than rejecting
every NaN indiscriminately.

## Exercise the actual bridge and metadata provenance

A standalone recurrent-kernel matrix does not qualify the prefill/decode bridge.
Call the actual plugin transitions with an independent expected state. Cover
more steps than a merge period, prefill with/without prior state, mixed requests,
row reorder, retirement and slot reuse. Require actual expected layer coverage
derived from the model configuration. A two-token service smoke only proves
startup/dispatch/response, not merge or lifecycle behavior.

For a no-D2H CPU metadata mirror, bind the actual scheduler-owned CPU source and
its H2D snapshot/copy path, KV group, request generation, epoch, native device
view, real layer and arena. Pointers prove view identity, not tensor content.
Invalidate old receipts before dummy/warmup overwrites buffers; disallow
unqualified dummy work while deferred state is live. Finish/check the last real
forward as well as intermediate forwards. Clearly distinguish cold OFF rollback
from an unimplemented hot uninstall.

## Recover evidence without rewriting failures

Inspect the complete independent-consumer read set, including CPU Meta and
predecessor receipts, in its actual mount namespace. If validation fails only
because a required read-only artifact was absent, retain the failed owner and
reopen the unchanged raw NPU data in a new bounded independent run. A successful
diagnostic owner is not a numerical PASS: check the underlying numerical and
strict-invariant fields separately. A missing guard/pointer receipt stays missing
until a new same-input run supplies it; join identities and output/state bytes,
and do not rerun an already complete matrix just to add one missing frame.

Keep heavy CPU/raw verification out of the NPU worker's timing path. Persist a
source-bound CPU result after actual termination/release; the worker validates
that certificate and its production-library identity, rather than importing
CPU-only consumers or repeatedly reopening all raw tensors.

Concrete evidence, failures and limitations are in the [2026-10-15 case](
../../../../docs/knowledge-base/ascend-infra/cases/runtime-binding-and-single-factor-evidence-20261015.md).
These gates do not replace whole-model matched performance and task accuracy.

## Validate the boundaries, not only the component

- Keep fixture modules out of the production import search path. Check the
  actual imported file and current configuration in a cold process; when a
  failure depends on collection order, reproduce it before repairing isolation.
  Retain semantic assertions and then rerun the affected same-image suite.
- Exercise the producer-to-consumer contract using the actual report schema
  and CLI/output rules. A correct inner result can still be rejected by a stale
  outer schema predicate or by placing input inside an output that must not yet
  exist. Repair that boundary explicitly, without renaming old reports or
  changing the independent mathematics.
- A reduced diagnostic must preserve launch geometry when geometry may explain
  the failure: full shape/stride, sequence metadata and grid first, compact saved
  evidence second. A device-synchronization timeout alone does not identify the
  failing kernel or establish an algorithmic no-go.

These checks target demonstrated integration failures; they are not a reason
to repeat already qualified, unchanged algorithm matrices or grow an unrelated
preflight framework.

For native-prefill/recurrent precision boundaries, verification-only streamed
raw checks and non-atomic compiler-child observation, see the
[native-boundary and saved-raw recovery supplement](
../../../../docs/knowledge-base/ascend-infra/cases/native-boundary-and-savedraw-recovery-20261015.md).

## Saved-frame identity and repeated-entrypoint seams

When extending a saved-frame replay across mixed model layers, distinguish a
capture map's actual model-layer keys from a recurrent-only list's ordinal
indices. Join them from the same pinned real payload and its metadata for each
source rank. Retain kind, rank, generation, ordinal and model-layer guards;
neither iteration order nor a filename is an identity proof.

For a changed selector, call that exact emitted runtime selector once on its
real saved inputs in the pinned image without devices before another device
admission. This is a cheap schema/identity check, not mathematical or NPU
qualification. Do not repeat unchanged mathematical suites for this purpose.

A wrapper around a process-oriented entrypoint must verify its actual exit
protocol across at least two consecutive calls and negative cases. Where the
original entrypoint raises SystemExit, accept only the declared exact integer
success code; reject bool, None, strings, nonzero codes and unexpected normal
return, and preserve unrelated exceptions. Initialize process-wide thread
settings once rather than once per case.

Check the final emitted driver, not only a repaired fragment or generator.
After the last generation step, verify its byte/AST delta and exact Ref before
dispatch; regeneration can reintroduce a rejected body. Preserve the original
oracle, tolerances, input-immutability checks, failed outputs and private error
evidence. A component matrix remains component evidence even when every case
passes; the service/state lifecycle still needs its own actual qualification.

For a configuration transform that retains embedded old/new source snapshots,
change the corresponding configuration tokens in every snapshot and preserve
the strict source equality and whole-byte inverse. Validate the actual producer
call path and its original preprocessing order: an isolated helper fixture or
CLI help can pass while the real caller still fails. A static inverse alone is
not evidence that native source preparation or model admission succeeded.

For EOS lifecycle adaptation, preserve the pinned engine's separate worker,
scheduler and HTTP domains: worker bookkeeping may retain sampled suffix tokens
that the scheduler excludes from the returned output. Do not invent a stricter
worker-prefix rule or fabricate a finish reason from a finished-ID alone. Check
the native-held request, typed finished-ID set, effective sampling parameters,
actual HTTP prefix/termination and every rank's retirement independently.
Unmodified native stop logic can be an independent software oracle, while a
field fixture that bypasses the native constructor is not native ABI evidence.

Before adding instrumentation, prove what existing successful verify, publish,
ACK and closed-frame receipts already establish in the pinned execution mode.
Reuse existing per-request calibration witnesses where sufficient; keep graph
replay and fallback scopes explicit, and avoid redundant per-kernel I/O.

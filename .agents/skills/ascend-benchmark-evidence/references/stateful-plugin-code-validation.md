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

# Native runtime contracts before the next model startup

Read this for a stateful-plugin failure at construction, prefill, publication, ACK or resource admission, especially after changing input length or speculative configuration. This reference grants no execution or cleanup authority.

## Repair the actual boundary

- Trace the first worker error through the real caller and callee. A normalized container may be a new object; pass the canonical object where the original contract requires identity. Do not replace a failed identity predicate with value equality. Conversely, preserve value equality for a value-type Owner when that is the original contract.
- Separate initial-prefill validation from active-frame validation. Do not fabricate a frame to satisfy a guard. Resource checks after ACK may still have a strongly held open live frame although runtime.active is cleared; inspect the real close order rather than treating active=None as proof of retirement.
- After fixing the first seam, inspect adjacent mandatory calls before paying for another model load. Exercise the affected production entry and refusal cases. Label AST/scalar/stub controls as such; they are not same-image Tensor, storage or NPU qualification.

## Derive geometry and budgets from the selected runtime

Use the pinned checkpoint, real native configuration and same-image native shape calculator. Distinguish full allocated state (including speculative entries/padding) from the algorithm's leading history tail. A short requested output does not reduce the native speculative allocation.

Recompute the original resource plan from that geometry, report every changed subtotal, and retain the outer approved limits. If those limits no longer fit, stop admission; do not silently enlarge them. Keep source/config derivation, same-image meta-Tensor checks, actual NPU shapes and measured peaks as separate evidence.

Put cheap native geometry/profile cross-checks into the existing same-image startup preflight, and have the controller consume the actual source-bound receipt. Keep their counts separate from unchanged historical tests. For native AR without speculation, a candidate-derived bound is not an observed AR allocation.

## Preserve independent claims

A streaming HTTP200 is only headers. Require complete returned token IDs, terminal DONE/normal finish as appropriate, and the independently joined worker/state lifecycle before calling the request qualified.

A native/reference failure triggers an oracle-applicability investigation, not an automatic candidate PASS. Do not transfer an inverse-tensor epsilon to long recurrent state, fit a threshold to the failed cell, or erase the old result. Freeze a defensible independent contract and validate untouched layer/sequence domains before model or performance promotion.

Task grades must refer to the verified generation body, not merely matching source/phase/arm metadata. When adapting a source envelope, invert it with the original checked transform and compare the whole object against the verified original RAW. Keep generated-code execution in its separately authorized sandbox.

## Real caller interfaces and faithful device-free controls

Source hashes and a constructed file plan prove identity, not that an installed
helper returns the interface its next consumer calls. Before another expensive
startup, execute the affected caller through installation and postverification
with its real immutable inputs. Check the returned capability and the exact
argument passed to it; a list of verified inputs is not a verifier object.
Include the actual outer CLI output leaf and the consumer's schema version.
Keep focused construction controls distinct from real-image and NPU evidence.

A device-free control must preserve the registered guard's semantics. Trace
its required read-only commands, wrappers, interpreter, arguments and timeouts
before adding a test fence. Blocking every subprocess can replace an expected
timeout with a harness exception, or reject an existing read-only inspection
wrapped by a resource-limit utility. Permit only the original reviewed calls
needed by that control; keep experiment starts, container/device mutations and
unregistered commands outside its scope. Classify an added fence's refusal as
a test-harness defect, preserve it, and repeat the affected control after repair.
Do not weaken the production guard or report a paper/numerical failure.

Keep guest, native controller and recording-wrapper terminals separate. A
guest's software PASS followed by a host postverification error leaves the
native stage failed; a wrapper exiting successfully after recording it does
not turn that exit into success. Reuse unaffected evidence only through the
registered consumer's supported recovery contract. If it rejects the failed
native result and has no recovery input, fix the actual interface and prepare
a new bounded affected stage. Preserve the original exit and result instead
of inventing a generic PASS/recovery schema.

Derive each stage's time and resource limits from the executed assignment and
callee, including any clipping by the remaining owner lease. A nominal numeric
budget in a manifest is not automatically the CPU stage's lease. An outer
observation limit may leave room for cleanup; it cannot extend the inner lease
or the human cutoff.

The October30 examples and their exact evidence are summarized in the
[BOLE/DeltaLog continuation handoff](../../../workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/HANDOFF.md).
They establish repaired source/control interfaces and scoped software results,
not NPU mathematics, whole-model performance or task acceptance.

## Evidence and next action

Record the failure class (wiring, implementation, numerical, reference, resource or invalid experiment), exact source/operation/output and the evidence that selects the next action. Transport observation failure is not experiment failure: recover a live operation with the same idempotency identity instead of restarting it.

Keep raw evidence and concrete numbers in the workstream checkpoint, not in universal rules. The October24 examples and original failures are in [the current workstream checkpoint](../../../workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/renew24_20261023T073553Z/CHECKPOINT_20261023T2333Z.md). BOLE had reached one first token, not a completed qualified request; MXR passed one untouched full-frame control, not all-layer/model acceptance. HYPIC remains a historical example, not a new result.

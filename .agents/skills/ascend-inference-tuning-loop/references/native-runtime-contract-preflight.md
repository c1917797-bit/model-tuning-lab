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

## Evidence and next action

Record the failure class (wiring, implementation, numerical, reference, resource or invalid experiment), exact source/operation/output and the evidence that selects the next action. Transport observation failure is not experiment failure: recover a live operation with the same idempotency identity instead of restarting it.

Keep raw evidence and concrete numbers in the workstream checkpoint, not in universal rules. The October24 examples and original failures are in [the current workstream checkpoint](../../../workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/renew24_20261023T073553Z/CHECKPOINT_20261023T2333Z.md). BOLE had reached one first token, not a completed qualified request; MXR passed one untouched full-frame control, not all-layer/model acceptance. HYPIC remains a historical example, not a new result.

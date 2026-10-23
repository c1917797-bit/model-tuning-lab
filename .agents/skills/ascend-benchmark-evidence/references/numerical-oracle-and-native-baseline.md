# Independent numerical truth and reduced-precision native baselines

Apply when a native-peer comparison fails while an independent higher-precision
reference suggests a different attribution, or when both native and candidate
fail the same absolute oracle gate.

Keep three quantities separate: native versus mathematical reference, candidate
versus mathematical reference, and candidate versus native. A native kernel is a
production control, not automatically exact truth. A higher-precision reference
also needs independent formula, normalization, state-layout, scale and reset
checks. No NaN/Inf is not a correctness gate.

Use the same immutable real input/state and normalization boundary for both arms.
Check actual dispatch, loaded source/library, dtype, runtime flags and input
mutation. A standalone replay is diagnostic until its relation to the real worker
is proved; compare replay results with the saved worker output and intermediate
inputs rather than assuming source equality proves execution equivalence.
Recover valid saved raw data after controller/import failures instead of
unnecessarily reloading the whole model.

If native also fails, preserve every original FAILED result. It is evidence that
the test contract or native precision needs investigation, not permission to
ignore the candidate's failure or reject the paper. Use independent algebra
controls and actual native measurements; a constructed dtype counterexample
alone does not identify the cause of a real frame.

A repaired numerical contract is a NEW experiment: freeze its reference,
thresholds, aggregation, dtype/rounding semantics, normal/subnormal/overflow
scope, lifecycle coverage and unseen holdout inputs before running it. Retain
old peer metrics and failure identities. Do not fit a larger epsilon to a failed
cell, use task-level accuracy tolerance as a tensor tolerance, or promote from
retrospective diagnosis alone. An operation-count error bound that grows with
candidate-owned cancelling terms needs an independent forward-error or
conditioning restriction; otherwise even a grossly wrong output can pass.

When the output ABI is BF16, distinguish the CPU64 reference before conversion,
the explicitly specified final reference conversion, and the actual BF16 output.
Do not assume a float64-to-BF16 library cast performs direct nearest rounding:
an intermediate FP32 conversion can double-round. Test midpoint-above/below,
ties-to-even, both signs, zero, subnormal and overflow behavior. If exact nearest
real output is claimed near a boundary, validate reference uncertainty with an
independent higher-precision calculation or justified interval. A reproducible
CPU64-operational oracle is an empirical contract, not a universal real-number
or CANN Exp theorem.

A repaired contract still requires independent wrong-scale/head/slot/metadata
negative controls, unchanged state/inactive-slot guards, relevant multi-step and
graph tests, and the final whole-model performance and task gates.

Evidence and limitations: [actual binding and numerical-baseline case](
../../../../docs/knowledge-base/ascend-infra/cases/runtime-binding-and-single-factor-evidence-20261015.md).
For subnormal failures, inspect actual operand/output bits and absolute error as well as relative error. Per-product FP32 rounding can impose a relative floor even when conversion, state and guards are correct. Distinguish this from flush-to-zero using immutable raw and an independent rounding model. An arithmetic-order repair is a new candidate and must retain overflow/cancellation tests; a CPU prediction cannot qualify its NPU implementation.

Persist each independent predicate and its raw identity before an aggregate assertion can terminate the consumer. A successful diagnostic owner proves complete inspection, not numerical qualification; failed boundary rows still block admission. Recover existing complete raw rather than repeating NPU execution merely to recover an omitted verdict.

For chunked GDN, distinguish a conditional inverse of the **actual rounded A**
from the full canonical recurrence built independently from original Q/K/g/beta.
Passing the former does not imply correct WY/H state propagation. Label an
oracle's own solve-residual separately from residuals measured on native or
candidate outputs; zero oracle self-residual is not exact candidate arithmetic.
A larger frozen matrix may reveal candidate-only misses even when earlier frames
showed shared native/candidate misses. Retain all three comparisons per frame,
attribute the first differing edge with counterfactual intermediates, and reserve
new failed frames as holdouts rather than waiving them as native precision.
Evidence: [saved-worker full48 diagnostic](../../../workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/renew24_20261023T073553Z/MXR_FULL48_DIAGNOSTIC_20261023.md).

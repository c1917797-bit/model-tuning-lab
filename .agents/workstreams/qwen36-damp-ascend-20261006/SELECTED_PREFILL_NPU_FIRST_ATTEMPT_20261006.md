# First actual selected-prefill NPU attempt and preparation correction

MAIN MA066f independently passed 43/43 stdlib source/actual-parent regressions;
receipt `b9c1d9ee…`. This proved preparation only, not Torch/NPU semantics.

## Actual failure, not a claimed success

MA0670 completed exit1 after fresh physical NPU4 -> logical0 admission,
nonprivileged canary and selected SO loading in actual Ascend910B4/CANN9.1.
Its raw report records 47 checks, 44 completed host negatives and zero completed
packing cases. The failed assertion is
`host_noncontiguous7_prepare_rejected_all_inputs_raw_unchanged`;
the supposedly invalid call produced no dispatch exception. The code constructs
P1 `indices[1]` with stride2 by slicing. Singleton shape semantics can still
make that tensor contiguous: this is a fixture hypothesis, not an established
operator defect, numerical failure or paper-wide no-go.

Preserve the raw report, original operation JSON, negative .pt and first_failure.
The exact owned container `05470975…` is stopped and retained, not deleted;
actual state is exited/Pid0/OOMKilled=false. Protected0–3 and release were checked.
The JSON companion holds full original paths and SHA identities.

MA0674 is running the distinct native_feedback stage on physical7, NEW
`native-repair-v2`; it does not repeat the isolated host-negative loop.
No PASS, final192 plan, shared service, graph, performance or task accuracy is
inferred from starting that operation. Its source packet stays immutable while
live. Component admission still needs both actual complete stages.

## Reusable preparation rules

- Negative fixtures need explicit semantic preconditions: actual shape, strides,
  is_contiguous, offset/alignment, dtype and alias classification. A slice is
  not automatically an invalid ABI input; singleton axes require special care.
- Reuse the exact target image Torch semantics for fixture checks before a long
  numerical matrix. Keep bad fixtures and failures immutable. Correct a proved
  fixture error in a new source-bound successor, not by waiving its assertion.
- Before cards: validate actual tool success/nonzero/cancel/timeout branches,
  module/ABI closure and callable signatures, source pins, commands, matrix,
  host oracle cost, ordinary RAM/CPU/disk joint budgets and one-shot output IDs.
- Parallelize genuine independent work only with symmetric ownership/monitor
  compatibility; neither CPU checks nor tiny canaries count as full NPU math.
- The old allT dispatcher has an artificial full-calibration scheduling coupling
  and its frozen reference helper accepts only B1/B16. A NEW reviewed dispatcher
  and trueT reference seam are being prepared; the old T2–15 path is not ready.
  Do not use PAD16 or manufacture a calibration SOURCE_LOCK to unblock it.
- Capture OFF/ON task-output drift remains unresolved and prevents final192
  fitting. Native turn-shape equivalence also requires evidence; logical client
  batch4 does not force native simultaneous prefill4.

The fixed paper deadline remains 2026-10-07T08:48:03Z.

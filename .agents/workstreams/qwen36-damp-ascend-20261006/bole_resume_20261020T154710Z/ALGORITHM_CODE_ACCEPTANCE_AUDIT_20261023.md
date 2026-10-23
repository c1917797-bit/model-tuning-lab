# Algorithm-code acceptance: evidence audit, 2026-10-23

This is a scoped implementation audit, not a numerical PASS, performance
result, paper rejection, or replacement of any frozen experiment contract.
The active human-approved window remains 2026-10-23T07:35:53Z through
2026-10-24T07:35:53Z, including cleanup. HYPIC is a historical exemplar.

## First-implementation deliverable

Before promoting an implementation to model performance screening, identify:

1. Paper/official-source mechanism -> functions -> actual worker/operator.
   Declare layout, head mapping, normalization, scale, update order, precision
   and rounding boundaries. Distinguish faithful migration from approximation.
2. An independent, direct mathematical oracle which does not reuse the
   candidate's critical calculation. Source identity alone is not independence.
3. Hand-computable nonzero-state and boundary controls, plus zero-update,
   append/materialize, masking, invalid-input and inactive-slot invariants.
4. Real-NPU output, complete logical state and necessary intermediate values
   against that oracle under the predeclared numerical domain and thresholds.
5. An independent trajectory from one common initial state, not a new oracle
   reset to the candidate's captured state at every step. Cover actual batch,
   transition, request-lifecycle, slot-reuse and relevant graph branches.
6. Negative controls which prove that wrong order/head/layout/rounding,
   missing decay, wrong merge and forbidden writes are actually rejected.
7. Actual source/operator loading and worker-call evidence for the model path
   to be measured. Smaller-geometry evidence cannot silently qualify 32k.

Report source/launch checks separately from mathematical qualification.
Software test counts, successful container creation, finite tensors and a
single HTTP response are not interchangeable correctness certificates.
User-allowed task-quality loss is not an intermediate tensor tolerance.

## DeltaLog: inspected existing code, not a newly passed gate

Source: the `deltalog-real-worker-new24h-v1-101-repair17-native-postprepare-footprint-20261017-001`
packet under `/cache/cch/qwen36-paper-preparation-20261007/lowbit/`:

- `dependencies/numeric_oracle.py`: SHA-256
  `cd395a05dbfcb21f1104d617afb1fab6f80374016585e9096ca24d85c2cae97a`.
  Independent CPU64 per-head dense recurrence; no deferred-log kernel call.
- `tensor_consumer.py`: SHA-256
  `08dd5b74dc2feefc2582658378cf934d298933f0fa61d511c53cd60c72b5fe0d`.
  State relative-L2 <= 7.92e-7 for independent-before, independent-after and
  native-peer comparisons; finite values and state/write invariants required.
- `precast.py`: SHA-256
  `4f1ca4d1243c90c663db2702010ecef8f76805a4259d107fb1be44648f35695d`.
  Actual pre-cast FP32 per-request normalized peak <= .00303 AND relative-L2
  <= 2^-13; BF16 bytes must equal independent direct-RNE(actual FP32).
  These are frozen empirical-domain predicates, not universal error theorems.

The current first-decode experiment starts from an unchanged native-prefill
boundary and independently checks one actual decode on all 48 GDN layers and
four ranks. It must not qualify merge, accumulated 160-step state, lifecycle,
normal EOS, task quality or performance merely by passing that first step.

The historical numeric16 owner remains a normal completed owner with a failed
strict independent qualification. Its local captured-before recurrence checks
do not prove an independent accumulated trajectory. Preserve the original
`INDEPENDENT.json` (4421 bytes,
`e7ac3e627bdba3918cc4632b22adf315cbbcae2071babadeea6a1abede1f606f`)
and `DOMAIN088.json` (224296 bytes,
`5f2a542b39d14a7fb6fa8f99619382a734cb70a674a35a8d73beaeed9aa891d5`)
in `/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/run-numeric16-MAIN-20261016-NEW24H-088-repair6-repair2-001/native/`.
Their qualification flags remain false. No historical failure is overwritten.

## BOLE: current rendered-code scope and missing model proof

The reviewed 48G renderer preserves the existing independent component math:

- GDN: peak absolute error <= 2e-5 + 2e-4 * max(abs(reference)) AND
  relative-L2 <= 2e-4; independent per-node FP64 recurrence versus the
  candidate's ancestor-matrix/depth expansion.
- Conv and FA: each element must satisfy abs(error) <= .001 + .01*abs(reference).
  Conv tails require byte equality; FA requires both independent FP64 and FP32
  path references, not another call to the candidate FIA wrapper.
- Actual accept/commit/rollback decisions, all 128 writes and untouched
  destinations require their separate exact state/ownership checks.

These are existing project gates, not a paper-provided whole-model guarantee.
Historical 131-prefix component/service evidence does not qualify the changed
dynamic-prefix service FIA wrapper, FAST observation path or 32768 input.
Current 32k first8 and subsequent trajectory/lifecycle proof remain pending.

## Latest preparation boundary

DeltaLog v4 early same-image Devices=[] preflight actually executed 253/253
software cases with zero skips plus 26/26 payload controls, and released its
retained container. The original full bound-only 255-case gate remains separate.
Owner RESULT: 838 bytes,
`da5212c86157bd7b976b9d85d95b41602281c5755f55d8d2d1b57df9d734e43c`,
at `/opt/host/vnf/austinov/run-deltalog-current-three-tree-20261023-v4-early/software/consumer/RESULT.json`.
This is software evidence only. No new NPU numerical, E2E or quality result is
claimed here. The active binder operation is `exec-0000000000000f19` on the
resolved chicaihong01/ma peer; inspect its actual terminal state before any
successor. A wait/timeout is not permission to duplicate that operation.

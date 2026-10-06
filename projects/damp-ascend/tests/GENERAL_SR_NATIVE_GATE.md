# Independent general-SR native gate — prepared, NOT executed

The new files do not modify the frozen production/reference/collector code.
Parent alone builds libraries, starts/stops containers and runs NPU workloads.
No performance, model calibration or task-accuracy result is claimed here.

MAIN review repair on2026-10-06: the eager reference explicitly converts its
new four-dimensional FP32 output through the deployed public ND ABI and checks
all three actual output formats. Meta and copied native arithmetic are unchanged.
Reference raw returns/input-after and candidate full packed-after/output are
retained BEFORE format, finite or unpack checks; complete byte-interval
nonalias and static/turn pointer guards supplement bitwise input checks.
These are harness/source repairs, NOT a built or NPU-passed reference.

## Preregistered order and scopes

1. Six NEW strict reference/native anchors: B1/B16 × SR1 identity plans,
   SR1 arbitrary per-Hv Pk/Pv, and power2 SR with arbitrary per-Hv Pk/Pv.
   Each changes Q/K/V/g/beta and unique active slots for160 steps.
   Compare complete transformed-coordinate FP32 state and restored BF16 output
   BITWISE; all input/static/untouched/pointer guards must pass. This stricter
   reference-identification test does not overwrite the older restricted gate.
   Expand native Q/K from model HQ4 to NK12 and THEN gather each Hv's Pk.
   Native has no exposed FP32 pre-cast output: only these exact dyadic/power2
   fixtures permit the tested native-BF16 restore commutation. Native FP32
   state is compared in the SAME transformed frame, not via a lossy inverse.
2. Only after ALL six anchors pass: B1/B16 × synthetic general positive FP32
   SR/random plans and general SR/near-half-cell cancellation stress,160 steps.
   Candidate mutates only FP16 hi + INT8 lo + FP32 scales. Reference unpacks
   its OWN independently quantized state, runs the separately named native-
   derived reference, and CPU packs only selected slots. No resync, candidate
   helper, candidate trace or CPU mv/sum recurrence is a golden.
   State max per-head relativeL2 <=1e-5, BF16 output <=0.00303; complete state
   is also checked. Preserve failures at half-cell crossings; never relax.
3. Final calibrated192plans, graph, mixed scheduling, slot leases, typed
   allocation/cache manager, TP4 serving, E2E speed and task accuracy are
   separate required gates. A synthetic general-SR receipt is not their pass.

The immutable reference receives original BF16 V; FP32 Div(V,c) precedes Pv.
Output is restored from the updated FP32 state before its sole BF16 cast.
Reference has no compressed buffers or quantizer. Test-only full FP32 arenas
are allowed for the anchor; there is no production persistent FP32 sidecar.

Full output roots must be NEW and outside Git. <160 steps is smoke-only.
Every turn hashes its fixture, compares complete states/inputs, records guards
and CPU independent pre-RINT proximity. On first failure it saves before/after
states, raw inputs/plans, reference updatedFP32/output/pre-RINT quotient and
candidate result to first_failure.pt with SHA256. This is reference evidence,
not a claim to expose the candidate's intermediate arithmetic.

## Parent-only commands

First, stdlib-only contract/source-pin tests (no torch/device required):

    PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
      projects/damp-ascend/tests/test_general_sr_contract.py

Then a same-image NO-device fixture audit:

    PYTHONDONTWRITEBYTECODE=1 python3 \
      projects/damp-ascend/tests/general_sr_native_gate.py --audit-only \
      --output-dir /damp-results/general-sr-fixture-audit-v1

Actual NPU launch after the parent's fresh physical4->logical0 / nonprivileged
inspection, independent reference compile/load/source-contract proof, candidate
frozen identity and manifest preparation:

    ASCEND_RT_VISIBLE_DEVICES=0 DAMP_ENABLE_NATIVE_REFERENCE=1 \
    PYTHONDONTWRITEBYTECODE=1 python3 \
      projects/damp-ascend/tests/general_sr_native_gate.py \
      --operator-library /ABSOLUTE/PRODUCTION-REGISTRATION.so \
      --operator-sha256 FROZEN-64-HEX-SHA256 \
      --reference-library /ABSOLUTE/libqwen36_damp_native_reference_ops.so \
      --reference-sha256 FROZEN-64-HEX-SHA256 \
      --device-proof /damp-results/FRESH-DEVICE-PROOF.json \
      --native-source-manifest /damp-results/GENERAL-SR-SOURCE-MANIFEST.json \
      --native-source-manifest-sha256 FROZEN-64-HEX-SHA256 \
      --output-dir /damp-results/general-sr-native-gate-v1

Use --anchor-only in a separate NEW root to validate the independent reference
against native before the quantizer repair is production-ready. This executes
only the six stage1 anchors and never dispatches the known-failed compressed
candidate. Its receipt explicitly records compressed_candidate_dispatched:false;
it is NOT a general-SR compressed or overall DAMP pass.

No auto-build, Docker action, graph capture, performance timings or automatic
retry occurs. Even failure before dispatch has a report/original traceback.
Native ABI is validated before invocation: FOUR positional Q/K/V/state,
SEVEN named keyword-only arguments. Registration/Meta checks do not prove graph.

Each general case explicitly checks prepare returns None, all SIX inputs
(q0, hi, pk, pv, inv_pv, sr) remain bitwise unchanged and keep their pointers,
and all THREE complete packed-state regions stay bitwise/pointer unchanged.
Snapshots are retained in the first-failure fixture if prepare raises or
mutates input. This check occurs outside capture, before the first recurrence.

The prepare-negative matrix is NOT automatically executed by this new gate.
Reuse the separately prepared eager_prepare_and_rejections function in frozen
packed_recurrence_gate.py, in a separately registered parent run if its NPU
receipt is not already bound to these exact bytes/SO. It covers duplicate and
out-of-range Pk, wrong plan dtype, bad Pv shape/permutation, inconsistent inverse
Pv, zero/negative/Inf/NaN SR, query dtype and hi shape; valid prepare is restored
afterward and all six good inputs checked unchanged. Do not infer an executed
NPU PASS from this source inventory or its older Meta/software receipt.
The separate invalid_dynamic_metadata matrix concerns decode lengths/slots
(atomic unchanged state/all-NaN sentinel), NOT prepare negative rejection.
Graph capture, blocked-format prepare rejection and complete malformed ABI
coverage remain separate gates; this new runner does not certify them.

Device-proof fields are the same frozen external-parent contract: unique
physical_npu_ids in4–7, logical_to_physical["0"]=4, privileged:false,
exclusive_resource_check_passed:true, observed_at_unix_ns<=30min and nonfuture.
A file's presence is not live ownership/mapping proof.

Source manifest JSON must contain:

- native_commit:5cb98caaadeff42b5b62b996e34bb2aaa29d20fd
- native_header_sha256:96e6d9667af1e3457316ffce92a8a983fcb90096df08e3efd13ec0b35b8b1c5b
- reference_source_hashes: EXACT REFERENCE_HASHES dictionary in the new runner
- candidate_source_hashes: EXACT CANDIDATE_HASHES dictionary in the new runner
- image_id: parent-inspected immutable serving/build image identity
- native_runtime_library_path and native_runtime_library_sha256:
  exact observed process-loaded native operator library (not a source header)
- source_contract_passed:true: parent's retained exact pinned-source receipt.

The runner independently checks all frozen source bytes and SO hashes, loaded
schemas/Meta B1/B16, physical ND, actual native runtime path/SHA in process maps,
CANN/torch/torch_npu identities and lazily loaded library snapshots. The external
manifest binds build provenance; source hashes alone cannot prove runtime
arithmetic. The actual bitwise anchors supply that missing numerical evidence.

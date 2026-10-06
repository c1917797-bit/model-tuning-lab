# DAMP independent numerical preparation

This package is equation-derived, not verified official DAMP author code.
Paper source: https://arxiv.org/abs/2608.27513v2 .
The independent CPU oracle does not import candidate pack/unpack, transforms,
or recurrence. It is a numerical reference, not a performance implementation.

## Frozen Ascend-adapted ABI

The new operator interface is:

    torch.ops.qwen36_damp.prepare(q, hi, pk, pv, inv_pv, sr)
    torch.ops.qwen36_damp.decode(
        q, k, v, g, beta, hi, lo, scales, pk, pv, inv_pv, sr,
        actual_seq_lengths, state_indices)

| Region | Physical shape / dtype |
| --- | --- |
| hi | [slots,12,128,16], FP16, value-major |
| lo | [slots,12,128,112], symmetric INT8, value-major |
| scales | [slots,12,4,112], FP32 |
| pk, pv, inv_pv | [12,128], INT32, logical indices 0..127 |
| sr | [12,128], FP32, original-coordinate positive c[h,v] |
| q, k | [batch,4,128], normalized native BF16 |
| v | [batch,12,128], BF16 |
| g / beta | [batch,12], FP32 log decay / BF16 update gate |
| actual_seq_lengths | INT32 [0,1,...,1], pinned per-sequence single-token ABI |
| state_indices | INT32 [batch], unique in-range slots |
| output | [batch,12,128], BF16 |

Pv and Pk map reordered -> original; inverse Pv maps original -> reordered.
GQA maps value head h to Q/K head h//3, then applies that value head's Pk.
SR c is in original coordinates: gather(v/c,Pv); update; read out with
128**-0.5; multiply by c[Pv] and inverse-Pv restore. Readout is from updated
FP32 state BEFORE it is compressed for the next token.

Groups of 32 run along reordered **value** channels. The three static plans
contain INT32 logical indices, not byte offsets. The kernel constructs byte
offsets internally. The old key-major PyTorch representation must never be
passed as this operator's ABI. The test runner has a named transpose adapter
solely to test the earlier PyTorch reference.

## Arithmetic and negative cases

Scale is FP32 nearest-even multiplication of group amax with FP32 reciprocal
bits 0x3c010204. All-zero groups use exact FP32 scale 1. Codes use FP32
x/scale followed by nearest-even integer rounding and clamp[-127,127].
No code -128 is allowed.

Boundary tests include positive/negative half points, one FP32 ULP on either
side, non-power-of-two scales, zero groups, real V-group boundaries, INT8
endpoints, FP16 +/-65504, tiny representable scales, and FP32 extremes in the
low region. A scalar Fraction-distance oracle independently verifies FP32
division for boundary samples. Positive-amax scale underflow, nonfinite input,
and FP16 high-region overflow are explicitly unsupported/fail-closed; no
epsilon floor, alternative rounding or NaN-to-zero recovery is silently added.

## Pre-registered matrix and meaning

Default steps: 160; batches: 1 and 16; slots=batch+3. Each turn changes q/k/v/g/
beta and active slot IDs. Layout has nonidentity, per-Hv value/key permutations
and positive synthetic SR scales. No model calibration fidelity is claimed.

Implementation parity is measured against an independent **compressed**
trajectory using the same frozen quantization algorithm. Selected-slot,
per-head maximum relative L2 thresholds are state <=1e-5 and BF16 output
<=0.00303. These are new pre-registered numerical gates, not the previous
full-state-average metric and not the user's 1% task-accuracy allowance.
Keep failures if these gates do not pass; do not tune thresholds post hoc.

A separate uncompressed trajectory reports quantized-versus-dense state/output
drift only as a diagnostic. It is not a task-accuracy result. Static packing
and unpacking parity are bitwise, including scale arrays and boundary codes.

The operator matrix checks all packed regions of untouched slots bitwise,
stable storage pointers, all static/turn inputs unchanged and state indices
unchanged. It is eager single-token only. Mixed prefill/decode, graph,
cache allocation, 48-layer TP4 serving, model-calibrated masks, performance
and LongBench-v2/GSM8K are explicitly outside this package's pass scope.

The harness invokes the explicit six-argument prepare outside capture and
before first decode. It tests schema mutable aliases only at state positions
5/6/7, a fresh non-alias output, Meta shapes/dtypes for B1/B16, and synchronous
prepare rejection of malformed shapes/dtypes, permutations/inverse Pv and
nonpositive/nonfinite SR. Unsupported dynamic lengths/indices must produce
all-NaN output while every region of every slot remains bitwise unchanged.
This negative all-NaN sentinel is checked only for unsupported metadata; valid
numerical runs require finite state/output.

The first CPU smoke failure is preserved separately. An exact-fixture
diagnostic proved that its legacy reference harness requantized unselected
slots, drifting scales by 1 ULP per repack. The corrected reference harness
repacks selected rows only and checks untouched packed bytes; the independent
oracle and frozen numerical limits did not change. This is a harness fix,
not evidence of operator, graph, performance or quality success.

## Execution: parent owns all containers and NPU scheduling

Use a new output directory outside the repository. Never overwrite a prior
run. The host Python lacks torch; run CPU mode in the same frozen image,
without NPU visibility/device attachment. The child preparing these tests
does not create containers or launch NPU.

Inside an already authorized, correctly mounted same-image CPU environment:

    PYTHONDONTWRITEBYTECODE=1 python3 \
      projects/damp-ascend/tests/packed_recurrence_gate.py \
      --mode cpu \
      --output-dir /damp-results/independent-packed-cpu-v1

The parent must first re-prove physical4->logical0, nonprivileged isolation,
and current device ownership. Save its fresh launcher/device manifest externally.

    ASCEND_RT_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 python3 \
      projects/damp-ascend/tests/packed_recurrence_gate.py \
      --mode npu-reference \
      --device-proof /damp-results/FRESH-LAUNCHER-MANIFEST.json \
      --output-dir /damp-results/independent-packed-npu-reference-v1

After building and validating the independently named operator's loader ABI:

    ASCEND_RT_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 python3 \
      projects/damp-ascend/tests/packed_recurrence_gate.py \
      --mode npu-operator \
      --operator-library /ABSOLUTE/PARENT-BUILT-TORCH-REGISTRATION.so \
      --device-proof /damp-results/FRESH-LAUNCHER-MANIFEST.json \
      --output-dir /damp-results/independent-packed-operator-v1

Operator mode requires that the supplied library registers the exact torch
schema. It does not silently import a replacement candidate or reinterpret
plan dtype. The parent must verify loader/library provenance and actual
device mapping; a manifest file's existence is not itself mapping proof.

--steps 8 can be used for a first smoke but is labeled smoke-only. It cannot
stand in for the 160-step matrix. No timings or speed ratios are emitted.

Passing --operator-library in CPU mode also runs schema/Meta checks without
calling eager prepare/decode on a device. A loader failure remains a separate
build/import failure, not a mathematical or NPU result.

To diagnose one retained failure (no NPU):

    PYTHONDONTWRITEBYTECODE=1 python3 \
      projects/damp-ascend/tests/diagnose_packed_failure.py \
      --fixture /damp-results/independent-packed-cpu-smoke-v1/first_failure.pt \
      --reference-sha256 SHA256-FROM-THE-RETAINED-FAILURE-REPORT \
      --output-dir /damp-results/independent-packed-cpu-diagnostic-v1

CPU smoke v2 passed untouched-slot checks but failed the unchanged 1e-5
state gate at B16 step2. The same-before diagnostic found two INT8 half
crossings after tiny FP32 reduction differences. This is distinct from the
v1 slot-lifecycle bug; neither result decides the unbuilt NPU kernel's
correctness. See [NPU_PARITY_PROTOCOL.md](NPU_PARITY_PROTOCOL.md): preparation,
not an executed pass. The native golden helper is likewise not yet executed.

## Restricted native-golden runner (new gate, not a CPU v2 rerun)

All source edits below are prepared only; no NPU result is claimed. First run
the frozen fixture audit in the same image without devices:

    PYTHONDONTWRITEBYTECODE=1 python3 \
      projects/damp-ascend/tests/restricted_native_golden_gate.py \
      --audit-only --output-dir /damp-results/restricted-fixture-audit-v1

It checks all 640 frozen turn fixtures for exact native BF16 V/SR conversion.
It is not a recurrence, NPU, performance or quality gate.

Restricted-native v1 is preserved as a call-ABI failure: native permits only
query/key/value/state positional, and seven keyword-only arguments. It did
not execute HQ12 or candidate numerical work; do not call it an NPU algorithm
failure. The helper now spells out all keyword arguments, the runner checks
actual schema names and kwarg_only flags BEFORE first native invocation, and
a stdlib-only AST/strict Python binder regression rejects the old call:

    PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
      projects/damp-ascend/tests/test_native_call_contract.py

This test requires no torch/container/device. It does not validate the actual
loaded Torch schema; the runner performs that separate pre-dispatch check.
Optionally add --schema-report pointing to the retained v1 report in an
existing no-device same-image CPU run. That imports torch only to parse the
retained schema and verify its Python kwarg_only API; it loads no native
library and is still not proof of the new runtime's actual schema.

Parent then runs the actual, separately preregistered native-golden gate:

    ASCEND_RT_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 python3 \
      projects/damp-ascend/tests/restricted_native_golden_gate.py \
      --operator-library /ABSOLUTE/PARENT-BUILT-REGISTRATION.so \
      --operator-sha256 SHA256-FROZEN-AFTER-META-LOAD \
      --device-proof /damp-results/FRESH-DEVICE-PROOF.json \
      --native-source-manifest /damp-results/NATIVE-SOURCE-BUILD-PROVENANCE.json \
      --output-dir /damp-results/restricted-native-golden-v1

Device proof JSON must record physical_npu_ids ([4] or a subset of 4-7),
logical_to_physical ({"0":4,...}), privileged:false,
exclusive_resource_check_passed:true, observed_at_unix_ns (within 30 minutes),
plus the parent's actual Docker/device/ownership observations. These fields
are external authority, not a script's independent host verification.
Native-source manifest must record reference/build/runtime identities; the
runner also checks actual GDN source, native schema and lazily loaded library
paths/hashes. The default deployed GDN hash is frozen; changed source must be
reviewed before supplying an explicit new expected hash.

Actual NPU order: B1/B16 HQ12 dyadic exact smoke, then four independent
160-step closed loops (B1/B16 x identity/power2 SR) with random per-Hv plans.
Candidate uses production prepare/decode, golden uses only native recurrent
plus independent CPU selected-slot pack; each feeds back its OWN state.
Steps below 160 are clearly smoke-only. Generic/non-power2 SR, graph,
batchmix, 48-layer serving, E2E speed and task accuracy remain unverified.

## Retention details

Report is updated at every check/turn with JSON-safe nonfinite markers, failed
case status and original exception. First numerical failure retains a CPU
tensor fixture and SHA256 outside Git. Fixture dumping cannot replace the
original exception; it records any dump failure separately. Output roots are
immutable per run. Do not retry a deterministic failure without a stated
implementation/harness change and a fresh output root.

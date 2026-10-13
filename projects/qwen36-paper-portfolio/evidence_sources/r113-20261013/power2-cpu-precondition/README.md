# Exact power-of-two control — CPU preconditions only, default OFF

Direct FP16001 is immutable and must NOT be deployed: MAIN Ma0298 actual
q1536 and selected V32 each lose one2^-25 bit in HALF, and full V includes
the same loss. This is an input-representation failure, not a native test.
Exact original descriptor: root-level FLOAT16_SOURCE_EXACTNESS_001.json
1342/4d527a03fedca5ade88ccf476a41d8392e357b15d87b0ba9fd14d8114832ef56.

This small leaf only prepares Qfloat*2, Kfloat*.5, Vfloat*2, then exact HALF.
It has NO FIA invocation and no controller. Functions:
prepare_power2(raw, original_reference, torch) -> supported, checks, evidence.
rescale_native_output(actual_HALF, torch) -> (actual_HALF.float()*.5).to(BF16).
The latter is for a future independently source-qualified caller only.

All real query/selected K32/V32/full guarded physical state must be finite,
their FP32 scaling reversible bitwise and every HALF.float exact to scaled
FP32. Full49152 FP32 products, full192 original/scaled/half-roundtrip QK
and scaled logits compare bits. Full1536 ideal scaled AV/2 must exactly
equal original uncast FP32 attention and both finalBF16 values must equal
saved original golden. Reference is the complete unchanged source-bound
numeric002 reference function. Original golden/.005/.99998 remain fixed.
No overflow, underflow, empty-state exception, discarded invalid area,
sampling or nearest-value tolerance is allowed. If K*.5 creates a new
HALF subnormal loss, supported=false; do not submit to FIA.

The pure-stdlib negatives show that this K loss is possible. No actual
scaled-input computation has been run here. Even actual CPU support is
not native arithmetic/tiling/model/long/96 qualification. Existing native
BF16 anchor + scaled FP16 inner0 control still needs a NEW reviewed caller
derived narrowly from the immutable001 entry after actual CPU support.
Do not monkeypatch001 globals, reuse its old source Ref, or change its
direct-half checks. The new caller must retain all guards/table/slot/pointer
checks, raw-before-metric saving and single shared120+60 budget.

Private cold: PY -I -B control.py; stdlib: PY -I -B test_control.py.
CPU-only future command, MAIN after FULL47 release and fresh CPU capacity:
TORCH_DEVICE_BACKEND_AUTOLOAD=0 ADAKV_POWER2_CPU_PRECONDITION_ENABLE=1
ACTUAL_CPU_PY -I -B control.py --execute --raw-ref EXACT_MA0248_RAW_REF_JSON
--reference-ref EXACT_NUMERIC002_SOURCE_REF_JSON --output NEW_ABSENT_SOLE_RW
No device endpoints, CPU1/2GiB proposed/child120/cleanup60, R87 CUT08:06:34Z.
MAIN must source-bind own files/mounts before this pending CLI can run;
there is no owner/source admission in this leaf. Output CPU_POWER2_PRECONDITIONS.pt
and REPORT.json keep all complete intermediate arrays and booleans. NPU,
numerical/matrix96/model/performance/task flags always false.

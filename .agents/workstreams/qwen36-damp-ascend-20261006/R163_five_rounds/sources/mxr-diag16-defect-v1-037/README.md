# Diagonal16 defect correction034 — explicit OFF, not qualified

Actual032 showed that the dominant off-diagonal error is already explained by
bad saved diagonal16 inverses. Tile64/head0/parent32=32: left/right diagonal
errors reach .0165185/.0125299; -(savedD16 @ actualHalfA21 @ savedB16) differs
from E16 by .03354475 at the bad point, while actual offdiag versus that
independent construction has SSE1.11918e-7. Original Q11 SSE is .00495018.
Y16 alone did not repair this. No final-cast anomaly, input-conversion-only
explanation, launch defect or paper failure is inferred.

One conditional stage is added after the existing 16-fractal inverse trick:
R=I-X-A16*X, then Xnew=X+X*R. A16 and X use the actual existing half L1/L0
formats; residual/accumulation are FP32, the residual is written to the same
scratch half L1 tile formerly allocated for Ylo. Five existing Cube GEMMs,
no new UB, L1 remains57344B; all added event sets/waits are balanced in source.
The later block16/32 recursion, actual varlen/tail loader/store, FP16 input,
FP32 workspace, BF16 cast and original9-argument ABI remain unchanged.

New namespace is mxr_diag16_defect_v1. Existing host export names
call_mxr_y16_control / call_mxr_y16_compensated are deliberately stable ABI
roles; they do not indicate the old Y16 arithmetic. New library name is
libmxr_diag16_defect_MEMORY_BASE.so and its actual Ref must bind this MF.
The false branch is source-inverted completely back through028 to the original
40303-byte author implementation. Old028/031 failure artifacts remain immutable.

Prediction/exit: the new actual diagonal16 errors and bad Q11 entry should
decrease. If they do not, this single defect-correction attempt is refuted;
retain full workspace/output and first fault, do not extend Y32 blindly. A
source token-balance proof or synthetic algebra example is not a device proof.

Compile through the already validated030 Devices[] stage: same actual bisheng
MEMORY_BASE/dav-2201 flags,180s compiler/15s nm, complete author/PTO roots RO,
450s total including90cleanup. Then use031's serial physical5→logical0 stage,
300s including120child/90cleanup. The explicit R156 private bindings only
change source/clock/namespace; no new controller or co-run permission exists.
Both stages retain8GiB guest/1CPU/512MiB host/8GiB reserve/4GiB output.

Gate uses the SAME actual captured all4 ranks, rank2 first, original/control/
refined each x3 (at most36 launches). Disabled new FP32/BF16 whole bytes must
equal deployed original; rank2 original must reproduce022 exact workspace and
remain failed. All original full-A FP64 limits (.002/.02/.999), complete
inputs/guards/pointers/finite/determinism and raw-before-rejection remain.

Local stdlib15 passed in6b6c45 (.279s). First7426f8 failed only a Windows
sandbox temporary-fixture write; no algorithm, compiler or device ran. The
actual same660 software, new build, numeric gate and model/graph/task remain
pending. Full-GDN shadow receives no permission unless the new actual gate
passes;129 tokens never grants32768 or multistep/graph/performance scope.

## Clock-contract repair037

Frozen034 adapter.instances still required the old R118 window and would fail
before the first actual launch.037 changes only that production window literal
to R156; build/numeric/derive/generated C++ are byte-identical to034.038 and039
bind this new source without changing existing bounded controller functions.
Test13 executes the actual instances body with real file/Ref/header validation;
only library/solve are controlled software stubs. Current-window success and
old/foreign-window,foreign-build and OFF rejection are covered. No actual build,
NPU, full-GDN, graph or model authority exists from these software controls.

# Split-power2 readout candidate051 — source-only

Actual093a proved all1536 original subnormal precast cells equal
0x00001680 =5760*2^-149; actualrecipe complete and not FTZ zero. Decimal80
independent reference explains original0.0056310889564176 FAIL. Original R3,
REC3, strict and controller failures remain unchanged. This is a production
arithmetic organization change, not a reference or epsilon change.

New production namespace qwen36_deltalog_split_scale_v051 (13arguments), new
debug namespace qwen36_deltalog_split_scale_sidecar_v051 (14arguments). Both
readout headers use q*=exact2^-4, then StoreOutput attn*=16*scale before debug
DataCopy and original BF16 CAST_RINT. LoadBase/key projection/U/base/log/merge
and metadata instructions are mechanically identical to B010 after reversing
the two scaling seams and namespace/debug-only additions (14 source checks).
New libraries are not original B010 or debug015: no artifactRef exists yet.

Exported C++ fixes headDim128 and scale=1.0f/sqrt(float(128)), no scale argument.
Kernel fallback for any other tiling scale is the original early-scaled q path,
not a claim that arbitrary scale supports split scaling. Defaultscale branch
uses exact FP32 constant0.088388346135616302490234375. Every BF16 value times
2^-4 is representable as FP32 (smallest BF16 subnormal2^-133 ->2^-137).
Intermediate query amplitude is smaller than old scale, unlike abandoned full-
late050. This does not prove general FP32 equivalence, cancellation accuracy,
CANN reduction/cast behavior or speed. No uniform relative-error bound near
cancellation is claimed. Original overflow must still be rejected and new
finite-final/intermediate-overflow holdouts must remain finite and pass.

Build uses copied015 actual owned controller, no new resource framework.
Only expected artifact arms/result schema/verifier count change. Original
Devices[], CPU/RAM/reserve,900phase/810child/90cleanup and fixed cutoff remain.
CMake subprocess imports CPU torch for include discovery; parent/guest safety
does not claim that all compiler subprocesses avoid torch. No device needed.
Both fresh DSOs must finish within that original budget; timeout is FAIL,
not license to extend it. COMMANDS binder -> sourceaudit ->compile are exact;
host is python-B (original cohort /proc identity), guest remains-I-B.

meta_abi.py is an explicit sameimage CPU child API, not another controller. It
requires actual completed source-bound two-arm build Ref, loads exact new DSOs,
verifies PrivateUse1+Meta and B1/B16 13/14arg outputs. No synthetic future
library hashes or Meta success. MAIN must run it through an existing owned
Devices[] CPU path. Meta alone does not qualify a real kernel.

PREREGISTER preserves all finite/overflow/subnormal/normal/cancellation/copy/
flush/guard and original thresholds. Next gates: original/new boundary + old
real firstfault + untouched heldout smoke, then complete numeric160, then model.
No bridge/model/PF/ACC targetpin changes before actual newbuild+Meta+NPU proof.
The present packet supplies complete compilable sources/build receiver and
Meta ABI; actual new numerical-owner wiring and every actual result remain
pending. It is not NPU READY or performance-qualified.

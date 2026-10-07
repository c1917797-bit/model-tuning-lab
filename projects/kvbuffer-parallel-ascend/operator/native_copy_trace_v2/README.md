# Native copy-only recurrent trace v2

Independent diagnostic, DEFAULT OFF, not KVBuffer performance code. Old native
trace v1 draft cannot be independently recovered; no old PASS is inherited.

Pinned image660 v0.23/CANN9.1 910B native RGDR arithmetic, queues and UB sizes
are retained. Six explicit observation transformations copy actual FP32 UB
precast and selected token-major updated state. No recomputed FP32 proxy,
feedback, extra UB tensor, cast bias, gate relaxation or global native override.
SOURCE_TRANSFORMS.json contains the reversible complete-header transform and
six exact native tiling method origins. Buffer profile defaults are native1/1.
Runtime UB/core information comes from the actual verified platform SDK API,
with ACL vector-core agreement; no hardcoded UB or "best" manual vStep.

Scope is ONLY saved T16/S19 BF16 q/k/v/beta, FP32 g/state, ND contiguous inputs.
Native seq ABI is non-cumulative [0]+[1]*12+[0]*4. CPU fixture admission must
verify all lengths, unique active slots and in-range indices before NPU.
prepare uploads the native17-field/72-byte tiling once outside capture;
tiling_info copies its cached host bytes for diagnostics outside replay.
Mutable state/precast/selected have explicit schema aliases and disjoint,
aligned storage checks. Undefined inactive native output is not gold.

Required next gates: actual no-device compile, defined export, load/schema/Meta;
then full native-before anchors in eager and NPUGraph, active output/state,
trace conversion, untouched slots, guards, inputs and pointers. Independently
repeat those anchors for only the candidate incoming slot4/head5/V[:32]
substitution. Retain raw before/after/errors even if instrumentation fails.
Trace-source equality is NOT compiled/NPU equality. Native precast remains
UNOBSERVED until these gates pass. Existing B16 step37 failure remains failed,
original output0.00303/state2e-6 limits unchanged. No E2E or task result.

Derived native header copyright notices remain in source; use the existing
CANN source license unchanged. Any independently named ABI and source identity
must be verified by the consumer; never wrap a new receipt as a legacy PASS.

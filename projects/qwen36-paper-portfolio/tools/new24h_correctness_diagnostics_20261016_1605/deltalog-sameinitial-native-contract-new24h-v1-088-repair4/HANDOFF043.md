# DL043 — NEW mixed actual-FP32-precast empirical experiment

Prepared only. No deployment, same-image execution, device execution, numerical
qualification, model qualification, performance result, or task score exists.
035R4 and 013 failures remain failures. This is not an epsilon adjustment.

## Frozen scope

Unchanged B010 production DSO `298749129c8586ecea56cb6076c435631b6fbef4b4e7757636ff87a4ec09abf7`;
actual already-built015 diagnostic DSO
`0d3400929262a16f6485cebc3fcf7e683fbff335af193df4754875091b915e2c`.
The latter only runs on cloned inputs/state and never supplies production output.
Both are loaded/called through actual Meta before NPU admission. Build/source
receipts are exact read-only dependencies, not guessed future PASS.

Primary readout predicate is the original016 `precast.py` unchanged: EACH request
actual FP32 sidecar versus independent CPU64 has peak <= .00303 AND relative L2
<= 2^-13, and actual production BF16 bytes equal direct integer RNE(sidecar),
including signed zero. Zero reference requires exact zero; nonfinite rejects.
Original FP32 state7.92e-7, flush/copy/reset/slot-reuse/continuity/input/guard gates
stay. Normal native prefill output/state peer gates remain hard. Decode's old
ideal-BF16 point and native-BF16 point output errors remain explicitly diagnostic,
with their old pass flags, not relabelled. New primary scope is empirical tested
inputs, NOT a CANN Exp theorem or a whole independent trajectory.

Full matrix remains B1/B16 x160 mixed steps, four dead-flush and four native-copy
records; smoke is the same matrix x16. New mixed seed2610154301 is pinned in
fixture, independent initial-anchor reconstruction and contract. Reset steps,
roll/slot swaps, copy lengths1/7, dead NaN/partial-live behavior stay unchanged.
Every production decode (including the 18 flush/copy setup calls) has paired
debug actual six-state/output/input/sequence/slot/pointer and sidecar-redzone
evidence. Seven additional real NPU controls: normal/tiny/subnormal/+0/-0/
cancellation/overflow. Finite cases must satisfy the same predicate; overflow
must actually trigger nonfinite rejection. No unsupported case is silently
accepted or called qualified.

## Actual code and controls

`sidecar_capture.py`: actual015 call after production on prior cloned state;
`per_request_increment.py`: actual captured inputs and active post-state join to
whole-core raw and independent oracle; `sidecar_audit.py`: all paired call bytes
and non-mixed local recurrence; `npu_controls.py`: actual operator boundary calls.
`meta043.py`: real dual DSO Meta/PrivateUse1 calls.
`raw_reader_entry.py`: hydrates lossless raw before old strict/domain consumers.
`raw_codec.py`: exact dtype/shape/content-addressed slot chunks, no lossy codec or
predicted compression rate. Old oracle/strict consumers/math files retain exact
original bytes; producer/host edits have executable inverse with included
original fixtures. Historical tests are retained; tests naming old035 explicitly
exercise its retained original predicate, not a fabricated sidecar.

Local full discovery: **73 tests PASS, 259.576 seconds**. Includes actual new consumer function
with saved CPU fixtures (not NPU evidence), wrong scale/slot/sidecar rejection,
head/order/cast/zero/NaN controls, B16 masking, corrupt blob, byte preservation
including dead NaN and signed zero, actual-cap rejection and default-OFF CLIs.
Initial inherited discovery failures and the codec test budget mistake were
corrected before seal; no actual device experiment was attempted.

## Source and invocation

Planned source root:
`/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-mixed-precast-new48h-v1-043-repair3`.
All mutable output phases MUST be fresh direct children of the one exact root:
`/opt/host/vnf/austinov/deltalog-mixed-precast-new48h-043-repair3`.
MAIN must independently resolve/create/verify its actual filesystem free space;
same-filesystem path changes do not create space. No existing raw is deleted.

`run043.py` provides bind -> sourceaudit -> cpu -> numeric16 -> numeric160;
`COMMANDS043.json` is typed argument arrays. Binding consumes the actual035R4
source ONLY to obtain its actual unchanged022/B010 component source+CPU receipt;
it does NOT consume the failed035 numeric result as PASS. CPU/smoke Ref3 values
must be real and source-bound. No model/accuracy receiver consumes043 yet.

Budget unchanged: guest8GiB, host512MiB, ordinary reserve8GiB; owner2880s,
numeric1800s (B1<=600/B16<=1200), independent CPU600s, cleanup90s, fixed
2026-10-16 07:18:17Z. Raw cap32GiB + filesystem reserve1GiB enforced on actual
new bytes. The codec deduplicates EXACT slot bytes only: paired debug-after
equals production-after, inactive chunks equal captured before, and selected
decode chunks equal whole-core after (independently checked). Any genuinely new
chunk is charged in full, before write. New sidecar readout itself costs at most
345 * 16 *12*128*4 = 33,914,880 bytes (conservative all calls B16); all unique
states remain retained. There is no measured NPU/CPU timing or actual full raw
size yet; a budget overrun fails this experiment, not an implicit extension.

## Preparation repair1 (original043 source-only draft retained)

The initial preparation collector omitted `debug_before` while consumers required
it. No043 device experiment or deployed source existed. Repair1 records an
independent real CPU snapshot of each actual cloned device operand BEFORE either
operator executes, rather than aliasing `before`. `test_collector_abi.py` executes
the real collector with explicitly CPU-only synthetic callables, then real
sidecar_audit and per_request_metrics, confirms every emitted record key and
independent snapshot storage, and rejects the original missing-key record and
corrupted cloned-before. These are software ABI controls, not NPU/kernel proof.

## Preparation repair2 — overflow cannot exempt state correctness

An independent original-function CPU counterexample proved repair1 accepted
expected-overflow readout with a finite but completely wrong represented state:
state_errors=[1.0], passed=True. Repair2 adds ONLY the missing state conjunction
to the expected-overflow branch: every state error must remain finite and <= the
original7.92e-7. Finite-state checks, normal/tiny/subnormal/zero/cancellation
predicates, seed, libraries, complete matrix and budgets are unchanged. All old
preparation sources remain retained; none had a real NPU execution.

The new test_aggregate_controls executes actual npu_controls.run→Capture→codec
and the unmodified control-aggregation AST block of actual domain_consumer.run
with explicit CPU allocation and synthetic readout instrumentation. It tests
7controls and57 paired-call smoke cardinality, definite FTZ readout rejection
while state remains correct, NaN state hard rejection, and the original finite
wrong-state counterexample both at audit and aggregate entry. This is software
ABI/gate evidence only, not a measured Ascend FTZ or kernel result.

## Smallest subsequent MODEL change (not implemented/qualified here)

Reuse existing actual model026/036 diagnostic tensor observer only. At the real
provider decode seam, install this same capture wrapper (default OFF), write
actual call Ref into the layer/frame capture, and consume via the same predicate
against that model frame's independent CPU64 ledger. Keep real mixed input/
metadata/slot/epoch joins and actual4-rank x48-prefix coverage. A local-component
043 PASS cannot replace the model tensor observer/trajectory/state gate. Do not
insert the sidecar or diagnostic wrapper into timed production PF/accuracy;
production remains original B010 once its own source/dispatch/qualification
evidence is valid. This successor still needs actual model, E2E and task tests.

# MXR084 saved2K prefill three-arm diagnostic

Source-only, default OFF. No model/old gate change, no NPU executed. First exact
raw is actual073R6 rank0 layer0 frame000 (32140793 bytes / 394b22b1...); four
other failing layers are not silently added to this experiment.

## Actual executable guest path

`guest_core.py --source-audit` reopens exact source/sidecar/raw/helper closure
without Torch/native imports. `--cpu-preflight` loads the actual shared-storage
raw with the original073 lossless codec, verifies every leaf and actual full
frame ABI in a Devices[] Torch3.12 container. Neither stage queries HAL or
imports vLLM. Runtime uses original079 package-first device properties, vendor
registration, device dispatcher proof, explicit source-pinned pyACL bootstrap
and the exact069 PCP1 helper (not a fake distributed object).

After singleton tiny arithmetic, write DEVICE.json and wait for MAIN_ARM.json.
MAIN must adapt the reviewed081 owner's schema from079 to084, preserving real
SMI/PID/start/cgroup/argv join; guest cannot grant physical-card authority.
Physical4–7 is selected only in a new MAIN plan. No DL storage authorization is
implied for MXR: MAIN must select/approve its separate exact output leaf and
check a fresh common resource ledger. No new controller is included.

Plan: {schema:mxr.prefill-three-arm-plan/v084,source:<this source Ref>,raw:<exact
actual raw Ref>,physical:<MAIN4..7>,logical:0,qualification:false}.
ARM: {schema:mxr.prefill-three-arm-arm/v084,pid:<actual guest>,plan_sha256:<plan
SHA>,physical:<same physical>}.
STAGE_RESULT schema mxr.prefill-three-arm-stage/v084 includes source, authority,
plan, raw, primary, result, NPU, qualified:false, old_failures_unchanged:true.
On success result.rows is candidate-first exactly saved_candidate/native/
cpu64_cast; result.raw_bytes <=256MiB; candidate_anchor_bitwise and same_actual_A_G
are true. MAIN's 081 receive/closure must be narrowly updated for these fields;
no foreign old079 row-count6 or retained069-producer contract may be inherited.
Stage failure writes FAILURE.json and primary, never a success qualification.

## Anchored calculation and observables

All arms run the exact official chunk on the same saved actual normalized
q/k/v/g/beta/initial/cu/scale with normalization OFF (it already occurred in the
real model). All actual generated A32 matrices must equal the saved A32 bytes.
Saved candidate B is injected into the first arm, without running a different
candidate solver. Its whole output and final state must exactly reproduce the
saved real044 model result BEFORE either other arm runs. If they do not, stop
and preserve failure: no unanchored attribution.

Arm2 uses official native solve on actual A32. Arm3 independently computes FP64
inverse from that same actual A32 through the original metrics implementation,
then casts it to BF16. This is an operational FP64-inverse cast diagnostic, not
a proof of exact-real inverse rounding. It never substitutes CPU-reconstructed
A for the actual native A. Shared G and A must be bitwise equal between arms.

Observe real cumsum G, A/B, actual WY outputs, and the official H API's full
BF16 Hentry (32chunks/head), BF16 Vnew and final FP32 Hend, then full O/state.
Native H storage is head-major then chunk-major according to the pinned native
hOffset formula. Raw retains its original API shape before consumer reshapes.
The intermediate31 unrounded FP32 Hend values are NOT API outputs and are not
claimed captured. Next chunk BF16 Hentry is observed instead. Exact first
divergence within a hidden vector epilogue remains unresolved by this packet.

Every intercepted API is restored in finally. All operands are fingerprinted
before/after. Same HF32OFF policy source as044 is explicitly applied/read back.
Existing source-to-DSO caveat remains; actual extension/schema proof is saved.
No per-frame hardcoded numerical adjustment or new threshold exists.

## Independent consumer / bounds

`consume.py --execute` only in Devices[], no Torch NPU backend autoload. It
reopens all3 exact raw Refs, original frame, checks candidate anchoring and
sameactualA/G, independently computes inverse(actualA), and emits per-chunk
API differences and first differing chunk for B/W/U/Hentry/Vnew/O, plus final
state. It does not grant component/model/performance/task qualification.

8GiB guest / .5GiB host / 8GiB reserve; 1 guest CPU, netnone, capdropALL,
read-only source/input, one fresh output RW. NPU child600, CPUchild600,
cleanup90, each owned-stage whole900. Raw hardcap256MiB and whole output1GiB.
Three whole2K API traces are about160MiB tensor payload; the hardcap is checked
after every exclusive fsynced raw, and overflow fails rather than dropping
evidence. MAIN schedules CPU and NPU stages serially against the real ledger.

Eight actual local software controls pass (cold -I CLI, no native import at
module load, first-anchor failure stops later arms, exact arm ordering,
signed-zero and dtype negative anchors, actual-A source path, scope claims).
These are software-only, not mounted-image or NPU execution. The true mounted
frame CPU preflight and owner adapter are still pending. COMMANDS are guest
commands, not a claim of a ready owned host launch.

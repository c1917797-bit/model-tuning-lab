# 043repair3 — explicit collection policy only, source prepared / no NPU PASS

Actual043repair2 numeric16 stopped at B16 step9, after its raw and sidecar were
saved, because native_fixture still used whole-core BF16 output-point .00303 as
a producer early-stop gate. This was BEFORE an independent actual-precast/domain
verdict; consume_pair then correctly rejected producer.primary != null. Original
R2 owner, partial raw, first failure and strict FAIL are unchanged.

R3 changes no input, seed2610154301, native/DeltaLog arithmetic, B010/015 DSO,
precast .00303 peak AND 2^-13 L2 AND exact direct-integer RNE, or state7.92e-7.
Only the explicit producer Diagnostics opt-in defers the old BF16 point stop.
Without that exact bool opt-in, the old point stop remains. Finite/state and all
byte/pointer/guard/input/owner/lifecycle checks remain hard; nonfinite scalar
errors are explicitly rejected. Every raw and old point metric/verdict is kept.
This permits collecting evidence, NOT passing an algorithm or redefining old FAIL.

The actual CPU pair frontdoor additionally requires all mixed steps per batch,
four flush/four copy records, exact7 controls and 2*steps+25 unique sidecar refs
(345 at160; 320 mixed). Partial collection cannot be passed to complete admission.
Original strict consumer runs unchanged first. Actual independent FP32/domain
failure leaves diagnostic_capture_complete/domain_checks_pass false, with model,
performance and qualification false. New source/owner/16/full160 are mandatory.

test_collection_contract executes the real native_fixture guard IF, real
producer Diagnostics class/step/raw retention, actual per_request_metrics and
real consume_pair aggregation in CPU software controls. It tests old point FAIL
plus new-precast FAIL, hard state/nonfinite/all-byte flags, old/default stop,
partial/duplicate/missing345 and old qualification rejection. Existing same-image
CPU entry runs this exact test file before any NPU work and links its receipt.
Temporary software records are never an actual NPU receipt.

COLLECTION_REPAIR3_INVERSE.json + fixtures_repair3 retain exact R2 source. The
declared small collection/control additions invert byte-exactly; original043
inverse checks compose this inverse before their historical035 transformation.
domain_consumer differs only in exact producer/fixture/new-policy source pins;
its numerical functions and reference contract are unchanged.

Existing controlled CPU→16→160 owner, resources/cleanup/cutoff and physical5
remain. New output is the exact independent opt root ending043-repair3, not the
15GiB cache filesystem. No remote write/container/build/NPU/Git was performed by
the preparer. MODEL/PF/ACC frozen predecessors must receive new exact pins in
separate successors only after this source is reviewed; future PASS is refused.

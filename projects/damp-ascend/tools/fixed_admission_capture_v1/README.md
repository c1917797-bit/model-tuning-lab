# Fixed-admission capture parity diagnostic — PREPARED, NOT NPU-PASSED

This NEW default-OFF packet isolates the native admission-shape confound discovered
in the failed full TRAIN capture. It does not repair or relax the frozen collector,
issue a SOURCE_LOCK, fit plans, measure throughput, or test task accuracy.

Protocol: one publisher TRAIN prompt (math-fit-02, exactly1024 existing token IDs),
one request admitted by the unchanged offline LLM.generate, max_num_seqs=1,
33 fixed output tokens, three fresh sequential arms OFF-A/OFF-B/ON. All arms use
the same common native-code-object observer, TP4 physical4–7 mapped logical0–3,
eager/prefixOFF/chunked-prefillOFF, seed0/temperature0/ignoreEOS. Native actual
prefill1024 plus32 single-token decode calls are checked, not inferred from C1.
The ON-only sole algorithm-side change remains the old frozen capture.register().
OFF/OFF divergence stops before ON. Short pass is not full36×4096 noninterference.

## Exact source and import route

The unchanged collector run forces plugin name damp_capture. Adding a second
same-name dist-info would be ambiguous. Explicit execution creates a Git-external
module-only overlay: symlink the frozen damp_capture module (not its dist-info),
symlink this diagnostic package, and add one new diagnostic dist-info whose
damp_capture entrypoint points to damp_admission_diagnostic:register.
No original package/image/source is edited. The no-device preflight checks unique
entrypoint, actual module resolution, defaultOFF imports, transitive repository
hashes and five immutable image source files before any canary/model operation.
Actual image preflight and actual native observer/frame ABI are still pending.

Register saves ORIGINAL donor/receiver core and runner code objects, source/code/
globals ownership, calls original collector register exactly once, then wraps only
the outer runner for supervised observation. It does NOT rebind the GDN core or
gating a second time. sys/threading profile callback observes the original native
core code object, including ON's call into that original code. All48 real Qwen GDN
receiver instances on every rank are checked. The native return object is returned
unchanged. Callback transfer/I/O/return(None)-unwind errors are deferred; an
original native exception is re-raised unchanged even if evidence writing fails.
A native successful call with failed/missing/superseded trace coverage is rejected.

## Bounded diagnostic evidence

Every rank records all48 layers for all33 real turns: native admission CPU mirrors,
original GDN argument layout and actual used-token bytes (not uninitialized pad),
actual selected slot, before/after selected FP32 SSM, separate conv state,
native g/beta/core output, cache pointers/storage geometry, exact call coverage
and original-return commit. Only true recurrent SSM before is compared with the
previous successful after; conv is separately recorded, not mislabeled as SSM.
Source/observed-state records are not independent mathematical golden evidence.

Raw CPU bytes are retained BEFORE finite assertions. Initial states and after
states are saved once; matching next-before states reference prior raw bytes.
Unexpected selected-state changes are independently saved. No raw file deletion.
Native pointers must remain stable within each arm; absolute virtual addresses
are not compared across fresh processes. Cross-arm slots/layout/parameters and
raw hashes are compared. Earliest observed GDN input/state/output seam is reported;
FA, model hidden states and logits are not observed as a complete causal chain.
Selected-slot evidence does NOT claim a full unselected-state/guard/lifecycle proof.

Total raw hard cap20GiB is split into12 equal rank/arm allocations; expected raw
is near19.5GiB and may fail closed if actual ABI/dtype/capacity increases it.
This is an upper bound, not a target to fill. Forty-five minutes TOTAL includes
cold starts and leaves90seconds for owned cleanup. CPU comparison checks remaining
budget before and after each bounded33×48×4 phase. An over-budget/incomplete result
is retained, not marked pass. Host ordinary memory must be at least64GiB plus8GiB
reserve; free disk≥40GiB. Containers are nonprivileged/cap-dropALL,64GiB cgroup,
8GiBshm,6CPUs, exact repo/modelRO/resultRW/inputRO plus driverRO, no retry/deletion.
The separate no-device preflight uses the SAME mounts/overlay/bootstrap but1CPU,
2GiB memory+swap,1GiBshm and networkNONE. Engine capacity is freshly observed:
known live allT4CPU/32GiB + preflight1CPU/2GiB + reserve1CPU/8GiB; formal6CPU/64GiB
requires allT actual terminal and four exact stopped/PID0 identities, then72GiB
MemAvailable. CPU quota is not a guarantee about future external CPU consumption.
External pure-sleep caps (including unbounded0) are recorded, not summed. Actual
non-sleep high CPU/RAM or identity changes fail closed and only this new container
is stopped. Full inspect checks devices, five bind mounts, quotas/security/network.
Every10seconds during child execution we monitor actual own cgroup/RAM and external
process identities; raw process arguments/environment credentials are not logged.
Only the exact newly nonce-owned container ID is stopped and retained in finally.

## Scope and pending gates

Software fixture/AST/import/defaultCLI checks do not establish actual frame locals,
native source registration/loaded maps, shapes, output determinism or NPU numerical
correctness. Target no-device preflight, canary and all three actual arms are MAIN's
exclusive actions. No performance/accuracy/graph/lifecycle claim is admitted.
The original failed full36 capture, selected-source failures, collector26 and
shared lifecycle sources remain byte-for-byte unchanged. No SOURCE_LOCK is created
in any success/failure branch. A short PASS cannot authorize final192 plans.

## Environment and prior scheduling authority

The NEW controller AST-extracts only the reviewed BOOTSTRAP literal from frozen
prefill_float_dispatch_v1/dispatch.py (SHA094defb9…), never calls its execute path
or accepts its historical parent guard as proof. Exact original toolkit/IR/ATB
shell sources initialize CANN; only then is the module-only overlay prepended.
Target preflight and each arm retain actual whitelist environment/source hashes.
No-device preflight verifies actual CPython3.12 public profile APIs, all NEW stdlib
behavior tests, unique metadata and runtime source bytes; it does not import Torch
or register native workers, and cannot prove original native frame ABI.
Formal --execute additionally SHA-binds the original MAIN exec06a0 terminal bytes
(peer/direct/completed/noncancelled/nontimedOut) and four original actual device-proof Refs, then fresh immutable stopped identities.
A nonzero prior exit only admits scheduling release, NOT numerical success.

## Narrow protected0–3 resident policy correction

MAIN direct read-only operation exec-00000000000006c6 actually reproduced the old
policy ValueError: known0–3 baseline ID eeb65fd29e054783ce8ba6f9165ea54d38a2575f170225ddf11b3e7584b9f12a,
name /qwen36_hypic2048_quality41984_baseline_npu0_3_v1, image660ce23a…,
26.76GiB observed Docker memory usage and7.20%CPU. Original tool receipt is retained
by MAIN; no future file/path/SHA is asserted here. This is a source-policy repair,
not DAMP/NPU/accuracy/performance evidence.

Only that exact ID/name/image/nonprivileged/same0–3+common device map and actual
vllm/python3/VLLM::EngineCor/VLLM::Worker_TP process set is known-protected.
Its already resident memory is reflected in MemAvailable, not counted twice or
rejected at2GiB. CPU<=50% remains. Initial resources retain the actual process PID/
name set and memory usage baseline; every monitor requires unchanged identities/
maps/processes and growth<=4GiB (half the8GiB reserve). Unknown non-sleep tasks
retain2GiB/50% rejection. Current allT classification,42/72GiB initial requirements,
our cgroups and8GiB live ordinary reserve remain unchanged. Any anomaly stops
ONLY the newly owned diagnostic container;0–3 is never stopped or modified.
Observed protection is not an external hard-cap or future-resource guarantee.

# KVBuffer true-T2–15 MAIN launch preparation (in-memory draft only)

Proposed publication location: `projects/kvbuffer-parallel-ascend/tools/middle_batch_launch_v1/READY.md`.
Do not add files under middle_batch_gate_v1: its reviewed runtime identity is exactly run.py SHA16ed62857871e4576694802bd45afb2a3ec70d726f90f2687860689b92ef3a10.

No actual formal start, MAIN input receipt, container, device proof or NPU result is issued by this preparation.
Original 49 sources, candidate SO, old receipts and the live MA070e sources remain frozen.

## Reviewed program and real prerequisites

Latest exact in-memory program is MA0775 original record.args[3], SHA12b63553f190b5eefe8f0205a21d23f765929091b09fa551dc8a03ee376552a4 (339 lines/29782 bytes).
Original d45d/MA0768 and 3139/MA076d drafts, README/MA0770, and actual software failures MA0764/0767 remain unchanged. Latest MA0775 is 170 stdlib contract checks, not runtime/NPU permission.

MA075b actual same-image consumer/middle source preparation and MA0762 actual no-device 14-positive Meta are prerequisites, not numerical PASS.
Meta14 report:
 /cache/cch/qwen36-kvbuffer-parallel-20261006/preflight-middle-meta14-v1/results/report.json
 SHA1c417ac0cae44e11842bd2a9434acd1cf537568f2bf19878ebb19dca64c65e75.
Its schema field is the actual Torch decode schema (not a kvbp label), status actual_14_positive_Meta_pass, meta T2..15, source49 before/after equal, mapped SO0e7c64…, npu/graph/physical-ND/service false. MAIN must retain its actual original terminal and inspected no-device lease. The new program also requires an explicit middle_meta14 Ref from MAIN and uses the original c.read_ref byte/SHA guard to actually read this report before creating output or invoking Docker. It checks all14 ordered T/slots/shape/BF16 rows and the producer's whole-matrix output_alias_checks field (not invented per-row fields), both exact49 source maps, actual canonical candidate loaded SO/build digests, original Torch decode/prepare schemas, real image versions, ordered completion, original scope/false flags and unimplemented-negative limitation. This is not device authority. The checked Ref is recorded in PROGRAM.json, per-worker identity evidence and CHILD.json. Default OFF and --source-audit do not consume/authorize it.
Worker deliberately keeps the old immutable Meta receipt (SHA2765f4…) for its unchanged schema binding; do not overwrite/relabel it.

Actual MA070e original terminal + source-bound release inputs MUST exist before launch. Completed nonzero is release-only, never numerical PASS; running/cancelled/timed-out is refused.
The four original owned containers must already have actual Running=false/Pid0. No old/unrelated container is stopped.
Producer source paths:
 independent_allT_dispatch_v1/controller.py:196–217 writes root/admission.json;
 :220 writes launch/EXECUTION_PLAN.json;
 :246–250 writes launch/STOP_RETAIN.json using frozen allT host.stop_owned :407–414.
STOP_RETAIN exact rows are {id,name,status,deleted:false}; admission.cards has container_id/name/create_argv_sha256; plan.shards has actual balanced batches and docker_create_argv.
The draft checks the actual MA070e balanced groups, not old contiguous groups.

## MAIN-issued inputs, clock and actual command

MAIN supplies one immutable, hash-bound JSON with:
 main_approved=true, run_slug, main_program_sha256;
 formal_start_utc, deadline_utc;
 phase_seconds keys "4","5","6","7" (each preregistered 1800..10800);
 release_terminal, release_plan, release_admission, release_stops (each exact {path,sha256});
 release_expected={command,args,cwd} from the original MA070e execution;
 middle_meta14={path:"/cache/cch/qwen36-kvbuffer-parallel-20261006/preflight-middle-meta14-v1/results/report.json",sha256:"1c417ac0cae44e11842bd2a9434acd1cf537568f2bf19878ebb19dca64c65e75"}.
Missing/other-path/other-SHA/old B1B16 Meta refuses launch before mkdir or Docker.

The preparation does not issue these values.
KVBuffer has its own MAIN-recorded actual formal-start clock, deadline-start<=24h and deadline<=2026-10-09T11:17:31Z.
DAMP's original 2026-10-07T08:48:03Z clock is not extended or reset.
Remaining time must cover setup600 + max registered single phase + cleanup180. Each worker phase is one attempt, no timeout extension/retry/shrinking.

MAIN source-only argv (no Torch/Docker/NPU or files):
 /usr/bin/python3 -B -c EXACT_MA0775_record_args3 --source-audit

Actual MAIN a_exec (only after review/release/fresh-resource admission):
 command=/usr/bin/python3
 args=["-B","-c",EXACT_MA0775_record_args3,"--execute","--inputs",ACTUAL_INPUT_PATH,"--inputs-sha256",ACTUAL_INPUT_SHA]
 cwd=/opt/host/vnf/austinov/model-tuning-lab
 explicit environment KVBUFFER_MIDDLE_MAIN_EXECUTE=1, PYTHONDONTWRITEBYTECODE=1.
Outer operation timeout must cover the actual setup/phase/cleanup budget; no guessed parent operation success/ref may be substituted.

## Four true-T groups and numerical scope

 card4 T[2,14,15], 12 cases/1920 feedback steps;
 card5 T[7,11,13], 12 cases/1920;
 card6 T[3,4,9,12], 16 cases/2560;
 card7 T[5,6,8,10], 16 cases/2560.
Total14 trueT /56 cases/8960 feedback steps.
Each T uses the frozen original run_case: eager trial0 + graph trials0/1/2, all160 steps; active=T, S=T+3, reset steps64/112, capacity16 real flush, no PAD16.
Original complete/per-head FP32-state L2<=2e-6 and output<=.00303, all complete-state/log/input/guard/pointer/untouched/finite gates remain unchanged.
Actual frozen validate_cases is generic T here; only true T16 graph uses its original padding schedule.
B1/B16 existing reports are not replaced or forged.
This does not cover model48-layer lifecycle, mixed prefill/native materialization, C16 scheduler transitions, paired E2E/TTFT/TPOT or task accuracy.

## Exact resource/mount contract

Joint four1CPU8GiB no-swap workers + ordinaryRAM8GiB reserve =40GiB; Docker NCPU>=5 including host reserve.
One nonprivileged owned worker per physical4..7->logical0, plus only davinci_manager/devmm_svm/hisi_hdc control nodes; cap-drop ALL, no-new-privileges, network none.
Protect0–3 by actual PID/cgroup/start-tick fingerprint throughout; never send their processes signals.
Refuse every unknown live model-tuning-lab owner. No oldowner relabeling or unilateral concurrent-monitor relaxation.

Worker mounts:
 canonical repo -> same canonical repo RO;
 /cache/cch/qwen36-kvbuffer-parallel-20261006/build-p1-v1 -> /kvbuffer-results/build-p1-v1 RO;
 /cache/cch/qwen36-kvbuffer-parallel-20261006/meta-p1-v1 -> /kvbuffer-results/meta-p1-v1 RO;
 fresh cardN/results -> /kvbuffer-results RW (only output writer);
 fresh cardN/launch -> /kvbuffer-launch RO;
 /usr/local/Ascend/driver -> same path RO.
No credentials in argv/environment/repo.
No additional source under middle_batch_gate_v1; kernel/native image source SHA is checked before canary.

Starter is exact /bin/bash -c "exec sleep infinity".
Every numerical exec uses the existing CANN/ATB WAIT bootstrap explicitly (startup-shell env does not carry into docker exec).
Inner executable is /usr/local/python3.12.13/bin/python3 -B run.py --execute --batches GROUP --physical-device CARD --identity /kvbuffer-launch/identity.json --output-dir /kvbuffer-results/gate.

MAIN first observes the exact waiting bash PID/NSpid/cgroup/start_ticks/argv, fresh host idle snapshot and separate canary.
Only then MAIN writes exclusive identity/RELEASE (fresh<=600s).
The separate canary is NOT the numerical process; final PASS requires actual NPU process PID to equal waiting exec PID, same start_ticks, exact new numerical Python argv and physical card.

Source-only child audit (can run in the existing no-device image with RO build/meta aliases):
 /usr/local/python3.12.13/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/middle_batch_gate_v1/run.py --audit-only --batches GROUP --physical-device CARD
Host audit adds --library HOST_BUILD_SO --build-receipt HOST_BUILD_RECEIPT --meta-receipt HOST_OLD_META.
Actual four host audit CLIs passed MA0756; they are not loaded-library/device proof.

## Evidence costs, budgets and failure handling

Frozen oracle saves complete unanalysed before/after/native/input/output/guard/pointer raw tensors before each metric/assertion.
Only an already-passed, exact hashed single raw-step file is unlinked; failed files remain. Expected peak<=one current raw per worker, not cumulative14T storage.
Cumulative raw write roughly499.83GiB; raw plus known metric D2H roughly801.70GiB. This is cumulative transfer/I/O, not simultaneous residency or performance.
1920/1920/2560/2560 native calls per card;1956/1956/2608/2608 candidate eager/capture/warmup calls.
Original three accumulated report writes/step remain O(n²); no source rewrite is hidden in this launch.

Explicit serializer-policy raw ceilings bytes: card4 110649344; card5 100212736; card6 94994432; card7 84557824.
At10800s, disk budget15288582144 bytes (14.239GiB):8GiB reserve +4 raw ceilings +4x64MiB reports +360x4x4MiB audit allowance. Recommend at least16GiB fresh disk. These allowances are fail-closed policy, not measured upper bounds.
Sample ordinaryRAM availability and disk reads are historical diagnostics, never future resource admission.
No claim10800s suffices: MAIN must preregister using actual first-case cost evidence, without silently shortening/resetting the matrix/deadline.

All original stdout/stderr/argv/exit/raw report hashes retained before interpreting PASS.
Secondary evidence/cleanup errors are recorded, never replace the original primary exception.
Exactly owned new containers stopped/retained only; no delete/no external kill/no create-ID guess. Cleanup180reserve, one cleanup attempt.
A numerical failure or bounded timeout is retained, not a paper-wide no-go.
The final marker is component-only, requires all original guards/cases, actual source/maps/PID and stopped leases; external genuine AWMCP terminal/refs remain MAIN-issued authority.
No serving/performance flag is upgraded by this packet.

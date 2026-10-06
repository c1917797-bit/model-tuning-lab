# KVBuffer two real MAIN-operation dispatch (prepared, default OFF)

This NEW packet prepares existing split_gate_v1 unchanged: B1 physical5 and B16 physical6, four eager/graph cases each, 160 changing feedback steps per case (1280 steps total). It is not NPU PASS, paper success, graph-service admission or E2E/accuracy evidence. Preparation does not start the paper's formal 24h clock.

The old aggregate authority requires two distinct actual AWMCP operation IDs and one exact child marker in each original stdout. Therefore MAIN uses prepare-joint once, then two distinct real run-arm AWMCP operations. There is no shim/runpy and no fabricated image-Python argv or split stdout. The frozen bridge remains unchanged; MAIN supplies each original outer terminal Ref, peer/op/command/argv/cwd and original stdout/stderr after that operation really finishes.

## Required MAIN input (no simulated future authority)

--inputs is an externally MAIN-approved JSON with exact keys: parent_operation Ref for original MA06a0, parent_expected {command,args,cwd} independently copied from its actual launch, run_slug, phase_seconds {"1":seconds,"16":seconds}, formal_start_utc, deadline_utc, main_approved:true, forbid_other_owned_jobs:true. Every phase budget is explicit (1800..10800s). Remaining time must include setup600s, max phase and cleanup180s, and the supplied real formal clock is <=24h. The tool never invents a deadline or extends one. MAIN must independently judge costs: each arm640 genuine native calls, many D2H/CPU metrics and ~12.40/59.00GiB cumulative raw writes; no measured full-matrix runtime exists and 3600 is not a proven bound.

Missing original terminal, exact four stopped IDs, source freeze, resource proofs or clocks rejects. A completed nonzero parent with consistent "exit code" error permits resource release, never promotes that run to PASS. Unknown/cancelled/timed-out/nonterminal parent rejects.

## Three commands (MAIN only, no background autoscheduler)

1. source-audit --packet-sha256 ACTUAL_PACKET_SHA (stdlib only)
2. KVBUFFER_SPLIT_DISPATCH_EXECUTE=1 controller.py prepare-joint --execute --packet-sha256 ACTUAL_PACKET_SHA --inputs ACTUAL_INPUT_PATH --inputs-sha256 ACTUAL_INPUT_SHA
3. Two independent real MAIN a_exec calls:
   controller.py run-arm --execute --batch 1|16 --packet-sha256 ACTUAL_PACKET_SHA --joint ACTUAL_JOINT_PATH --joint-sha256 ACTUAL_JOINT_SHA
   with KVBUFFER_SPLIT_DISPATCH_EXECUTE=1. The MAIN tool timeout must exceed the explicit phase/setup/cleanup budget; tool-side timeout is not a numerical result.

Default CLI emits OFF/pending without reading device state or creating anything. All paths, actual argv and source/artifact hashes are source-bound; MAIN must fully review then execute. No commands in this document have been run on devices.

prepare-joint creates two new bounded 1CPU/8GiB/no-swap/no-network/cap-drop/nonprivileged single-card sleep containers after fresh checks and stopped-parent inspection. It emits actual prepared IDs, not live readiness or canary PASS. run-arm rechecks source and stopped parent, exact own/peer identity and live joint24GiB ordinaryRAM +3 CPU capability, disk8GiB base reserve plus source-shaped two active raw ceilings and conservative remaining30s audit allowance, and mount2560 policy reserve. Unknown live model-tuning-lab owners reject without stopping them. Other containers merely declaring devices are not used as process evidence; actual target processes, HBM/AICore and tiny canary govern device admission. 0–3 are only fingerprinted/read, never stopped. No HugeTLB changes, no broad filesystem RW mounts. Repo/build/meta/native driver/launch are RO; only fresh per-arm results are RW.

## Actual process/identity seam

Canary is a separate child, not the numerical gate. The actual docker exec invokes waiting bash -> exec exact imagePython -B oldRUNNER. Prelaunch hostPID/NSpid/cgroup evidence is explicitly wait-bash, not observed native NPU PID. Identity and release are exclusive new files; release follows actual source/canary/resource/inspect checks. Success requires later actual NPU process-table PID equals the wait PID, stable start ticks/cgroup/NSpid, exact Python/RUNNER argv and expected physical5/6. If the required observation is missed, no child marker/PASS is emitted.

Both arms use true B1/B16, no PAD/fake batches. Each arm cleans only its own exact ID after name/image/labels/device/mount checks, retains it and originals; no automatic retry. Peer is allowed only under exact joint ownership. One arm failing cannot make the other or aggregate PASS. Exclusive ARM_CLAIM and fresh output/launch names prevent retries/overwrites. Once prepare returns, MAIN owns two idle retained containers even if no run-arm is started; this tool has no hidden expiry or cross-arm cleanup.

Raw subprocess streams/receipts precede parsing. Saving/cleanup errors are secondary stderr records and must not replace original execution exceptions. Early CLI/source/config failures can happen before a new audit directory exists: actual AWMCP stdout/stderr is then the durable boundary, not a falsely claimed child report. A child may fail before original report mkdir, or the frozen child finally may mask its earlier numerical error; this parent preserves original Popen streams/outcome but cannot retroactively repair frozen history. Missing/failed reports reject, raw failure artifacts are retained, no unchanged retry.

Successful child schema is the frozen kvbp.split-child-execution/v1 with genuine docker command/args and one MAIN_KVBUFFER_SPLIT_CHILD marker. It also retains actual gate NPU-process proof, joint/source-before/source-after and exact stop evidence. The marker is not external operation authority. MAIN must feed the two original operation records to split_service_authority_v1/validator.py; service adapter remains a separate missing step. No T2–15, full-model/lifecycle, TP4 OFF/ON, TTFT/TPOT, GSM8K/LongBench or production-performance claim.

Tests are synthetic stdlib contracts only, do not run Docker/Torch/NPU. The host safety telemetry/parser/cgroup/mount and tiny-canary text are reused from exact frozen DAMP helpers, not a new generic framework.

## Sampled runtime budget correction

All three actual npu-smi commands use verified /usr/local/sbin/npu-smi, non-symlink0555 and SHA c9476b1bf1a2b1cb6b1def82e27889b6f89189a12e9ff4aee5bd2047a19a3cce. Source-audit verifies actual bytes, resolved path and executable permission without running it.

Every30s the parent saves original RAM/cgroup/disk/time/engine inputs before interpreting them, then a bounded resource receipt. Live checks require ordinaryRAM8GiB reserve plus uncommitted growth to both live8GiB caps; both exact owned cgroup1CPU caps, actual current<=peak<=cap (missing live peak rejects); exact stopped peer is recorded separately with last-observed peak or explicitly unavailable, not fabricated. Engine must still expose joint3CPUs. The monitor is sampled, not a guarantee of continuous telemetry or device availability.

Remaining-phase disk minimum is unchanged8GiB reserve + two full source-shaped checkpoint ceilings + ceil(remainingSeconds/30)*2*4MiB conservative future audit allowance. Original passed checkpoints are removed by the frozen child, so cumulative73GiB writes is not treated as simultaneous residency. Raw ceiling derives from frozen cloned tensor shapes (<=FP32 output) plus conservative16MiB serialization policy; not a measured Torch archive upper bound. Each observed current raw must stay under it; over-size/symlink/multiple current raws fails closed without deletion/clipping. Concurrent original passed cleanup can remove a listed raw before lstat; it is recorded as disappearance with no PASS inferred, while unchanged worst-case disk allowance remains. Peer remaining time stays at its full timeout if exact elapsed is unavailable. Own elapsed/deadline/cleanup limits remain unchanged; no budget extension.

Original runtime-budget inputs remain if an assertion fails. Sampled validated budget Ref list is in the child sidecar. This extra gate-process/resource evidence is not interpreted by the frozen aggregate bridge: MAIN must independently validate its true PID/card facts before later authority/service consumption. No device proof or consumer success has been fabricated.

Idle HBM is not an invented1024MiB rule: the NEW source closure explicitly binds existing run_collector_smoke.py SHA da541917ebd8764a81624a215a157b6d4e18fbaaa53d9310be54a104d2fbbf92. Its actual idle_snapshot body supplies exact<=3165MiB via a strict AST/source check; the same zero-AICore + no-real-PID requirement remains. MAIN fresh2860–2864MiB baseline fits that envelope. This preparation does not claim that future cards are idle, and no resource process is stopped merely for mapped devices.

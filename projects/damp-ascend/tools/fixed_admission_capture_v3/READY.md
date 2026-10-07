# C1 v3 BEFORE-guard packet: prepared, not NPU-passed

Only new files in fixed_admission_capture_v3. The published v1/v2 observer, guard,
controller, model, kernels, thresholds and original evidence remain unchanged.
Default plugin OFF, default CLI plan-only, no import/default artifact creation.

Real MAIN0862 failed before the v2 time-axis guard could retain its current values.
MB0494/0498/0499 verified all four off-a trace events files are zero bytes. MB0496,
0497,049a,049b proved actual starts/computed semantics but not failed values. This
packet therefore captures facts; it does not guess a field or weaken that guard.

Explicit runtime: one unique damp_capture entrypoint calls frozen v2 register once.
The original actual supervised_forward closure is checked before adding one wrapper.
The wrapper writes an independent exclusive JSON, unbuffered and fsync, BEFORE
the old begin. CPU/np starts, computed, scheduled, request IDs, prompt count,
expected/actual turn, source hashes and the ORIGINAL bound positions/input_ids are
recorded. It never uses the old Writer or events stream. D2H is diagnostic only.
Each record <=128KiB, at most 4 ranks x33 turns; <=16.5MiB extra bytes per arm,
<=49.5MiB across three arms, within unchanged total20GiB/45min bound.

If evidence construction/write fails, fail before original model writers; this is
an observer failure, not a fabricated native failure. Once old original is called,
its exception object/return object propagates unchanged; no finally evidence can
overwrite it. The original guard, original profile coverage48 and OFF/OFF before
ON remain fully enforced. No source lock, calibration192, compressed model,
performance, accuracy or actual time-axis success follows from software tests.

SOURCE_MANIFEST + full source closure must be checked after MAIN applies/reviews.
The target Python3.12 same-image no-device preflight is required before any device
launch; host AST/fixture tests are not full native first-forward proof.

Commands (MAIN only, cwd canonical repo; no command executed by preparer):
  /usr/bin/python3 -B projects/damp-ascend/tools/fixed_admission_capture_v3/run.py
  /usr/bin/python3 -B projects/damp-ascend/tools/fixed_admission_capture_v3/run.py --preflight-only --output /cache/cch/qwen36-damp-20261006/fixed-admission-c1-v3-no-device
  /usr/bin/python3 -B projects/damp-ascend/tools/fixed_admission_capture_v3/run.py --execute --output /cache/cch/qwen36-damp-20261006/fixed-admission-c1-v3 --prior-host-job-cleanup --prior-device-proofs /cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/physical4/device-proof.json /cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/physical5/device-proof.json /cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/physical6/device-proof.json /cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1/physical7/device-proof.json --prior-device-proof-sha256 3b08af992b969e4b56c7e087457ee9e2082e40556074fb95d660583b019b9ff7 bba9dbd852f6965d086ed0dca27002fb541a94fe5d1e213d00980de3577f6f2f 72f3942a934d0cd03659f4752d5a76a278c8e4d44dbf326998ae23e44772335e b99bcca4fa807122aedc8724b795e6dee44efacf5956f2147bd63c0583676122

Formal retains all original source52/environment/CPU6/cgroup64GiB/ordinary72GiB,
fresh4-7idle/0-3 protection and current070e host-job cleanup. Additionally checks
previous real C1 failed/stopped identity2e3f31... retained (fixed original inspect
and stop refs + fresh exact identity/config/mounts/stopped/Pid0/noOOM/noExecIDs).
All raw failures remain. No repeated automatic retry. Deadline08:48:03Z unchanged.

# MAIN-only one-shot command

Default source validation and printed plan only (NO Docker/NPU/Torch/output):
    cd /opt/host/vnf/austinov/model-tuning-lab
    /usr/bin/python3 -B projects/damp-ascend/tools/fixed_admission_capture_v1/run.py

Software only:
    /usr/bin/python3 -B -m unittest discover -s projects/damp-ascend/tools/fixed_admission_capture_v1/tests -v

After MAIN full source review, a no-device preflight may run WHILE four allT
containers run, subject to actual engineNCPU>=6 and conservative42GiB available
(our32+new2+reserve8),1CPU/2GiB cgroup, unique output and same complete mounts:
    /usr/bin/python3 -B projects/damp-ascend/tools/fixed_admission_capture_v1/run.py --preflight-only --output /cache/cch/qwen36-damp-20261006/fixed-admission-no-device-v1

Formal MAIN one-shot needs actual prior terminal file/SHA (not yet generated while
exec06a0 is running), four MAIN-frozen immutable identities file/SHA, allTstopped/
PID0, fresh NPU4–7 idle,72GiB available and engineNCPU>=7 (6CPU+1reserve):
    /usr/bin/python3 -B projects/damp-ascend/tools/fixed_admission_capture_v1/run.py --execute --output /cache/cch/qwen36-damp-20261006/fixed-admission-c1-v1 --prior-operation-receipt /cache/cch/qwen36-damp-20261006/allT-dispatch-independent_v1-terminal-original.json --prior-operation-sha256 ACTUAL_MAIN_SHA --prior-device-proofs /cache/cch/qwen36-damp-20261006/allT-dispatch-independent_v1/physical4/device-proof.json /cache/cch/qwen36-damp-20261006/allT-dispatch-independent_v1/physical5/device-proof.json /cache/cch/qwen36-damp-20261006/allT-dispatch-independent_v1/physical6/device-proof.json /cache/cch/qwen36-damp-20261006/allT-dispatch-independent_v1/physical7/device-proof.json --prior-device-proof-sha256 b0db314b7752614832cb7bb71682ef71f633082c3a646d891a6f96954ff499ca 552659aec66716f4595bf20ffd90e281d9250e818165b085fd3bdf813b6d4aa1 157ee02348d220e39b01983c4792859e8f7af3b071634a6eb9f9086288d2d337 133b3e76cae53dee474222d81fec330aea202bab5ec454243327517fe078538e

No placeholder above is a success receipt; missing/mismatched inputs fail closed.
Reuse four original device-proof Ref inputs, not a synthetic identity manifest.
Exact original IDs/name/image/owner and physical4–7/logical0 device maps are bound;
fresh actual inspect must be stopped/PID0 with unchanged map. Original full proof
Env is not printed/copied into authored reports or Git. Terminal accepts original AWMCP operation JSON (or original tool structuredContent);
nonzero completed exit permits resource RELEASE only, not correctness PASS.

The controller is complete but NOT LAUNCH-VALIDATED: deterministic TRAIN manifest,
module-only overlay, no-device actual target publicAPI+stdlib+metadata preflight,
reviewed toolkit/IR/ATB shell and whitelist receipts, security/mount/quota checks,
monitoring, exact owned retain-finally, canary and unchanged offline runner, common
supervised observer, OFF/OFF stop rule and OFF/ON comparison.45min TOTAL includes
coldstarts/90sec cleanup;20GiB total raw; no retry, gate relaxation or SOURCE_LOCK.
External sleep declarations do not block; actual unknown high CPU/RAM or changed
external identity stop only our new container. No global-cap/futureCPU guarantee.

Software history remains: MB03e7 originalterminal1,21tests13PASS/8ERROR because
hostCPython lacks public threading.getprofile; MB03ed23PASS is host stdlib only,
stdoutSHAe3b0c442…b855/stderrSHAf583a235…28ce6, originals retained.
Host-only compatibility reader is isolated; target requires3.12 PUBLICgetprofile.
Actual target preflight/native frame/native hooks/canary/threearms remain pending
until MAIN independently executes. No performance/accuracy/fullcalibration claim.

The exact running0–3 baseline is protected, not classified as unknown26.76GiB:
only ID eeb65fd29e054783ce8ba6f9165ea54d38a2575f170225ddf11b3e7584b9f12a
with original name/image/nonprivileged0–3 maps/process set qualifies. Its resident
usage is already in MemAvailable. Initial process IDs/usage are retained; changes
or growth>4GiB/CPU>50%/ordinary reserve breach stop ONLY our newly owned container.
UNKNOWN2GiB/50%,42/72GiB floors and0–3 no-touch boundary are unchanged.
MAIN direct exec06c6 original ValueError is retained as policy-failure evidence,
not a future terminal/file authority nor an NPU result.

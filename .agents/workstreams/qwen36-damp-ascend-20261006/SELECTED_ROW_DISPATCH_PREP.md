# Selected-row validation successor preparation — 2026-10-06

Status: attempted/source-reviewed; not NPU, E2E or task acceptance.

The original MA06a0 completed with exit1 (not tool timeout/cancel): single3600s phase timeout. Its original unmodified tool receipt is /cache/cch/qwen36-damp-20261006/allT-dispatch-independent_v1-terminal-original.json, SHA cf6f4c48b146f9b80bcc037db4059b3b5f322910e6016f9b590495d385ce9d73. Do not retry it unchanged or call this a paper numerical rejection.

MAIN readback MA06f6 finds21 completed graph cases plus partial runs (3544/10240 recorded changing steps), 20866 recorded checks with zero failed checks,24 native B16/single-row anchors across four shards. Full reports remain running/incomplete; no aggregate/source-after acceptance. They do NOT pass the full64-case matrix or general-SR/model gates.
Report SHA physical4/5/6/7: 622b1672fe708eb3f52d6b33615f4d68c78f51cf786b21bf1292fefef5301e12 / 2233678dd5f5549724e9e99ec78b5ad02034b008480e0bce12d676f242837896 / 152588cae163edecc4fd4c2e48abf8788e48033ef6bbef0fef83107e68292934 / a1707f3527fbdfc87f20671dd9706b8608b8ff2d7d8f76e365dc28aacaae1abd.
Original FAILURE SHA59f7fa6a15898a88166cabfc42837f01518ad3c67a62d3562d1cbd59c2fbf0c9; STOP_RETAIN ce5da4b55d2f9cb5d078d6a0d3e4abb0d1c64c1e9c9e7ccf244c0000141546da; POST_RELEASE ce95df6d22205c0246ded25fbb07d7df9344e6559e3a7b47d04e46e8392d7711. Exact four owned containers stopped/Pid0, retained, not deleted; protected0–3 PID/start/cgroup unchanged.

MAIN MA06f1 fresh ordinary MemAvailable62,744,388KiB (~59.84GiB), below unchanged formal-model64+8GiB admission. No full C1 model launch, cap reduction, HugeTLB reclaim or external stop is authorized by idle cards. Actual4–7 have no compute PID/core0, HBM2860–2864MiB inside the existing source-bound3165MiB idle envelope (run_collector_smoke.py da541917...), not an invented1024MiB threshold.

## Evidence-supported successor

NEW projects/damp-ascend/tools/selected_row_dispatch_v1:
explicit T groups4=[1,8,9,16],5=[2,7,10,15],6=[3,6,11,14],7=[4,5,12,13], sumT34 each. Source packet8b22355b400654e96ab10813bfc605ccecabbe4e647c701ba29f544a817fdcef.
First192 full-S/local-S1 bitwise equivalence pairs, then original24 native anchors, then unchanged64×160 changing steps/eight identical replays, guards/limits1e-5/.00303. DefaultOFF; no candidate/native source, kernel, SO or threshold change. No general-SR/final192calibrated plans/service/performance/task claim.
Journal changes evidence disk serialization/checkpoints, preserves every check/step/raw and requires final exact reconstruction. safe_json still scans in-memory history; this is not a proven CPU-linear or E2E speedup.

MAIN MA06f8:14/14 stdlib, AST4, actual original MA06a0/triple artifact replay (prior_success=false), complete52-entry source/model closure, noTorch/NPU; six NEW files are the only untracked source dependencies. Original software-source receipt saved outsideGit at selected-row-reference-preparation-v1-main-records/software-source-MA06f8-original.json (hash to read back).
Agent MA06f2 early two stale reference digests failed strict closure before actions; MA06f5/f7 corrected only NEW packet to actual frozen final seam/test digests. Preserve failure, do not relax pin checks.

Next MAIN: coherent commit/push; exact-image no-device fresh-export CLI/Meta; fresh summed resources/mapping/canary/source; one immutable bounded successor only if prerequisites pass. Fixed DAMP deadline2026-10-07T08:48:03Z unchanged. Formal performance/calibration remain exclusive; E2E/task acceptance still missing.

## Reusable lesson

Prepare real CLI and transitive tracked source closure, original authority format, executable paths, host-specific idle envelope and cost-balanced groups before scarce-card launch. Validate a faster oracle bitwise before using it; never drop coverage to finish a timeout. Separate zero failed partial checks from a completed matrix PASS, and separate free NPU memory from ordinary host-model RAM admission.

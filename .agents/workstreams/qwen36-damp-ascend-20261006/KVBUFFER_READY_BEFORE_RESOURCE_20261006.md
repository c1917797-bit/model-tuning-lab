# Ready-before-resource: KVBuffer coherent preparation

## Evidence and scope

MAIN read all11 old service files, five split gate files, four authority bridge
files and five NEW dispatcher files. Existing compiled/operator/plugin/oracle
bytes were not changed. MA0713 actually completed exit0:
17 service +17 split +14 bridge +21 dispatcher =69 stdlib checks.
All49 dispatcher source dependencies matched; tests are CPU software contracts,
NOT actual candidate NPU/model/service/performance/task acceptance.
Original terminal is outside Git:
`/cache/cch/qwen36-damp-20261006/kvbuffer-main-preparation-MA0713-terminal-original.json`.
The original original-wrapper timedOut=false/exitCode=0 was inspected rather
than inferred from projected summaries.

Original MA0713 SHA
da943338fcaf101ab9a6b6a36ec3d6a4460fdb8dd893144af7e710ab170a973d.
Original MA0712 live observation SHA
b68e268a3cf99fe3f0b941649e922dcbd8ee61e78856829e5865e5559ece4d0d.
MA0714 MST validates20 skills, Python parsing and authored governance
whitespace passed. Full staged whitespace exited2 solely for four retained
extra EOF blank lines in frozen service metadata/__init__ files. Preserve
source-bound bytes; this is a recorded negative style check, not a blanket PASS.

Dispatcher packet:
`projects/kvbuffer-parallel-ascend/tools/split_dispatch_v1/PACKET.json`
SHA eb2fd0cae186db8b73749255bc8f1ceba5ef1d57f67e2a557126b8bbb37517a9.
This checkpoint publishes its complete previously-untracked25-file closure:
service11 + split gate5 + bridge4 + dispatcher5. Other draft paths stay excluded.
Fresh-export actual-image CLI tests and downstream adapter are still pending.

## Proven pre-card integration gap

Old service launch.py calls validate_native_gate even under --prepare-only.
That contract accepts only kvbp-parallel-fp32-native-gate/v1 with the old combined
8-case kernel_native_eager_graph_pass report. NEW split validator produces
kvbp.split-kernel-prerequisite/v1; old startup rejects this descriptor before
model/argv admission. The existing producer-shaped test explicitly reproduces
the rejection. Never manufacture old single-process PASS to hide it.

NEW dispatcher really records actual_gate_process (ACTUAL_GATE_NPU_PID with
real Python argv/NSpid/cgroup/start_ticks), joint, cleanup,
runtime_resource_budgets and source_before/after. Frozen bridge binds arbitrary
device raw Refs but does not parse those extra observations. Prelaunch
same_process_pid belongs to waiting bash and is explicitly NOT native execution.
A distinct consumer must verify actual Python/NPU rows and recompute the sampled
resource inputs, not merely accept a canary boolean or process-agnostic hashes.

Actual split reports are output_root/gate/report.json. New two-arm reports do
not exist yet; old /kvbuffer-results/p1-native-matrix-v1/report.json examples are
not valid current paths. Plugin and both general-plugin entrypoints DO exist;
no missing-package conclusion is supported. Old launch PYTHONPATH contains
plugin and tools/service; keep both arms' common plugins/settings equal.

The bridge uses canonical source and host absolute artifact/authority paths.
If reused inside the image, explicitly mount the exact joint/authority/build/
Meta/native snapshot evidence RO at those same paths and inspect actual mounts;
a sole /kvbuffer-results mount does not make /cache/cch Refs readable.
New live arm outputs remain separate RW. No path alias is assumed verified.

## Next execution and goal alignment

During MA070e all four authorized cards are owned by the existing DAMP matrix;
no second NPU job or live52-source edit. MA0712 observed11 completed cases/
1760 feedback rows and24 native anchors, zero failed recorded checks; aggregate
is pending. Four actual Python PIDs map to physical4–7; protected0–3 unchanged.
This partial observation does not accept all64 cases or imply final192 plans.

Finish thin NEW consumer/launcher wiring and real-image export/CLI prerequisite
before reserving cards. After actual MA070e terminal and exact-owned release,
MAIN freshly checks physical devices, aggregate RAM/CPU/disk/mount caps and
new names, then dispatches a reviewed useful matrix; no automatic retry.
Full model C1 unchanged72GiB ordinary RAM remains unmet at the latest snapshot.
Do not lower it or stop protected0–3 merely because target HBM is idle.

DAMP cutoff2026-10-07T08:48:03Z and portfolio cutoff2026-10-09T11:17:31Z
remain fixed. KVBuffer preparation has not started a new formal24-hour timer.
Kernel prerequisite never implies trueT2–15/full48 lifecycle/TP4 correctness,
matched E2E, three repeated pairs or final GSM8K/LongBench-v2 acceptance.
Prior HYPIC remains an historical exemplar, not a newly delivered success.

# SparQ009 diagnosis and KIVI CPU persistence failure — 2026-10-08

## Scope and current decision

Goal remains active; no new non-HYPIC candidate has passed matched E2E and final
tasks. Original SparQ009 native failure is unchanged. CPU diagnosis supplies a
new ranking-boundary hypothesis, not native correctness or a relaxed threshold.
KIVI002 failed during CPU evidence persistence, not quantization numerics.
All MAIN jobs mentioned here are terminal and exact owned guests stopped-retained.

## SparQ009 original saved-failure diagnosis

Original native gate: MAIN118f exit1/212281ms,4 complete B1 cases/689 successful
steps; graph mean0 trial1 step049 failed same-candidate-query support comparison.
Saved checkpoint171463194B SHA
3815632ca4a920e4a1cf52e823c4b099cb4c612eb2fe9254048ed5655d7448da.

New MAIN11b1 completed0/22539ms. Actual same-image Devices[] CPU reader:
Torch2.10.0+cpu,3.269s,441192KiB RSS. Host externally bound actual workload
PID2593840/startticks35819762/guestPID7/argv/cgroup/oneCPU/eightGiB;
no Torch-NPU import/init or hardware FD. All15 CPU snapshot checks passed,
including complete native K/V bitwise parity, append-only history, topology,
guards and128-context metadata. This does not establish graph pointer lifetime.

Exact full BF16 K and V matched every scratch token to2098 live tokens.
Recovered all128 tokens equals independent FP32 full-capacity2304 support.
FP64 differs by one: native/CPU32extra361,missing1157; q/rq bitwise equal.
FP64 scores:1157=0.0028689084312485597;361=0.0028689084269511757.
Gap4.297384063184362e-12=0.018457124 FP32 ULP. CPU32 selects361 by1ULP.
Classification:consistent-with-cpu-fp32-ranking-boundary-not-causal-proof.
root_cause_confirmed=false; retry_permitted=false.
Original native ranking/selected intermediates were not saved.
A new minimal source-bound same-checkpoint NPU observation is being prepared.

Actual output root:
`/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq009-support-cpu-20261008-001`.
RESULT SHA7acab64ea01f3a5145a1e1f20ada39a7ebdc641ebee2bf530b23a1c529dbdc6c;
support-diagnostic/REPORT.json2978B SHA
2772c563b4c9536afacfb82201b433a166ad29d81e1c43067f5ce555be8fe7ee;
RANKING.json SHA7b72fe85de6e98a887d4b9ef4b3c0d8dc25733f01c55e2a81775881c3a5de8b7.
Independent MAIN11b4 completed0/83ms checked exact source/result/ranking and
CPU CID558888f31e283e2456e51f515f8e27c00cc8b795402e6c72b55e741d43763c86
stopped/Pid0/noExec/OOMfalse. Whole originals now saved outsideGit in the same
root: MAIN11B1_ORIGINAL_OPERATION.json and MAIN11B4_ORIGINAL_READBACK.json.
CPU host source root:
`/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq009-support-cpu-host-v1-001`;
host_main.py SHA b57b80c6b8b3672aba30018da694a3ac1f1af28b4cb8718c707e8ad5295b3640.
These artifacts are CPU/storage diagnosis only, not vLLM readiness or throughput.

## KIVI002 actual CPU run and primary persistence failure

MAIN11b9 completed1/25834ms. Fresh host and Docker daemon each had7 effective
CPUs; before create checked MAIN4 + three preparer helpers3 CPU, ordinary
11.25GiB including unchanged8GiB reserve at every shared ancestor. No NPU.
Source manifest e1d20c16c9e2cb7d6fa4df95353cdfdce5e1eb535ab936a1da855c5be61272d7.
Actual producer PID2704112/startticks35893630 passed preflight/oneCPU/twoGiB
proof, then firstb2-float16 attempt failed at CPU_ABI.py69 torch.save:
RuntimeError:Cannot save multiple tensors or storages that view the same data
as different types (torch_npu/utils/serialization.py400).
algorithm checks=[]; independent consumer did not execute. The generic host
terminal assertion is secondary to the preserved inside serialization traceback.
Not a numerical or paper-wide no-go; do not repeat002 unchanged.

Output:
`/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-cpu-host-002-main-20261008-01`.
Preserved producer-INSIDE.json170311B,algorithm/RESULT.json3485B,
producer-HOST.json84700B,HOST_RESULT.json and MAIN11B9_ORIGINAL_OPERATION.json.
Exact CIDcdd4a68f2049edc2382992893dbad45503015647afb2e5e1aeea1c51a1882abb
was stopped-retained/Pid0/noExec/OOMfalse; secondary cleanup errors=[].
Exit137 is owned stop, not an OOM claim. Independent current inspect pending.
MAIN11bf completed0/566ms independently inspected this exact stopped-owned
Devices[] CID before and after readonly public Python source copies; State and
ExecIDs unchanged, Pid0/OOMfalse confirmed. The pending inspection above is
now satisfied; no guest restart/exec/device work occurred.
Successor preparation is snapshot-only cloning after live alias descriptions;
packing/reader/math/coverage unchanged; tiny same-image serialization prerequisite
must precede its full CPU run. Nothing is NPU/model/E2E-ready from this failure.

## Memory authority and next actions

Exactly32GiB idle1GiB HugeTLB release already completed once atOct7T16:04:28Z,
node0 nr471->439. This authority is SPENT; no further release.
MAIN11b9 fresh readonly before-create atOct8T04:24:45.925405Z verified:
ordinary MemAvailable116617672KiB (~111.215GiB), OVS PID27118/start11471,
actual Hugetlb24GiB; pools439/485/486/474. No OVS stop/config change.
Original memory RESULT SHA
069cae7b82a614fd377dea7498c084286db1bd80425cb32efb3e9d98382bac58.

Next: SparQ single-checkpoint native selector witness -> evidence-supported
correctness repair only if justified -> TP4/full model/stockgraph/lifecycle;
KIVI tiny snapshot prerequisite; SparsePrefix v4 real same-image import.
SparsePrefix19CPU was a conservative template, not source-proven necessity:
prepare a separately registered exclusive guest4+host1+reserve2 correctness
budget with prep CPU commands paused, no coverage/tolerance/cutoff reduction.
All performance/task evidence remains pending. Fixed portfolioOct9T11:17:31Z,
KV/H8Oct8T08:29:54Z unchanged. Remote normal-push authentication blocker
unchanged; local checkpoint must not be described as pushed.

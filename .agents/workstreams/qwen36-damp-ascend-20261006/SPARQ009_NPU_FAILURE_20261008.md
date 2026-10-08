# SparQ009-002 real NPU partial-matrix failure — 2026-10-08

This is a failed numerical implementation gate, not a paper-wide rejection.
No full-model, end-to-end speed or task-accuracy result was produced.

## Actual source and terminal authority

The native PA boundary now uses persistent CPU int32 context lengths and the
source-supported workspace/event/task-update graph interface. The token selector,
mean-V lifecycle, independent feedback oracle, complete matrix and original
0.005 relative-RMS / 0.99998 cosine limits were unchanged. Actual canonical
MAIN1188 passed 116 software tests and 27 source bindings; MAIN118e checked the
three real default-OFF CLIs and exact host argv. These are prerequisites only.

MAIN118f genuinely completed exit1 in212281ms. Source manifest SHA:
2af9e35649d8e1b8b8220968bedd819a5fc6c2afa5c1abfb77ebf768dd4b49af.
Original terminal envelope is preserved beside this note. Original result root:
/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-v6-009-002-native-20261008-001.

Actual same-image Devices[] ABI and physical NPU6 -> guest0 canary passed.
The native matrix completed four B1 cases: eager mean0/mean1 trial0 and graph
mean0/mean1 trial0. There are689 written step records, not the full128case /
20480step PASS. B1 graph mean0 trial1 failed at step049 before the output-error
comparison, because native selected token IDs differed from the independent
same-query GQA formula. Batches2..16 were not reached.

The first failed assertion is not an identified root cause. Preserve the171463194B
CPU failure checkpoint, including both Q streams, full KV and compact scratch,
and distinguish near-boundary arithmetic/order differences from stale graph data.
The raw selected-support field is assigned after this assertion; do not invent
it in the old checkpoint. Recover scratch->full-cache support only under a
unique byte-exact match, otherwise report unknown. No unchanged retry or gate
relaxation is authorized by this evidence.

## Retained artifacts

- RESULT.json SHA4a2e2ef353601c1f4116c8cc4009b14f6676614ec31b3accb43160fb57d2abcb
- gate/REPORT.json SHA f3bf94122b432a15e138ab7c595d66e4d8f0aa79264d2f9bf83b28a725f5907d
- matrix.stderr SHA e602bd4e862176de0ae4497500542b7dd3808b73fa006774ec2a6adb5733efe4
- gate/failure-b1-graph-mean0-t1-049.pt SHA3815632ca4a920e4a1cf52e823c4b099cb4c612eb2fe9254048ed5655d7448da

The old progress observer's uppercase CASE glob returned0 and did not measure
actual lowercase case files. Use the original REPORT and actual filenames.
Preparatory CLI observers had per-entry payload assumptions and an extra EOF
copy error; their failed receipts are not native numerical/paper failures.

## Actual release and next loop

MAIN1196 read-only at2026-10-08T03:47:19.544514Z independently proved both exact
owned CPU777c66150fee5cc749a0123e2d55b0981472dc9ed3a22894ae6fc7be2577cf90
and NPU4ba3a153dfa84d7f2803c3f34bfa382d74115fb9068b73531b99bf6fc0733433
stopped-retained/Pid0/noExec/OOMfalse. All physical cards had no NPU process.
OVS remained PID27118/startticks11471/24GiB; ordinary available111.2250938GiB.
HugeTLB pools439/485/486/474 and protected NUMA3 capacity were unchanged.
The earlier32GiB release is completed/SPENT, never a renewed allowance.

Short: source-bound Devices[] checkpoint diagnosis; only then a proved minimal
numerical fix and an unchanged complete native matrix. In parallel, prepare the
actual FULL model graph seam, KIVI faithful compact lifecycle and SparsePrefix
all-rank byte-commit/request corpus. A model callback design is not a native PASS.
Continue through TP4/lifecycle -> same-stack/common-opt fixed1024 paired E2E
with TTFT/TPOT -> final no-thinking2048 normal-EOS LongBench-v2/GSM8K.
No accepted new non-HYPIC method exists. Per-paper/portfolio cutoffs do not reset.

Normal push remains unconfirmed: the previously verified credential-helper
blocker has not changed. Do not retry unchanged, bypass authentication, force
push or update main. This is a disabled research checkpoint, not final delivery.

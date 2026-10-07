# SparQ004 actual entry result — 2026-10-07 22:21Z

MA107a is terminal exit1/61.844s. Whole original, child and dispatch envelopes
are preserved beside this note. This was an actual same-image Devices[] ABI
attempt, not a NPU numeric or algorithm failure. NPU CID=null/npu_executed=false.

Original failed RESULT:
b56e4aee888fe61edcffab1453960781814b3ce1a9e9cad1b7049ba0391b8f4e
Original CPU ABI:
b4f64182cf9f0f0af12aef9ad12a666ccb9ecdcf5e4ebee3e7b01c62115aab86
Raw child:
507014db03f4c7a76666b688686c4610df4d3b052f2ee077cb30ad959b0b12e5
ABI observations:
520a0954d8a67fb002646eab205652eac22af8295ad709ae2e9921b778f81661

The original observer captures ImportError: DeviceOperator from partially
initialized vllm_ascend.device.device_op. Direct leaf import has a real circular
dependency in this pinned v0.23 image. All observed device nodes/Ascend FDs
remain empty and TorchNPU initialized=false. The actual stack is Torch2.10.0+cpu,
TorchNPU2.10.0.post4 and vLLM-Ascend0.23.0. No native numerical case started.
The source-only 84 tests/source27 success did NOT prove runtime import ordering.
Sparse owner must use source/actual successful normal bootstrap evidence for
a minimal independent import-order successor; do not rerun004 unchanged.

Exact CPU CID3fa392c7db126e7552d5fa5fdfe7893a5363f125eb3a748db6a0a4d55cb49143
was stopped and retained, no deletion or OOM. Own cleanup errors=[].
MAIN readonly MA107b initially selected process_rows on the wrong helper module;
retain its exit1 rather than relabel it. Separate corrected readonly MA107c exit0
fully validates exact original OWNED/source/labels/device/mount identity, then
Stopped/Pid0/noExec/noOOM/Devices[]. It emits unmodified fresh SMI: all NPUs idle,
healthOK/AICore0/idle HBM, no running processes. This is not a repeated stop.
The original failed RESULT SHA is verified unchanged.

Additional readiness lessons: AWMCP same-peer copy acknowledgments for H8 v6
did not establish physical files: exact execution-plane checks found the whole
proposed v6 root absent. Preserve failed MAIN exact mechanical copy MA1070.
The three-host-controller RO mount proposal was blocked by safety review and
is paused; no equivalent alternate write or new host mount was attempted.
An independently safer host-full-ancestry plus guest-leaf proof may be prepared,
without namespace/capability/PID/network/host-controller visibility expansion,
and without reducing any resource floor, protection, source or deadline gate.

Memory release authority is completed/spent: exactly32GiB, OVS/full NUMA3 intact.
KV cutoff2026-10-08T08:29:54Z and portfolio2026-10-09T11:17:31Z remain unchanged.
No newly accepted non-HYPIC paired E2E or task-quality result. Three actual source
preparers continue, MAIN alone admits serial device work. Local checkpoint36f958e
passed MST20/diff checks; credential-helper publication blocker unchanged.

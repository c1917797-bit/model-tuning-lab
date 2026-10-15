# Official bounded profiler diagnostic — prospective, not launched
Purpose: explain retained G3 regression, not redefine formal performance/quality.
R6 full40 TPOT452.718825ms vs G1 284.114624ms; C2 barrier alone changed only
0.36percent versus R5, single-unit noise not established improvement.
No live owned NPU stage. Actual04af release verified.

Evidence/source routing:
- Official pinned image660ce23a...; no-device inspections04b8/04b9/04ba/04bf.
- Native TorchNPUProfilerWrapper SHA256
  0c9ffcaf695a9b1fcb44a51bdd92e69f763a7c5be64a8efbd498d6536b9e09e5.
- Native WorkerProfiler wrapper SHA256
  31f8a33afd23e67a2ade5a95d0d837a03b0a9164d5b18acf561d948c9ae6c06c.
- Built-in Level1/PipeUtilization CPU+NPU. Stack/memory disabled, frontend ignored.
- Cannbot external guidance commitd5e0d44b7a1d2e90c5f0b9fb62970fb3bac89ec3;
  guidance only, not reproduced profiler evidence.
- Explicit start/stop native endpoints; max_iterations uses > comparison,
  hence configured12 can collect13 worker step boundaries. Not exact12 promise.

New profile_tp4_diagnostic.py copies ONLY our reviewed generic guard/controller,
not old HYPIC code. Original native_tp4_smoke.py and inference source94 unchanged.
independent_profile_workload.py uses same immutable full40 artifact, same2B+2A
unscored warmups then first16 exact32768 inputs concurrently, fixed64 outputs.
This reduced output diagnostic is NEVER the40/1024 formal unit or quality gate.
Profile is enabled after warmups, bounded max12(plus boundary), finally stopped.
First capture may contain both chunked prefill and early decode: classify actual
timeline/rows, do not label a combined capture pure decode. Subsequent phase
capture must choose delay from observed actual worker step alignment.

CPU04c1 found invalid empty-artifact positive fixture; retained failed operation.
Fixture corrected,04c2 five protocol controls PASS.04c4 parse/import PASS.
These are host doubles, no NPU/profile completeness proof.

Before device start:
freeze new contract/controller/module hashes and unchanged R6 manifest;
prove native endpoint/config compatibility, fresh ma/host-development/direct,
physical0-3/8233/HCCL empty and new immutable output root absent.
Only current deadline2026-10-15T19:04:09UTC. Continuous isolation/exact own release.
Keep instrumented traces outside Git under new rawroot/scratch profile directory.
Validate fourworker trace identities, kernel/operator/API tables and valid timeline;
profiler start HTTP200 alone is insufficient.

Analysis/disproof:
timeline gaps/serialized launches vs CPU-to-NPU copies vs kernels/synchronization,
then HCCL overlap/crossrank spread. Sum durations across ranks/streams is NOT
removable wall time. Rebaseline same diagnostic if quantitative attribution needs
native control. No algorithm change until a measured opportunity bound supports it.
Full G1-G4x3/paired quality/lifecycle/Paper-to-Ascend/29Skills remain unfinished.

# Attribute an Ascend numerical failure to the actual executed library

Use this when a standalone replay and a captured production frame disagree. Keep model qualification and performance acceptance separate from diagnosis.

1. Record the actual call schema, callable identity, loaded binary hash and adapter hash at the call. Registration or an imported module proves availability, not dispatch. Identical adapters can load different binaries.
2. Freeze the same input and independent initial state, dtype/layout, parents/depth, oracle and numerical limits. Retain independent FP64, the native/reference ABI, and historical production output as separate comparisons. A historical mismatch must not be silently discarded when a new replay matches.
3. Compare one variable at a time. A new/old/new result that repeats the new result supports a library-dependent difference for that case. It does not prove the exact stream dependency or qualify other shapes, states or callers. To attribute a stream fix, isolate and verify the specific dependency change.
4. Validate the actual runtime consumer and CLI, including hardcoded identity predicates, not only a static request-prefix helper. Rebinding request Refs may leave a nested binary SHA predicate stale. Preserve the failed entry and update only the proven identity binding for the new diagnostic package; do not weaken guards or alter mathematical tolerances.
5. Exit0 from a diagnostic means collection completed. Check actual compute calls and individual numerical results. Diagnostic reports explicitly lacking original consumer/operator/short8/model acceptance cannot be promoted by a MAIN boolean or a neighbouring PASS.
6. Integrate the actual new wrapper with its complete artifact provenance. Obtain its real one-frame acceptance and required shape/state coverage before original model gates. Old wrapper receipts do not qualify a wrapper with a changed binary binding. Whole-model matched performance and task accuracy remain separate gates.
7. Keep evidence on the authorized host, persist immutable inputs and exact owner/container terminal/release, and dispatch only a genuinely ready successor. Do not turn a preparation queue into fake NPU utilization or treat phase limits as measured durations.

Observed case, 2026-11-04: BOLE physical1 newf65/old8e7/newf65, same adapter7118 and captured frame2f4d. New runs each matched seven NPU/FP64 metrics; old run mismatched six. All remain single-case diagnostics. Host evidence index: `.agents/workstreams/qwen36-damp-ascend-20261006/dual_resume_20261104T091749Z/BOLE_NEW_OLD_NEW_CASE_REVIEW_20261104.json`, SHA256faa9d17401600ad970ed6fc3d5bf4f5393294f21982ffeca5e60248082ed772c. Do not describe these results as an accepted algorithm or a performance gain.


## BOLE f65 registered wrapper one-frame closure, 2026-11-04

1. Bind complete path/bytes/SHA Ref3 to actual registered build inputs; identical bytes at another path require a genuine new proof. Preserve exact guards and old evidence.
2. Check the real CLI, self-file pin, role-specific producer/consumer schemas, transitive Python imports and readonly mounts together. The original FP64 reference needed its model_entry import root. Verify every owner-required immutable file before dispatch.
3. Allocate fresh complete mutable S/control/META/OUT paths. Keep predecessor file/CID/PID/start as one actual tuple. Rebinding only its file caused an entry failure; omitting its required readset caused another, both before container creation.
4. Numeric RESULT.checks differs from independent ACK.checks_verified and independent_CPU_reference_checks. A report-contract exception is not a numeric failure and must not be filled by a neighboring PASS.
5. Original FP64 saved-output readback is independent verification, not a repeated algorithm CPU suite. Its frozen CPU-only device tag does not authorize real NPU access; actual owner mapping and no-device consumer inspect prove separate facts.
6. After child remote I/O hangs without handles, use MAIN calls and bounded offline agent review. No returned artifact means no READY successor. Bound metadata by role instead of dumping dirty trees or full Ref collections.
7. Docker NoSuchObject is absence, not exited. An explicit successor must bind healthy same-daemon/full-list and no-writer evidence on producer and consumer sides, preserving historical ledger/file hashes without fabricated State/ExitCode/OOM.

### Physical-scope labels and original192 evidence

The newf65 matrix executed on physical1 using saved four-source-rank x48-layer inputs:192 original cases/3456 original predicates. Independent RAW-hash/identity audit is not a second numerical recomputation. Runtime identity filenames and binary/wrapper FullRefs are separate; metric dictionaries require explicit passed fields. Preserve stale physical4 aggregate with exact actual-card proof. Real registered-consumer derived acceptance is limited to components; TP4 model/performance/accuracy remain unqualified.

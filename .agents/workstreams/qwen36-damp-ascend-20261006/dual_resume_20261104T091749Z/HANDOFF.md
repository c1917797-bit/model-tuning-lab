# Current stage: physical1 real NPU diagnostic completed; qualification pending

Updated 2026-11-04 16:56:57 UTC. Latest authority permits physical0–3 only; preserve physical4–7 and vllm-au-test. Frozen cutoff remains 2026-11-05T09:17:49Z (1793870269).

- Actual entry exec-00000000000007bb / ma: owner2233361/start192780472; exact CID 029413132d35f6ba9799b5da4a1c8785983d36b35f6168b8de2d3e11747938fb. Guest and owner exited0. This is a single saved-frame diagnostic, not a model or qualification PASS.
- Seven NPU P/U/Y/state metrics match the FP64 oracle; inputs remained bitwise unchanged. Three recorded production P/U/Y replay metrics still fail. Review: BOLE_PHYSICAL1_V18_INDEPENDENT_DIAGNOSTIC_REVIEW_20261104.json; fresh release: BOLE_PHYSICAL1_V18_FRESH_SMI_AND_METRICS_20261104.json.
- Physical1 host node is mapped to guest /dev/davinci0; logical0 is intentional. ASCEND_VISIBLE_DEVICES=1, ASCEND_RT_VISIBLE_DEVICES=0. Do not reject the guest alias as access to physical0.
- Physical0 is genuinely blocked at the driver UDA namespace layer (udevid0/ns_id0); owner unproved. This is distinct from compute occupancy. Do not blame or stop vllm-au-test from its broad device declaration. Do not reset or alter service/shared modes.
- No extra full CPU suites or mirrored preflight: the native owner already validates fixed operands with actual globals. Preserve all native guards. Source-only preparation failures and precreate V16 failure are not algorithm failures.
- Read latest EXECUTION_BOLE_PHYSICAL1_V18_DIAGNOSTIC_TERMINAL_20261104.json. Next host-only work is production routing/capture contract review in PRODUCTION_GDN_CONTRACT_NEXT_20261104.md. No genuinely ready successor yet; do not fake READY/MAIN/consumer PASS or rerun old qualification packages.
- All short8/state/long160/model/performance/accuracy qualifications remain false. Source and RAW stay on chicaihong01. No cleanup/hugepage allowance added; no deadline extension. Thirty-minute utilization remains unmeasured.
- Treat older text below as history; old V9 and old scope/status must not override this section.


# BOLE / DeltaLog — current device-scope handoff

The latest human instruction is “你改用0-3卡”. Physical NPU0–3 are authorized for this window. Preserve physical4–7 and vllm-au-test; do not stop it or its processes. The old protect0–3 rule is superseded only for this device scope. No deadline or cleanup-budget extension.

Authority: DEVICE_SCOPE_AUTHORIZATION_20261104_0_3.json, 3555 bytes, SHA256 47519b2e65ea727370cad369c1b0b52444bf712b05eedd98cbb022169a371383.
Fixed cutoff: 2026-11-05T09:17:49Z, epoch1793870269. Original start1792828303 and old window closures remain unchanged. Source and RAW remain host-only.

## Actual execution

V9 operation exec-000000000000076a has actually finished with owner exit3 and guest exit3. It is not active. Owner PID908286/start191963775 is absent. Exact CID a71264f7015793f74aa379325786006fd54b6369486fbe66e1f5bcf340c168b7 is exited/Runningfalse/Pid0/noOOM. Independent read operation076b observed physical0 healthy/AICore0/HBM2886MiB/no compute PID at epoch1793802890.8295074; protected vllm-au-test still running. See SCOPE0_3_V9_INDEPENDENT_REVIEW.json. These are dated observations, not future admission.

V9 stopped at ValueError “one visible NPU required”, guest line124, before BOLE NPU operator arithmetic. Actual device_count was not recorded. The phase label NPU_OPERATOR and container startup do not prove kernel execution. Reference ABI calculations passed; expected recorded-frame mismatch remains an observation. No numeric/model/performance/accuracy PASS. Diagnose actual enumeration count and real physical0 isolation before correcting this assumption; do not blindly rerun V9 or relax the guard from a guess.

Owner: run_bole_stream_queue_physical0_owner_v9_release.py, 21478 bytes, SHA256 a03808c1812c08ed254febea555c3e9d026dd44225b4c7bd89dc02d3f612a981.
Preparation: bole_physical0_prepare_v9; owner metadata: bole_physical0_owner_v9; output: bole_physical0_stream_queue_run_v9.
The entry uses only physical0 mapped to guest0, 300-second phase plus60 cleanup, 4GiB guest RAM and20MiB diagnostic output cap. It is a diagnostic, not model qualification.

## Evidence and repaired boundaries

The historical frame, compiled stream-queue library, numerical oracle and thresholds are unchanged. New device mapping, authority, cutoff, lock, protected set and runtime Ref3 closure are bound to current scope. inputs[4] gamma and4GiB limits are unchanged.
Ten actual prior terminal CIDs were checked using original full-hash source/terminal/ownership records plus healthy Docker, exact NoSuchObject, old PID identity and cgroup checks. PRIOR_EXACT_TERMINAL_CID_INDEX_V8.json and PRIOR_REMOVED_ACTUAL_BOUNDARY_V8.json preserve the evidence.
The modified repeated-observation write boundary was actually exercised twice; immutable timestamped receipt names avoid overwriting prior observations. See REMOVED_OBSERVATION_APPEND_BOUNDARY_V9.
Do not run prepared base owners without the release suffix. Old V1–V8 failures remain preserved; do not retry them.

V8 reached container creation but failed before start on duplicate observation filename. Its exact CID d097d5f2025e8575d61eddbbd66896d4ed8c1044cca27ad768f2c0a6b5ca2015 was last observed created/Runningfalse/Pid0. This is not a current release snapshot. Inspect exact current state if needed; a declaration-only idle container is not compute occupancy.

## Remaining work

V9 terminal and independent release are now verified as above. Next collect only the missing visibility/enumeration evidence through a bounded new diagnostic with current scope, fresh resource checks and new output/control directories. Official contract research is delegated to npu_visible_count_contract; it has no host access and cannot establish runtime PASS.
If the diagnostic proves the stream fix, prepare the actual short8 model successor on0–3; preserve original qualification gates. Then matched32K/fixed1024/c1/profilingOFF diagnostic, long correctness, three formal pairs and GSM8K/HumanEval/MMLU smoke/full are still required.
DeltaLog current-window timing source-only work is retained, not NPU READY. CPU004 precise logical-close/ABI successor remains unfinished; do not repeat unchanged CPU255 tests or claim a guest software exit as native PASS.
30-minute utilization is UNMEASURED without continuous evidence. Snapshots and preparation do not establish no idle gap or paper success.


## New/old/new library diagnostic stage — 2026-11-04

This section supersedes the V18-only attribution description above. Actual V26 old-production-library replay (operation07e3, exact owner3022716/start193268028, CIDc91e2a1f29d9f3f2f07d3722eb7d65bb0b34b9a765124ed14f61a4af1ff734df) exited0 after29.0187s. That exit means diagnostic collection completed: actual verify_calls1, with six NPU/FP64 mismatches (P/U/Y/state1/2/3). V27 new-library repeat (operation07e9, owner3087375/start193307233) exited0 after29.1766s and repeated all seven NPU/FP64 matches. V18/new and V27/new use f65d7eced4ac9f66f2d525d079786bf15e5e67270a70ed3b6ed794fa5b068a2a; V26 uses actual production8e7f4e2a43e700e8535f754ffcba8fa2bc3b36b2d2fd32dc4ae4c19d020fdb9d. Adapter711840f039f43de2eeff2827431e2717a242f04b4d181cdcc4ebb25662953427 is byte-identical. Same immutable real input, parents/depth, independent FP64 oracle, dtype/device and mathematical thresholds. This supports a library-dependent difference for this one case; it does not prove a particular stream mechanism or whole-model success.

Evidence: BOLE_NEW_OLD_NEW_CASE_REVIEW_20261104.json (20516B/faa9d17401600ad970ed6fc3d5bf4f5393294f21982ffeca5e60248082ed772c). V27 RESULT.json is9331B/6708edf31aa5903add9217102e80d10d491e4c2f2e0a19c54048566d3b44a429. Independent review at epoch1793815931.4893224; it checks exact owner absent and exact container exited/Pid0. Fresh device admission is still required for every next action. Historical captured P/U/Y remain discrepant; operator/short8/model/performance/quality qualification remains false.

The failed V21 attempt is retained: it reached the real runtime validator but its binary SHA predicate still expectedf65 after the request was rebound to8e7. V26 changed only that exact diagnostic identity predicate; mathematical body and numerical bounds stayed identical. The separate static request-prefix contract had passed and was insufficient to prove the real CLI boundary. Do not rerun V21 or claim its failure was numerical.

Next real BOLE node: bindf65 with its real compiled index/manifest/source package to the actual core112 wrapper; prove that wrapper through the original one-frame acceptance and required matrix/state gates. The old wrapper's acceptance and192-case receipts cannot qualify a new wrapper. Source preparation is underway in a separate host directory and is not READY or NPU PASS. All TP4 performance remains blocked until physical0 is genuinely usable and the original model gates pass. No formal performance or task-accuracy result exists.

DeltaLog: original CPU004 close receipt is absent; no close was applied. Native policy binds old cutoff1793447464 in approval/receipt verification. A minimal current-window successor must retain historical source/ledger/seal authority separately, preserve235051B/23files, close only1073506773B unused reservation and retain34GiB+1MiB limit. Existing user permission covers that exact logical close, not extra deletion or quota. No repeated CPU255 suite is needed.

Scheduling: V26/V27 have actual numeric durations10.2294s/10.3178s and separate startup/cleanup/owner spans. These are operator diagnostics, not throughput measurements or continuous AICore utilization. Complete continuous observations for the last30min are unavailable: full-window idle duration and effective utilization are unmeasured. Do not say four cards were continuously busy. Current source preparation gaps and physical0 UDA attribution are explicit; no fake load is permitted. Current authority is DEVICE_SCOPE_AUTHORIZATION_20261104_0_3.json with unchanged cutoff1793870269, preserving4–7/vllm-au-test.

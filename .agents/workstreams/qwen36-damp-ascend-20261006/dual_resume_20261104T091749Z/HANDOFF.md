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


## BOLE f65 registered wrapper one-frame closure, 2026-11-04

Physical NPU1: the f65 wrapper passed all18 original numerical checks, verify1/commit4/diagnostic-direct0, actual numeric9.85049876011908s. Original independent FP64 readback passed all18 checks and bitwise final-output identity, actual6.037297589937225s, without candidate execution or NPU access. Exact NPU and CPU owners/containers were independently verified absent or terminal exit0/Pid0/noOOM at the recorded final release. Fresh admission remains mandatory.

MAIN acceptance BOLE_F65_REGISTERED_WRAPPER_ONE_FRAME_MAIN_ACCEPTED_20261104.json:5735B/cbbbb505227b1f2f2673cf81cef2ca09ba33a29ff8798f5816ef3ee9382bec06. Execution EXECUTION_BOLE_F65_WRAPPER_ONE_FRAME_ACCEPTED_CENTRAL_IO_20261104.json:2113B/819e9fd6872a1f70a6015eb3a21ab8d7e27c314441a319ee5bd0a420c71b934c. All source/RAW remain host-only. Authority is physical0-3 with4-7/vllm-au-test protected; unchanged cutoff1793870269.

Only one captured wrapper frame is qualified. New-library original192 matrix, model short8/multistep/long-state, formal paired32K/fixed1024 performance and GSM8K/HumanEval/MMLU accuracy remain pending. Old-library matrix receipts do not transfer. Matrix owner v1/op083f failed before container creation on predecessor file/CID inconsistency; v2/op0841 failed before container creation on missing EXACT_LITERAL_REF_READSET.json. Preserve both failed OWNER_RESULT files. New preparation binds the actual tuple and all owner-required immutable inputs; inspect latest actual execution, never infer PASS from preparation.

DeltaLog CPU004 logical close remains unapplied: exact absent CID needs an explicit healthy-daemon/full-list/no-writer producer and consumer, not invented exited State. No extra deletion/quota is authorized. Physical0 UDA ownership remains unproven; do not terminate protected or unknown processes. Child remote calls hung without returned handles, so MAIN centralizes remote I/O and agents review sanitized metadata offline. Continuous30min utilization is unmeasured; do not claim zero idle.


## 2026-11-04 actual physical1 matrix192 and precise CPU004 close

Active Nov4 09:17:49Z–Nov5 09:17:49Z authority plus DEVICE_SCOPE_AUTHORIZATION_20261104_0_3.json; MAIN physical0–3, preserve4–7/vllm-au-test. Original start/cutoff unchanged.

BOLE f65/registered adapter7118/wrapperbc984 actually passed original192 saved cases/3456 original metric predicates on physical1: verify192/commit768/direct0, numeric128.7378312s, exact owner/container terminated and released. This covers saved four-source-TP-rank x48-layer inputs on one physical card, NOT TP4 model. The independent read-only scope audit reopened192 RAW fullSHA/identities/metric dictionaries, NOT a second full FP64 recomputation.
Immutable aggregate incorrectly labels physical4; REQUEST/executed guard/exactCID mapping prove1. Preserve original result and audit failures. Scope-discrepancy INDEX explicitly model_consumer_ready=false. Next: explicit current-f65 binding of original report/RAW/manifest + exact owner/mapping + discrepancy INDEX through the registered native fused_component_qualification.py contract. No old8e7 proof transfer, silent normalization or192 rerun merely for label. Original consumer location: historical short8_cann_matrix192_successor_prepare_v6r7b/native_prepare/source-short8.

Delta CPU004 unused1,073,506,773-byte logical reservation actually closed ONCE. Original ledger and235,051 bytes remain. Receipt runtime_storage/CPU004_UNUSED_ACCOUNTING_CLOSE_v1.json SHA84f882f1bd0203dfd71b1f8a4a3aec7df015222b366a77ea43568e41596c0ba6. Exact absent-container proof and independent new-policy consumer passed; absent is never fabricated as exited. No reapply/delete.
Delta176 source files were fully written, then native materializer exit1 at final report anti-overwrite assert because immutable preview already existed. Preserve original exit1/previewFalse/target/stderr. Recovery INDEX verifies exact176-path set/FullRefs/template/close lineage/two no-writer observations and no remaining materialization after failed assert. Source completeness only, NOT SOURCE_BOUND/CPU/NPU PASS. Original command builder currently lacks actual capture005 CURRENT_OVERLAY.json; next original new-source sourceaudit/capture005/nativebind/current MAIN admission, avoiding unchanged255-case CPU reruns. Never rerun materialization into existing target or invent overlay.

Fresh receipt records no computePID on0–3, preserved320140–320143 on4–7. UDA0/ns0 reservation owner still unknown; no reset/stop/service change. TP4 on0–3 awaits attribution; independent qualified1–3 work allowed. No continuous30min utilization evidence: unmeasured.
Evidence in this directory: ACTUAL_STAGE_MATRIX192_DELTA_CLOSE_AND_SCOPE_20261104.json; bole_f65_registered_matrix192_evidence_scope_review_v2/INDEX.json; delta_CPU005_materialization_recovery_v1/INDEX.json; EXECUTION_BOLE_F65_ACTUAL192_NUMERIC_VERIFIED_SCOPE_DISCREPANCY_20261104.json; EXECUTION_DELTA_CPU004_EXACT_ABSENT_LOGICAL_CLOSE_VERIFIED_20261104.json. Source/RAW/generated artifacts stay host-only. No model/performance/task-accuracy acceptance.

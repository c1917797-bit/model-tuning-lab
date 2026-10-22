# Production startup repair checkpoint — 2026-10-22

This is source/startup progress, not BOLE acceptance. Historical deadlines are unchanged; the current internal batch still ends at 23:10 UTC, phase3600/shared cleanup180, whole admission3780. Physical4–7 only; no0–3 action.

## Retained failure and narrow correction

V6 unit u2 terminated with MainPID0 and ExecMainStatus3. Actual traceback: host_service.py57 → performance_host.py71 → original host_run.run → subprocess.TimeoutExpired on a4-second Docker health call. No model requests or production collective observations completed. The owned model container stopped, was retained, and was not OOM-killed. CPU cleanup and model cleanup were preserved; physical4–7 returned to idle.

Retained V6 RESULT:
- /opt/host/vnf/austinov/run-bole-reduction-ON-v6-common_20261022T210000Z/RESULT.json
- 2376813 bytes, SHA256 2a97fc55c0fb4ae05253099eaaf8937ebd949a7de92a749adbe116238e5a641c.

V7 changes only the actual performance_host health call: outer deadline min(30,startup remaining,phase remaining), positive-budget assertion. Inner HTTP timeout2, startup900, all math/transaction/TP/rollback/resource gates and phase/cleanup are unchanged. TimeoutExpired remains fatal, so an unknown surviving guest probe is never blindly retried.

Actual health controls op08d1:9PASS, including the original real runner's TimeoutExpired/partial-bytes behavior. Independent whole runtime comparison op08d8: only performance_host.py differs; its complete inverse equals V6. Four original observer/raw helpers and common environment helper remain byte-identical.

## Exact source and dispatch

- Source /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v7-startup_20261022T215000Z/SOURCE_BOUND.json; 1645404 bytes, SHA256 7a0aa94fb3e2d4285c94280c5591b03d8ec9c32a063842ed8dce9190c07fda5a.
- Complete source audit /opt/host/vnf/austinov/run-bole-reduction-ON-v7-startup_20261022T215000Z-SOURCE-AUDIT-v2/SOURCE_AUDIT.json; 1427207 bytes, SHA256 488530d35f07828102a7033db287235bb3cfd3bed8e0451d46c148896d953a6f.
- Actual audit op08e0 passed; independent op08e9 rehashed6321Refs and matched the exact host readset/recorded command operand. A prior metadata-only checker op08e3 reconstructed a sorted Ref and was correctly rejected; no source or gate was changed.
- Actual16-history controls op08e7 passed. The added V6 lifecycle branch preserves the exact failed primary; it never promotes the failed model to numerical qualification.
- Config /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/reduction_admission_prepare_v7_startup_20261022T215000Z/CONFIG.ON.actual-v1.json; 22958 bytes, SHA256 65b1bcf1229a3ce4a045386e82c183a61d36af5abed4f8b7a4820c2c678154b0.
- Actual readonly snapshot v2: all16 registered owners stopped, no physical4–7 processes, original fit true. Op0900 independently checked the snapshot. V1 was retained after it aged during metadata inspection.
- Unit bole-reduction-on-v7-startup-20261022t215000z-u1.service, dispatched op0905 with snapshot age110.9s. MAIN source/live/ownership gates remain active.
- Last observed host PID2420119 was the actual V7 host_service.py, not merely a lock or intent record.
- CPU software child0, CPU parser child0, CPU stop/retain/errors[]; four-device canary child0. Model container CID2e941d42dcc8c05bd1d16e2a84305b7181caa64f4914dc44b61c201a0b5f7bbe.
- API startup selected actual Qwen3_5ForConditionalGeneration, v0.23, maxlen4096,TP4,C1,eager,text-only. Last observed phase: server startup; model request completion and actual production flags remain pending.

Use the shared MAIN lock; never relaunch this unit just because observation expires. Re-prove its terminal state and own-only release before a successor.

## Next evidence, not asserted results

After actual terminal host RESULT and cleanup, run the independent V7 production-repeatability consumer (11331B, SHA256 ac34c4fa9293279c09a29d24712f0302c332366741c8ec0bea3e6fbc7ff1b737). Its function bodies are exactly the reviewed V6 consumer; only source/output operands and module documentation changed, default OFF verified op0916. It must join real HTTP/state/lifecycle, all8 worker flags, complete pre/post bytes and outer projection return. Even a PASS is boundary-repeatability only, never BOLE numerical/performance/task acceptance.

Native AR revision3 is a complete unbound source-only candidate with a repaired strict worker reader,13 positive/negative controls and6733Ref template check; not frozen or NPU-qualified. FAST short8 numerical bridge is still being reviewed/bound. Its selected-conv-tail and CPU-digest defects must be fixed before numerical use; long160/1024, page growth and outside-request arena coverage remain pending.

No formal1024 throughput, TTFT/TPOT, task smoke/full accuracy or final usable technology is established here.

## Actual terminal production result

Op092f: unit naturally terminal, MainPID0 / ExecMainStatus0 / active-exited.
Host RESULT /opt/host/vnf/austinov/run-bole-reduction-ON-v7-startup_20261022T215000Z/RESULT.json,2407482B, SHA256 083a3c3747567b1fe9ce14ef43adda2aa4a8d579808949a2141a8be01172390a.
Primary null, secondary[], whole source-before/source-after identical; elapsed717.747907s, original32 rank state frames and HTTP/lifecycle checked. Op0931 independently inspected both own containers stopped/retained/OOMfalse and physical4–7 idle.

Op0932 independent consumer exit0, stderr empty:
/opt/host/vnf/austinov/run-bole-production-repeatability-v7-20261022T221200Z/REPEATABILITY.json
56082B, SHA256 b8f788afb9b07170a554fef23909e5c48778af0b8b6119b6d8d2cc522da1e51d.
Execution2002B SHA256 557684aa3c9f71d972f9bc2a410498d3382fd9ee9cc44f419e95181ba44e8704.

Independent op093b rehashed all16 raw files/21463040B, checked all8 actual worker HCCL_DETERMINISTIC=true observations, complete per-rank pre/post equality across G1/G2, cross-rank post equality, original32-frame stagejoin and actual projection/HTTP/lifecycle outer graph join. Consumer actual input set107Refs. Interpretation: the captured first native prefill projection is repeatable under the common setting. G1 warmup/G2 measured is not two warmed repetitions; no whole BOLE numerical, long decode, formal throughput or task acceptance is supplied. All those flags remain false.

No new full phase fits the unchanged batch after22:07UTC (whole3780 required before23:10 cutoff). Do not extend the ticket or start a successor merely to avoid idle time. Continue device-free source/validator and task-input preparation; require a legitimate remaining/new execution window for further admission.

## Git delivery

Commit36f05951fb7664ceb9eebdb59c861daf1b6d1d62 exists locally. Remote was a900f1dfcfb1faaec75f64b4b19fad091c64c63e at op08dd. Normal push op08e4 failed with HTTPS low-speed timeout; do not claim36f pushed. Keep unrelated dirty skills/HANDOFF untouched. No force push, no main edit.

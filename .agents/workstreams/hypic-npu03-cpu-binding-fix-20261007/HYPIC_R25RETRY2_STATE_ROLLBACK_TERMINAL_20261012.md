# R25 retry2: bounded HYPIC observer lifecycle regression passed

This closes the retained-callable uninstall defect in the diagnostic observer
for this one integrated request. It is not full HYPIC quality/performance or
main-Skill acceptance. r24 remains FAILED_POST_UNINSTALL; r25 and retry1 remain
pre-health isolation failures.

## Frozen identity and terminal evidence

- Code checkpoint: 9b3f6b3c; controller exec-0000000000000014, exit 0,
  duration 624.884 seconds, released at 2026-10-12T20:16:39.294264Z.
- Contract SHA256: 3921e2b27d8bad406eaa1653b3a30cbdca3feb413d6dee4d89c4210568cb126a.
- HYPIC source: 4429e35177979c874bf053ab29789e4773f39b22.
- Image: sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1.
- Qwen3.6-27B BF16 TP4, physical NPU0-3 only, port8223; sample059,
  prompt20414, explicit boundary16384; two1-token warmups, max2048 target,
  one1-token post-uninstall request.
- Immutable raw root:
  /cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r25retry2-state-enabled.
- Independent auditor: r25retry2_state_audit.py, exec-0000000000000021 exit0.
- External audit:
  /cache/cch/hypic-npu03-cpu-binding-fix-20261007/r25retry2-state-enabled-independent-audit.json.
- Audit SHA256: 01d49278c92c931ccaff5a6d204e750d20010953e32daa64a5c7e980c3bd83c5.
- Exact owned container: c7b9dcf282e6e10adcd4a4fd4a76ee9adc453ae0f559b4ac2590bcd9b6ca95b4.
- Host worker PIDs1704652-1704655; namespace267-270 independently joined to
  framework ranks0-3 and declared physical devices.
- 117 continuous guard samples, no foreign PID or probe error. Exact container,
  own NPU processes and8223 released. No external task was stopped or changed.

## Observed bounded result

All four responses completed. The target produced1275 tokens and stopped
naturally. The post-uninstall request produced its requested1 token without
the old NameError/HTTP500. All four workers sealed five events each, and their
target request/step8 receipts independently joined.

For the selected two layers/head0/KV rows, destination-cast comparisons have
zero different coordinates and zero maximum absolute residual for KV, GDN
state, conv tail and position mapping. GDN FP64 residual maxima by rank are
1.4594260377975843e-7, 9.328871364289171e-7,
5.622073295796781e-8 and0. These are reported residuals, not a newly invented
numerical-equivalence threshold.

The nested numerical comparator deliberately does not prove physical execution;
the outer audit separately verifies device/PID/source/isolation receipts.
Material producer-generation and independently regenerated material inputs
remain unproven. This is not all-layer/full-tensor equivalence or a diagnosis
of r19's quality difference. r19 remains227/381 versus219/381 under its
frozen REJECT_OR_QUALIFY decision.

## Lesson and next gate

Retaining generation-specific inert dispatchers fixes old callable aliases
that outlive module-attribute restoration. Active hooks and session callbacks
are removed; inert global names remain until process exit and are disclosed.
The real post-uninstall request now passes for this bounded integrated case.
This observer lifecycle route is closed; do not repeat the same serial test.

Continue the HYPIC quality investigation with a prospective, discriminating
concurrency/material-generation hypothesis grounded in r19/r20 and this capture.
Do not start another broad quality wave without a changed premise, or declare
sampled serial success to repair c32 quality. Existing completed baselines are
not rerun merely for a new attempt number. Only matching final-source quality,
performance and delivery evidence can support promotion.

Runtime-monkeypatch-delivery gains this successful bounded supplement while
remaining partial-evidence for the actual HYPIC delivery package. The29-Skill
inventory remains7 bounded verified and22 partial; no main/remote sync claimed.

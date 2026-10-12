# r25 pre-health isolation failure — 2026-10-12

Decision: ISOLATION_FAILED_BEFORE_HEALTH. Controller exec-0000000000000d4c
ended exit1 after193.011 seconds. There were zero warmup/target/post responses
and zero captures, so the observer-v2 fix is NOT device-tested by this attempt.

At12:09:49.434456 UTC, the continuous physical0-3 guard captured NPU1
PID586905 in container efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6
(cannbench_ds by the earlier Docker inventory). This identifies a container,
not its human launcher. 24 guard samples, one foreign event, zero probe errors.
At12:10:53.011013 UTC only the identity-proven owned container
c9c9452170aa9aded4824f49c987e04ef481a313e420ece144917e71d652a8e5
was released, with owned physical processes and8223 free. Foreign tasks and
NPU4-7 were not stopped or changed.

Raw root:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r25-state-enabled`.
Independent failure auditor `r25_isolation_failure_audit.py` passed exec0d59.
Audit:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/r25-state-enabled-isolation-failure-audit.json`
SHA256 `b4472f4fd93a924c53bb89094fd1675b43a62a2b41a6d724edb323c82da61d2a`.

The auditor verifies the frozen contract and declared image/device mapping,
failure/event identity, absence of responses/captures, service-log hash and
exact release. It does not invent a live-worker source/activation proof before
health. This is environmental invalidation, neither algorithm failure nor
successful observer rollback.

## Recovery

Preserve this root and frozen r25 files. User permits waiting for actual idle
physical0-3 despite passive container mappings. A new-root retry may retain the
same diagnostic bytes except attempt/root/request identifiers; no parameter
tuning, threshold relaxation, new quality baseline or repeated full corpus.
Recheck the live direct ma route, numbered physical processes and8223
immediately before admission; maintain the continuous guard.
A prior idle observation is never a reserved lease or protection from new jobs.

This adds bounded host-maintenance/isolation and runtime-delivery negative
evidence only. r24 partial numerical results, r19/r22 quality judgments and
29-Skill acceptance remain unchanged. No main or remote synchronization.

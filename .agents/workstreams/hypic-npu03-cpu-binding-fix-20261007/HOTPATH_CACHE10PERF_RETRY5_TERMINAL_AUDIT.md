# HYPIC phase-6 retry5 terminal audit

Date: 2026-10-09 UTC
Campaign: frozen `cache10perf`, `hypic-only/repeat3`
Classification: environmental pre-measurement isolation failure; not a HYPIC performance verdict.

## Immutable attempt and launch

- Raw root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry5`.
- Controller operation: `exec-0000000000000197`, launched through a freshly resolved direct route to `chicaihong01/ma` after an immediate physical preflight showed NPU0–3 and port 8223 free and the retry5 root absent.
- The operation returned an executor timeout. Same-target inspection found physical guard evidence in the immutable root; the root is preserved and must not be reused.
- Contract SHA256: `8a1020814dad5ea91520fb44c161137a2b7212d36e65a1c294f100c096a96057`.

## Isolation and request evidence

- The continuous physical-lane guard recorded 2 samples and 0 probe errors.
- At `2026-10-09T10:36:02.322155Z`, it captured foreign PID `3539167` on physical NPU0, in container `87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa` (`/Maxon4ick_vllm`). The process had exited by follow-up inspection; the foreign container was not changed.
- Guard SHA256: `24d9e1f91596214903a95d9fe8b7ff91562a8fc5411eedd63a3e7845c9e8ce87`.
- `hypic-evidence.jsonl` is 0 bytes (SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). No scored request rows, `performance.json`, or `arm-result.json` exist. Therefore there is no performance metric to report.

## Exact owned-resource cleanup

- The attempt-owned container was exactly `eec7c5ef562cd446364c6b021c1e0c70f1988362c8d5c108db3c4dab5091ca5f`, named for the retry5 attempt and labeled `hypic.experiment=hypic-npu03-bindingoff-quality41984-20261007-hotpath-cache10perf-hypic-only-repeat3-retry5`.
- Docker inspection showed it exited with code 137 (not OOM). It was removed by that exact container ID only; its bind-mounted evidence under `/cache/cch/hypic-npu03-cpu-binding-fix-20261007` was preserved. No foreign container was stopped, modified, or removed.
- Post-cleanup `npu-smi` showed no processes on physical NPU0–3; port 8223 was free.

## Decision

Retry5 is consumed as an environmental isolation failure before measurement. It is neither a positive nor a negative HYPIC performance result. Preserve all prior phase roots and the already-frozen r13 quality conclusion (`REJECT_OR_QUALIFY`, 230/381 to 219/381; strict four-worker hot coverage 368/381 FAIL). No retry6 is authorized; a new attempt requires a separate explicit user authorization and a distinct preregistered root.

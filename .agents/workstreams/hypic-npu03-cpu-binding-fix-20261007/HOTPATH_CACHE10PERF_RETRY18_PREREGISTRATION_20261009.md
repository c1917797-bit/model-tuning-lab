# HYPIC repeat3 retry18 preregistration — 2026-10-09

## Frozen objective

Retry only the missing sixth matched performance phase, `hypic-only/repeat3`,
under the existing cache10r13 contract. Do not change the workload, candidate,
source, image, quality gate, or performance acceptance criteria. The immutable
r13 quality decision remains `REJECT_OR_QUALIFY`: 230/381 no-cache versus
219/381 HYPIC (−2.8871 pp); strict four-worker hot coverage remains 368/381.
No performance result can reverse that quality decision.

## Identities and command

- Target: `chicaihong01/ma`; physical NPU0–3 only. NPU4–7 are forbidden.
- Branch: `work/hypic-npu03-cpu-binding-fix-20261007`.
- Source/plugin: `c12060cd47e7575ead059983d7a8bb4704165c98`.
- Frozen workload: 40 measured requests, concurrency 16, 32768 input tokens,
  16384 prefix tokens, fixed 1024-token output, 2 warmups, EOS ignored, and
  explicit HYPIC segment-end evidence; same no-cache denominator as all five
  independently audited phases.
- Controller SHA256:
  `c11a6223dea01ab85c6b91e1cc59ab39092aab0572baa0d724832df9eee9b139`.
- Request-ID benchmark SHA256:
  `0d88b054a91e4985f131187d84899d76d57a1da1d97f842c2f51052534abc6ac`.
- Unique root (must be absent immediately before launch):
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry18`.
- Command, from the workstream directory:
  `python3 -B hotpath_cache10_matched_performance.py --arm hypic-only --phase repeat3 --environmental-retry18 --run`.

Retry18 is admitted only by the controller's exact immutable retry17 failure
gate, including retry17 receipt SHA256s. It is a new attempt, not a continuation
or overwrite of retry17.

The first controller-only invocation failed before root creation due to a
local initialization-order bug; see
`HOTPATH_CACHE10PERF_RETRY18_CONTROLLER_STARTUP_FAILURE_20261009.md`. The
corrected controller is the frozen identity above. Because no root, service,
or measurement artifact was created, retry18 itself remains unlaunched.

## Resource admission

The user authorized opportunistic monitoring and execution only when physical
NPU0, NPU1, NPU2, and NPU3 have no running processes and TCP 8223 has no
listener. Take a fresh direct-routed snapshot immediately before launch and
prove the retry18 root is absent. Keep the controller's continuous physical
PID/cgroup guard for the complete phase. A container mapping alone does not
block allocation; a physical process does. Never stop, signal, reconfigure, or
otherwise modify foreign work.

Retry17's immutable guard captured an external container on physical NPU0
before health/scoring (PID 1198578; container ID
`87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa`). Its
terminal audit is `HOTPATH_CACHE10PERF_RETRY17_TERMINAL_AUDIT_20261009.md`.
That attempt yielded zero scored rows and no performance metrics. Its later
cleanup snapshot is not an allocation lease for retry18.

## Failure and acceptance boundaries

If a foreign physical process appears, or a probe fails before health/scoring,
preserve retry18's unique root and detection-time evidence; classify it as an
environmental no-result; clean up only the exact retry18-owned service; and
wait for another idle observation. Do not make a HYPIC success/regression
claim. Any later attempt requires another unique preregistered root. Never
restart a live or ambiguous controller.

Retry18 becomes a valid measurement only after 40/40 successful fixed-output
rows plus 2 warmups, all 40 measured request IDs with four-worker HYPIC
hot-path proof, continuous clean isolation, exact owned cleanup, and a passing
independent phase audit. Then—and only then—run the frozen independent audit
across all six phases. Until that gate passes, the sixth phase remains
unmeasured.

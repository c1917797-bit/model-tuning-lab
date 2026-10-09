# HYPIC repeat3 retry17 preregistration — 2026-10-09

## Purpose and frozen boundary

This is a new-root environmental retry of only the sixth frozen matched
performance phase: `hypic-only/repeat3`. It does not change the HYPIC
algorithm, workload, controls, thresholds, or the already-rejected r13 quality
decision. The paired quality result remains no-cache 230/381 versus HYPIC
219/381 (−2.8871 percentage points, `REJECT_OR_QUALIFY`); strict four-worker
hot coverage remains 368/381 and fails. Performance cannot reverse either
quality finding.

Retries 15 and 16 both stopped before service health or scoring because the
same external `cannbench_ds` container intermittently entered physical NPU2.
They each had zero scored requests, no performance metrics, a clean probe, and
exact cleanup of only the service container owned by that attempt. Their
immutable roots and audits remain environmental evidence, not HYPIC
measurements. Retry17 must use a distinct root and must not reuse any previous
attempt artifacts.

## Frozen identities

- Target: `chicaihong01/ma`, physical NPU0–3 only; NPU4–7 are out of scope.
- Branch: `work/hypic-npu03-cpu-binding-fix-20261007`.
- Workload: unchanged cache10r13 matched performance contract, 40 scored
  requests, concurrency 16, 32768 input tokens, 16384 prefix tokens, fixed
  1024-token output, two warmups, EOS ignored, and explicit HYPIC segment-end
  evidence. The sixth phase is `hypic-only/repeat3`.
- Source/plugin identity: `c12060cd47e7575ead059983d7a8bb4704165c98`.
- Phase controller SHA256:
  `ac94107218a1bc90ca3336ffdb6ddc0f325a8eb0c05d381029bc8a09d8d47e95`.
- Request-ID benchmark SHA256:
  `0d88b054a91e4985f131187d84899d76d57a1da1d97f842c2f51052534abc6ac`.
- Attempt root (must be absent before launch):
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry17`.
- Exact controller invocation from the workstream directory:
  `python3 -B hotpath_cache10_matched_performance.py --arm hypic-only --phase repeat3 --environmental-retry17 --run`.

## Admission and interruption rules

User-authorized policy is opportunistic: monitor, and launch only while a
fresh direct-target snapshot proves that physical NPU0, NPU1, NPU2, and NPU3
have no running processes and TCP port 8223 has no listener. A container's
declared device map alone is not occupancy; a real physical process is.
Immediately before launch, also prove the retry17 root is absent, the exact
five earlier performance phases are valid and released, the r13 quality audit
is unchanged, and the controller accepts the immutable retry16 environmental
failure evidence. Retain the controller's continuous physical PID/cgroup
guard throughout startup and measurement.

At the 2026-10-09 13:22 UTC preregistration check, physical NPU1 was actively
used by PID 1091574 (`python -m kernel_eval.staged_eval`, cgroup/container
`efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6`,
`cannbench_ds`). NPU0, NPU2, and NPU3 showed no running process and port 8223
was free. Therefore this document is not an allocation: do not launch until a
new snapshot proves all four physical cards and the port are idle. Do not stop,
signal, reconfigure, or otherwise modify that external workload.

If external physical work appears or a probe fails before the controller's
health/scoring boundary, preserve the unique root and exact detection-time
PID/cgroup/container evidence, count zero benchmark rows, remove only the
exact attempt-owned service/container, and classify the attempt as
environmental—not as a HYPIC success, regression, or performance result. A
later try requires another unique preregistered root. Never restart a live or
ambiguous controller; inspect the same operation and its root first.

## Completion test

Retry17 is a valid phase only if its immutable receipts prove the frozen
contract/source, all 40 unique successful fixed-output rows plus 2 warmups,
full per-request-ID four-worker HYPIC hot-path activation, continuous clean
physical NPU0–3 isolation, no probe errors or foreign processes, exact owned
resource cleanup, and a passing independent `audit_phase` audit. Only after
that may the independent six-phase audit compute the matched performance
comparison. Until then the sixth phase is unmeasured and the campaign is not
fully reproduced.

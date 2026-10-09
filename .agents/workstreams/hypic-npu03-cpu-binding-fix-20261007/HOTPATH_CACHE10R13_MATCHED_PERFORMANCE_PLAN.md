# r13 matched performance follow-on (frozen before device execution)

The existing cache10r2 performance plan never passed its entry gate. This
follow-on uses the r13 dual-quality audit, without treating the older 0.9/4
segment service or the invalid r2 arm as a control. No r13 performance phase
has run yet.

## Entry and identity

- Require the independent `hotpath-quality-cache10r13-dual-audit.json`
  receipt with two complete, raw-hash-checked 127×3 arms, clean physical
  NPU0–3 isolation, exact release, same service fingerprint, and source
  attestation. A quality regression or a cold request remains a negative
  outcome, not a reason to silently change the pair or its denominator.
- The service identity is source
  `c12060cd47e7575ead059983d7a8bb4704165c98`, official image
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`,
  Qwen3.6-27B TP4, physical NPU0–3, cpuset 112–191, context 41,984,
  GPU utilization 0.85, CPU binding disabled, 3,584 MiB/10 materialized
  segments. Only HYPIC enablement and evidence path may differ by arm.
- Start each fresh owned service only after actual physical 0–3 process and
  port checks. Keep a 10-second foreign-process guard from before container
  startup through the measured workload. A foreign PID or probe error
  invalidates the phase; never stop a foreign process or touch NPU4–7.

## Workload and decision

Run six immutable roots in this order: baseline/candidate screen,
candidate/baseline repeat2, baseline/candidate repeat3. Use the frozen
shared-prefix benchmark: 2 concurrent one-token warm requests, then
40 requests at c16 with 32,768 input, a 16,384 shared prefix, explicit
`[16384,32768]` segment ends, fixed 1,024 output, temperature 0, seed 0,
ignore-EOS. Each phase must have 40 unique successful 1,024-token rows,
four correct physical workers, raw/summary arithmetic agreement, a clean
guard, source attestation, and exact owned release. The independent audit
reports every phase, three paired differences, medians, weighted TPOT,
P95 TTFT/TPOT, throughput and duration. Its predeclared effect screen is
at least 10 ms/token weighted-TPOT savings and 10 s TTFT-P95 savings.

The pinned original shared-prefix benchmark does not retain per-row OpenAI
request IDs. The frozen observational adapter
`hotpath_request_id_benchmark.py` retains the first SSE ID for each warm
and measured request without changing prompts, request parameters, barrier
or original metrics. Require all 42 unique IDs per phase. The independent
auditor joins each of the 40 measured candidate IDs to exactly one
scheduler boundary and four worker-namespace post-repair receipts. It reports
all-request deployed performance whether or not every candidate request is
hot; strict C1/C2 effect is accepted only with 120/120 hot measured requests
across the three candidate phases. A cold request remains a negative
strict-coverage result, not a reason to discard the deployed metric.
Favorable performance alone is not paper-complete C3 or production adoption.

The six predeclared `hotpath-cache10perf-*` attempt names were never
executed; their roots were checked absent before retargeting their entry
gate to r13. Contract fingerprints and the r13 audit hash, not the older
generic root name, define this campaign's evidence identity. No historical
performance result is overwritten or reused.

Controller: `hotpath_cache10_matched_performance.py --arm ... --phase ... --run`.
Auditor: `audit_hotpath_cache10_matched_performance.py`. Both refuse to
reuse prior result roots. A narrowly scoped recovery amendment applies only
if hypic-only/repeat3 fails before service health and before benchmark start
because the physical-lane guard observes an actual foreign PID/probe error:
preserve the failed original root and its exact receipts, wait for the lane
to become idle, and permit up to three same-protocol immutable recovery roots
(`--environmental-retry1`, `--environmental-retry2`, then
`--environmental-retry3`) if each previous
run terminated before service health with foreign-lane evidence and exact
owned-container removal. They may not be used for workload, quality, hot-path, or
performance failures, and it does not alter any denominator or acceptance
rule. The user subsequently authorized one additional bounded recovery on
2026-10-09 after retry3 also failed pre-health with no measured rows. This
amendment permits exactly one fourth immutable recovery root (`retry4`) only
when retry3 has audited pre-health foreign-lane evidence and exact owned
resource release. It does not alter source, workload, denominators, measured
repetitions, metrics, or acceptance rules. The independent six-phase audit
uses the latest valid retry root only if one exists;
the original pre-measurement invalid attempt remains reported as excluded.
If the controller's immediate `assert_lane_available` detects a process before
creating the retry root, that invocation has no root, container, or scored row;
it is only a failed availability probe and does not consume the one new-root
measurement attempt. Recheck the lane and reissue only while it is truly idle.

Retry4 was run under that amendment and is terminally invalid: after service
health, its 120-sample guard recorded foreign PID 3079008 on physical NPU1;
only 16/40 responses completed before the owned service was released. The
partial rows are not performance evidence, and phase 6 remains incomplete.
See `HOTPATH_CACHE10PERF_RETRY4_TERMINAL_AUDIT.md`. Retry4 consumed the sole
amended recovery root; no retry5 without a new explicit user authorization
and preregistered amendment.

The 120/120 per-request worker proof is the strict C1/C2 mechanism-attribution
gate, not the all-request deployed performance result. Both are reported;
failure of strict coverage must not erase or relabel the deployed result.

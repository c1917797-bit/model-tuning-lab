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

The original shared-prefix benchmark does not retain per-row OpenAI request
IDs. Consequently these six phases can establish an *all-request deployed
performance effect* with coarse HYPIC activation, not 40/40 request-level
four-worker hot-path coverage. Report strict C1/C2 performance as
`UNVERIFIED_REQUEST_JOIN` until a separately frozen benchmark records
joinable IDs and validates every measured request. Favorable deployed
performance alone is not paper-complete C3 or production adoption.

The six predeclared `hotpath-cache10perf-*` attempt names were never
executed; their roots were checked absent before retargeting their entry
gate to r13. Contract fingerprints and the r13 audit hash, not the older
generic root name, define this campaign's evidence identity. No historical
performance result is overwritten or reused.

Controller: `hotpath_cache10_matched_performance.py --arm ... --phase ... --run`.
Auditor: `audit_hotpath_cache10_matched_performance.py`. Both refuse to
reuse prior result roots; inspect operation handles before any retry.
